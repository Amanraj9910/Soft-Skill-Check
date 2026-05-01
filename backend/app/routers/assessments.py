"""
Assessment API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
import asyncio
from typing import List
from app.models.schemas import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentAbandonRequest,
    HeartbeatRequest,
    SuccessResponse,
    ErrorResponse
)
from app.services.supabase_client import SupabaseService, get_supabase_service
from app.services.ai_assessment.report_generator import report_generator
from app.config import settings
from datetime import datetime

# Import logging and messages
from app.core.logging import api_logger, error_logger
from app.core import log_messages
from app.core.auth import get_current_user_id
from app.core.assessment_logger import assessment_event_logger

# Shared limiter — single instance across all routers (see app/core/rate_limiter.py)
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])


@router.post("/", response_model=AssessmentResponse)
@limiter.limit("5/minute")
async def create_assessment(
    request: Request,
    assessment_data: AssessmentCreate,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Create a new assessment.
    
    Args:
        assessment_data: Assessment creation data
        user_id: Current user ID (from auth)
        db: Database service
    
    Returns:
        Created assessment
    """
    try:
        api_logger.info(f"🚀 POST /api/v1/assessments/ - Creating assessment for user: {user_id[:8]}...")
        
        # Ensure profile exists (Self-healing)
        profile = await db.get_profile(user_id)
        if not profile:
            api_logger.info(log_messages.profile_not_found(user_id))
            await db.create_profile(user_id, {"full_name": "User"})
            api_logger.info(log_messages.profile_created(user_id))
            profile = await db.get_profile(user_id)

        # --- Role-based attempt limit check ---
        user_role = profile.get("role", "candidate") if profile else "candidate"
        if user_role == "candidate":
            client = db.get_client(use_admin=True)
            # Count ALL assessments for this user regardless of status.
            # Abandoned assessments still consume an attempt slot — candidates
            # are allowed exactly 1 total attempt (completed + in_progress + abandoned).
            # Completed assessments count toward the limit, but technical issues may allow 1 extra attempt.
            total_count = await asyncio.to_thread(
                lambda: client.table("assessments")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            total_attempts = total_count.count if hasattr(total_count, 'count') else 0

            if total_attempts >= 1:
                # Check if this is a completed assessment, which should not be retakable
                existing_assessments = await asyncio.to_thread(
                    lambda: client.table("assessments")
                    .select("*")
                    .eq("user_id", user_id)
                    .execute()
                )
                
                completed_assessment_exists = any(
                    assessment.get("status") == "completed" 
                    for assessment in existing_assessments.data
                )
                
                # If there's a completed assessment, do not allow any more attempts
                if completed_assessment_exists:
                    api_logger.warning(f"⛔ Candidate {user_id[:8]} blocked: Attempt to retake after completion")
                    raise HTTPException(
                        status_code=403,
                        detail="Assessment already completed. No additional attempts allowed."
                    )
                
                # Check if user has abandoned assessments that might qualify for an extra attempt
                abandoned_assessments = [
                    assessment for assessment in existing_assessments.data
                    if assessment.get("status") == "abandoned"
                ]
                
                # If user has already used their extra attempt after abandonment, block them
                if len(abandoned_assessments) >= 1 and total_attempts >= 2:
                    api_logger.warning(f"⛔ Candidate {user_id[:8]} blocked: Extra attempt already used")
                    raise HTTPException(
                        status_code=403,
                        detail="Assessment limit reached. No additional attempts allowed."
                    )
                
                # Allow one extra attempt if the previous attempt was abandoned due to technical issues
                if len(abandoned_assessments) >= 1:
                    api_logger.info(f"📝 Candidate {user_id[:8]} granted extra attempt after technical issue")
                else:
                    api_logger.warning(f"⛔ Candidate {user_id[:8]} blocked: 1 attempt already used")
                    raise HTTPException(
                        status_code=403,
                        detail="Assessment already taken. No additional attempts allowed unless due to technical issues."
                    )
            else:
                api_logger.info(f"📝 Candidate {user_id[:8]} starting first attempt")

        # CRITICAL: Validate profile exists and has name before creating assessment
        profile = await db.get_profile(user_id)
        if not profile or not profile.get("full_name") or profile.get("full_name").strip() == "":
            error_logger.error("Attempt to create assessment with incomplete profile", extra={
                "event_type": "PROFILE_VALIDATION_ERROR",
                "user_id": user_id,
                "profile_exists": bool(profile),
                "profile_name": profile.get("full_name") if profile else None
            })
            raise HTTPException(
                status_code=400, 
                detail="User profile must be complete before starting assessment"
            )

        # Create new assessment
        assessment = await db.create_assessment(user_id, {})
        
        if not assessment:
            error_logger.error("❌ Failed to create assessment: database returned null")
            raise HTTPException(status_code=500, detail="Failed to create assessment")
        
        # Log with student name for traceability
        student = await db.get_student_identity(user_id)
        assessment_event_logger.started(
            assessment_id=assessment["id"],
            student_name=student["name"],
            email=student["email"],
        )
        return AssessmentResponse(**assessment)
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"❌ Assessment creation failed for user {user_id[:8]}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/", response_model=AssessmentListResponse)
async def list_assessments(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service),
    limit: int = 10,
    offset: int = 0
):
    """
    List user's assessments.
    
    Args:
        user_id: Current user ID
        db: Database service
        limit: Max results to return
        offset: Pagination offset
    
    Returns:
        List of assessments
    """
    try:
        # Use the new async list_assessments method
        assessments_data, total = await db.list_assessments(user_id, limit, offset)
        assessments = [AssessmentResponse(**item) for item in assessments_data]
        return AssessmentListResponse(assessments=assessments, total=total)
    
    except Exception as e:
        import traceback
        error_logger.error(f"List assessments failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Get specific assessment.
    
    Args:
        assessment_id: Assessment UUID
        user_id: Current user ID
        db: Database service
    
    Returns:
        Assessment data
    """
    try:
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Verify ownership
        if assessment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this assessment")
        
        return AssessmentResponse(**assessment)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assessment_id}/complete", response_model=SuccessResponse)
async def complete_assessment(
    assessment_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Mark assessment as complete and trigger holistic audio analysis.
    
    Args:
        assessment_id: Assessment UUID
        background_tasks: FastAPI background tasks
        user_id: Current user ID
        db: Database service
    
    Returns:
        Success response
    """
    try:
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        if assessment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Resolve student identity for logging
        student = await db.get_student_identity(user_id)
        
        # Calculate stages completed count
        client = db.get_client(use_admin=True)
        responses_result = await asyncio.to_thread(
            lambda: client.table("assessment_responses")
            .select("section", count="exact")
            .eq("assessment_id", assessment_id)
            .execute()
        )
        stages_done = responses_result.count if hasattr(responses_result, 'count') else 0
        
        # Calculate duration
        created_at = assessment.get("created_at", "")
        total_duration = None
        if created_at:
            try:
                start_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                total_duration = (datetime.utcnow().replace(tzinfo=start_dt.tzinfo) - start_dt).total_seconds()
            except Exception:
                pass
        
        # Update status to completed immediately
        updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "stages_completed": stages_done,
        }
        
        updated = await db.update_assessment(assessment_id, updates)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to complete assessment")

        # ---------------------------------------------------------
        # Trigger Holistic Audio Grading (Background)
        # ---------------------------------------------------------
        from app.services.ai_assessment.audio_grader import audio_grader
        from app.core.concurrency import openai_full_semaphore
        
        async def run_audio_grading(assess_id: str):
            # Use semaphore to limit concurrent background grading tasks
            async with openai_full_semaphore:
                try:
                    api_logger.info(f"🎧 [Background] Starting audio grading for {assess_id}...")
                    
                    # Run the grading logic
                    result = await audio_grader.grade_assessment(assess_id)
                    
                    if result.get("error"):
                        error_logger.error(f"❌ Audio grading failed: {result['error']}")
                        return

                    # Calculate total from breakdown if not explicitly present
                    # The prompt returns fields like fluency.score, etc.
                    def get_s(cat): return result.get(cat, {}).get("score", 0)
                    
                    total_score = (
                        get_s("fluency") + get_s("pronunciation") + get_s("grammar") + 
                        get_s("confidence") + get_s("hesitation") + get_s("storytelling") + 
                        get_s("vision_clarity")
                    )
                    total_score = max(0, min(100, total_score))
                    
                    # Determine Grade
                    grade = "beginner"
                    if total_score >= 90: grade = "expert"
                    elif total_score >= 80: grade = "advanced"
                    elif total_score >= 65: grade = "upper_intermediate"
                    elif total_score >= 50: grade = "intermediate"
                    elif total_score >= 30: grade = "elementary"

                    # Save Scores & Details
                    scores_data = {
                        "assessment_id": assess_id,
                        "fluency_score": get_s("fluency"),
                        "pronunciation_score": get_s("pronunciation"),
                        "grammar_score": get_s("grammar"),
                        "confidence_score": get_s("confidence"),
                        "hesitation_penalty": get_s("hesitation"),
                        "storytelling_score": get_s("storytelling"),
                        "vision_clarity_score": get_s("vision_clarity"),
                        "total_score": total_score,
                        "grade": grade,
                        "overall_feedback": result.get("overall_review", ""),
                        "strengths": result.get("strengths", []),
                        "weaknesses": result.get("weaknesses", []),
                        "recommendations": result.get("recommendations", []),
                        "details": result # Store the full detailed reasoning JSON
                    }

                    # Save to DB - Check if scores exist first? Or just insert/upsert.
                    # Since this is "complete", we likely don't have final scores yet. 
                    # Or responses.py created partials. We should ideally upsert or delete old.
                    # Assuming insert for now as this is the definitive final score.
                    
                    client = db.get_client(use_admin=True)
                    
                    # Atomic upsert — avoids race condition between concurrent writers
                    await asyncio.to_thread(lambda: client.table("assessment_scores").upsert(
                        scores_data, on_conflict="assessment_id"
                    ).execute())
                    
                    # Update main assessment total score
                    await asyncio.to_thread(lambda: client.table("assessments").update({
                        "total_score": total_score, 
                        "grade": grade
                    }).eq("id", assess_id).execute())
                    
                    assessment_event_logger.scoring_completed(
                        assessment_id=assess_id,
                        student_name=student["name"],
                        total_score=total_score,
                        grade=grade,
                    )
                    
                except Exception as e:
                    assessment_event_logger.scoring_failed(
                        assessment_id=assess_id,
                        student_name=student["name"],
                        error=str(e),
                    )
                    error_logger.error(f"❌ [Background] Audio grading task error: {e}")

        # Log assessment completion
        assessment_event_logger.completed(
            assessment_id=assessment_id,
            student_name=student["name"],
            stages_done=stages_done,
            total_duration_sec=total_duration,
        )
        
        # CRITICAL: Also log the ASSESSMENT_COMPLETED structured event for analytics
        from app.core.logging import get_logger
        completion_logger = get_logger("completion_tracker")
        completion_logger.info("ASSESSMENT_COMPLETED", extra={
            "event_type": "ASSESSMENT_COMPLETED",
            "assessment_id": assessment_id,
            "student_name": student["name"],
            "stages_completed": stages_done,
            "total_duration_seconds": total_duration,
            "completion_timestamp": datetime.utcnow().isoformat()
        })
        
        background_tasks.add_task(run_audio_grading, assessment_id)
        
        return SuccessResponse(message="Assessment completed successfully. Results are being analyzed.")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{assessment_id}", response_model=SuccessResponse)
async def delete_assessment(
    assessment_id: str,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Delete assessment (soft delete - mark as cancelled).
    
    Args:
        assessment_id: Assessment UUID
        user_id: Current user ID
        db: Database service
    
    Returns:
        Success response
    """
    try:
        assessment = await db.get_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        if assessment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Log who is deleting
        student = await db.get_student_identity(user_id)
        api_logger.info(f"🗑️ Assessment {assessment_id[:8]} cancelled by student=\"{student['name']}\"")
        
        # Update status to cancelled
        updates = {"status": "cancelled"}
        await db.update_assessment(assessment_id, updates)
        
        return SuccessResponse(message="Assessment cancelled successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assessment_id}/heartbeat", response_model=SuccessResponse)
async def assessment_heartbeat(
    assessment_id: str,
    heartbeat: HeartbeatRequest,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Heartbeat endpoint — frontend calls every 30s to signal the assessment is still active.
    Updates last_heartbeat_at and current_section in the database.
    """
    try:
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        if assessment["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update heartbeat timestamp and current stage
        updates = {"last_heartbeat_at": datetime.utcnow().isoformat()}
        if heartbeat.current_stage:
            updates["current_section"] = heartbeat.current_stage

        await db.update_assessment(assessment_id, updates)

        # Log at DEBUG level to avoid noise
        student = await db.get_student_identity(user_id)
        assessment_event_logger.heartbeat(
            assessment_id=assessment_id,
            student_name=student["name"],
            current_stage=heartbeat.current_stage or "unknown",
        )
        return SuccessResponse(message="Heartbeat received")

    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"❌ Heartbeat failed for {assessment_id[:8]}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assessment_id}/abandon", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def abandon_assessment(
    assessment_id: str,
    request: Request,
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Mark assessment as abandoned — called on browser close (beforeunload/sendBeacon),
    back-button navigation, or network failure.

    NOTE: This endpoint intentionally has NO JWT auth requirement.
    sendBeacon() cannot send Authorization headers (browser limitation).
    The 128-bit assessment UUID is the implicit proof of ownership — it is
    unguessable, and an attacker who knows the ID could only mark it as
    'abandoned' (not delete it or modify scores).
    Rate limited to 10/min per IP to prevent flooding.
    
    Supports text/plain payloads to bypass CORS preflight requests.
    """
    import json
    
    # Manually parse the body to support text/plain from navigator.sendBeacon
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        if body_str:
            data = json.loads(body_str)
            reason = data.get("reason", "unknown")
            last_stage = data.get("last_stage", "unknown")
        else:
            reason = "unknown"
            last_stage = "unknown"
    except Exception:
        reason = "unknown"
        last_stage = "unknown"
        
    abandon_data = AssessmentAbandonRequest(reason=reason, last_stage=last_stage)
    # Human-readable reason mapping for logs
    REASON_LABELS = {
        "user_left_assessment": "Candidate navigated away from assessment (back button / dashboard link)",
        "browser_closed": "Candidate closed the browser tab or window",
        "network_error": "Network connection lost during assessment",
        "manual_exit": "Candidate manually exited the assessment",
        "navigation_away": "Candidate navigated to another page",
        "cpu_limit": "System CPU limits exceeded during assessment",
        "memory_limit": "System memory limits exceeded during assessment",
        "timeout_error": "Assessment timed out due to slow response",
        "device_error": "Audio/video device error during assessment",
        "browser_error": "Browser compatibility or runtime error",
        "server_error": "Backend server error during assessment",
        "quota_exceeded": "Resource quota exceeded during assessment",
    }

    try:
        assessment = await db.get_assessment(assessment_id)
        if not assessment:
            # Return 200 silently — sendBeacon doesn't retry on errors
            return SuccessResponse(message="Assessment not found")

        # Only abandon if still in_progress
        if assessment.get("status") != "in_progress":
            return SuccessResponse(message="Assessment already finalized")

        # Count how many stages were completed before abandonment
        client = db.get_client(use_admin=True)
        responses_result = await asyncio.to_thread(
            lambda: client.table("assessment_responses")
            .select("section", count="exact")
            .eq("assessment_id", assessment_id)
            .execute()
        )
        stages_done = responses_result.count if hasattr(responses_result, 'count') else 0

        # Build descriptive reason for the log
        raw_reason = abandon_data.reason or "unknown"
        log_reason = REASON_LABELS.get(raw_reason, raw_reason)

        # Calculate duration
        created_at = assessment.get("created_at", "")
        total_duration = None
        if created_at:
            try:
                start_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                total_duration = (datetime.utcnow().replace(tzinfo=start_dt.tzinfo) - start_dt).total_seconds()
            except Exception:
                pass

        # Update status
        updates = {
            "status": "abandoned",
            "abandon_reason": abandon_data.reason,
            "last_completed_stage": abandon_data.last_stage,
            "stages_completed": stages_done,
            "completed_at": datetime.utcnow().isoformat(),
        }
        await db.update_assessment(assessment_id, updates)

        # Fetch student identity for logging (best-effort)
        student_name = "Unknown"
        try:
            user_id = assessment.get("user_id", "")
            if user_id:
                student = await db.get_student_identity(user_id)
                student_name = student.get("name", "Unknown")
        except Exception:
            pass

        # Log with the human-readable reason
        dur_str = f"  duration={total_duration:.0f}s" if total_duration else ""
        api_logger.warning(
            f"🚨 ABANDONED: student=\"{student_name}\" | assessment={assessment_id[:8]} "
            f"| stages={stages_done}/6 | last_stage={abandon_data.last_stage or 'unknown'}{dur_str} "
            f"| reason: {log_reason}"
        )

        assessment_event_logger.abandoned(
            assessment_id=assessment_id,
            student_name=student_name,
            last_stage=abandon_data.last_stage or "unknown",
            reason=log_reason,
        )
        return SuccessResponse(message="Assessment marked as abandoned")

    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"❌ Abandon failed for {assessment_id[:8]}: {e}")
        raise HTTPException(status_code=500, detail=str(e))