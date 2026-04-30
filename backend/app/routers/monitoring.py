"""
Monitoring endpoints for system health and assessment tracking.
Provides visibility into stuck assessments, completion rates, and system status.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
import asyncio

from app.services.supabase_client import SupabaseService, get_supabase_service
from app.core.logging import api_logger, error_logger

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/health/stuck-assessments")
async def get_stuck_assessments(db: SupabaseService = Depends(get_supabase_service)):
    """
    Get assessments stuck in 'in_progress' for more than 10 minutes.
    These will be auto-marked as abandoned by stale_checker.
    
    Returns:
        - stuck_count: Number of stuck assessments
        - assessments: List of stuck assessment details with timestamps
    """
    try:
        client = db.get_client(use_admin=True)
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        
        stuck = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("id, user_id, created_at, last_heartbeat_at, last_completed_stage, stages_completed")
            .eq("status", "in_progress")
            .lt("last_heartbeat_at", cutoff)
            .order("last_heartbeat_at", desc=True)
            .execute()
        )
        
        assessments = stuck.data or []
        api_logger.info(f"⚠️ Found {len(assessments)} stuck assessments")
        
        return {
            "stuck_count": len(assessments),
            "cutoff_time": cutoff,
            "assessments": assessments
        }
    except Exception as e:
        error_logger.error(f"Failed to fetch stuck assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/completion-metrics")
async def get_completion_metrics(db: SupabaseService = Depends(get_supabase_service)):
    """
    Get assessment completion statistics.
    
    Returns:
        - total_assessments: Total number of assessments
        - completed: Count of completed assessments
        - abandoned: Count of abandoned assessments
        - in_progress: Count of in-progress assessments
        - completion_rate: Percentage of completed vs total
    """
    try:
        client = db.get_client(use_admin=True)
        
        # Get counts by status
        stats = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("status", count="exact")
            .eq("status", "completed")
            .execute()
        )
        completed_count = stats.count if hasattr(stats, 'count') else 0
        
        abandoned = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("status", count="exact")
            .eq("status", "abandoned")
            .execute()
        )
        abandoned_count = abandoned.count if hasattr(abandoned, 'count') else 0
        
        in_progress = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("status", count="exact")
            .eq("status", "in_progress")
            .execute()
        )
        in_progress_count = in_progress.count if hasattr(in_progress, 'count') else 0
        
        total = completed_count + abandoned_count + in_progress_count
        
        # Calculate completion rate
        completion_rate = (completed_count / total * 100) if total > 0 else 0
        
        api_logger.info(
            f"📊 Completion metrics: "
            f"completed={completed_count}, abandoned={abandoned_count}, "
            f"in_progress={in_progress_count}, total={total}, rate={completion_rate:.1f}%"
        )
        
        return {
            "total_assessments": total,
            "completed": completed_count,
            "abandoned": abandoned_count,
            "in_progress": in_progress_count,
            "completion_rate_percent": round(completion_rate, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        error_logger.error(f"Failed to fetch completion metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/abandonment-analysis")
async def get_abandonment_analysis(db: SupabaseService = Depends(get_supabase_service)):
    """
    Analyze abandoned assessments by reason.
    Helps identify whether abandonment is user-intentional or backend-caused.
    
    Returns:
        - by_reason: Count of abandonments grouped by abandon_reason
        - backend_failures: Assessments abandoned but had stages_completed > 0
        - never_started: Assessments abandoned with 0 stages completed
    """
    try:
        client = db.get_client(use_admin=True)
        
        # Get all abandoned assessments
        abandoned = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("id, abandon_reason, stages_completed, created_at")
            .eq("status", "abandoned")
            .order("created_at", desc=True)
            .execute()
        )
        
        assessments = abandoned.data or []
        
        # Categorize
        by_reason = {}
        backend_failures = []
        never_started = []
        
        for a in assessments:
            reason = a.get("abandon_reason", "unknown")
            stages = a.get("stages_completed", 0)
            
            # Count by reason
            by_reason[reason] = by_reason.get(reason, 0) + 1
            
            # Categorize
            if stages == 0:
                never_started.append(a["id"])
            elif reason == "no_heartbeat":
                # User did work but marked stale by backend
                backend_failures.append({
                    "assessment_id": a["id"],
                    "stages_completed": stages,
                    "reason": reason
                })
        
        api_logger.info(
            f"🔍 Abandonment analysis: "
            f"total={len(assessments)}, backend_failures={len(backend_failures)}, "
            f"never_started={len(never_started)}"
        )
        
        return {
            "total_abandoned": len(assessments),
            "by_reason": by_reason,
            "backend_failures_count": len(backend_failures),
            "backend_failures_detail": backend_failures[:20],  # Return first 20
            "never_started_count": len(never_started),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        error_logger.error(f"Failed to analyze abandonments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/system-status")
async def get_system_status(db: SupabaseService = Depends(get_supabase_service)):
    """
    Overall system health check combining multiple metrics.
    
    Returns:
        - status: 'healthy', 'degraded', or 'critical'
        - completion_rate: Current completion percentage
        - stuck_assessments: Count of stuck in_progress assessments
        - avg_completion_time: Average time to complete assessment (minutes)
    """
    try:
        client = db.get_client(use_admin=True)
        now = datetime.now(timezone.utc)
        
        # Get completion metrics
        completed = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("id, created_at, completed_at", count="exact")
            .eq("status", "completed")
            .execute()
        )
        completed_assessments = completed.data or []
        completed_count = completed.count if hasattr(completed, 'count') else 0
        
        # Get stuck assessments
        cutoff = (now - timedelta(minutes=10)).isoformat()
        stuck = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("id", count="exact")
            .eq("status", "in_progress")
            .lt("last_heartbeat_at", cutoff)
            .execute()
        )
        stuck_count = stuck.count if hasattr(stuck, 'count') else 0
        
        # Calculate average completion time
        completion_times = []
        for a in completed_assessments:
            if a.get("created_at") and a.get("completed_at"):
                try:
                    start = datetime.fromisoformat(a["created_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(a["completed_at"].replace("Z", "+00:00"))
                    duration_minutes = (end - start).total_seconds() / 60
                    completion_times.append(duration_minutes)
                except:
                    pass
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Get total for rate
        total = await asyncio.to_thread(
            lambda: client.table("assessments")
            .select("id", count="exact")
            .execute()
        )
        total_count = total.count if hasattr(total, 'count') else 1
        
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        # Determine status
        if completion_rate < 50 and stuck_count > 10:
            status = "critical"
        elif completion_rate < 70 or stuck_count > 5:
            status = "degraded"
        else:
            status = "healthy"
        
        api_logger.info(
            f"🏥 System status: {status} | "
            f"completion_rate={completion_rate:.1f}%, "
            f"stuck={stuck_count}, "
            f"avg_time={avg_completion_time:.1f}min"
        )
        
        return {
            "status": status,
            "completion_rate_percent": round(completion_rate, 2),
            "stuck_assessments": stuck_count,
            "completed_assessments": completed_count,
            "total_assessments": total_count,
            "avg_completion_time_minutes": round(avg_completion_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        error_logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
