"""
Assessment API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Request
import asyncio
from typing import Optional, List
from app.models.schemas import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentListResponse,
    SuccessResponse,
    ErrorResponse
)
from app.services.supabase_client import SupabaseService, get_supabase_service
from app.services.ai_assessment.report_generator import report_generator
from datetime import datetime

# Import logging and messages
from app.core.logging import api_logger, error_logger
from app.core import log_messages

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])


from app.core.auth import get_current_user_id

# Use a local limiter instance JUST for the decorators to attach metadata.
# The actual rate limiting is handled globally by the Limiter in main.py.
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)


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
            # Count completed + in_progress assessments for this user
            completed_count = await asyncio.to_thread(
                lambda: client.table("assessments")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("status", "completed")
                .execute()
            )
            in_progress_count = await asyncio.to_thread(
                lambda: client.table("assessments")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("status", "in_progress")
                .execute()
            )
            total_attempts = (completed_count.count if hasattr(completed_count, 'count') else 0) + \
                             (in_progress_count.count if hasattr(in_progress_count, 'count') else 0)
            
            if total_attempts >= 2:
                api_logger.warning(f"⛔ Candidate {user_id[:8]} blocked: {total_attempts} attempts (limit: 2)")
                raise HTTPException(
                    status_code=403,
                    detail="Assessment limit reached. Candidates are allowed a maximum of 2 attempts."
                )
            api_logger.info(f"✅ Candidate {user_id[:8]} attempt {total_attempts + 1}/2 allowed")

        # Create assessment
        # Create assessment
        # Metadata fields (user_agent, ip_address) are currently not supported by the DB schema
        # We pass empty metadata to avoid PGRST204 error
        assessment = await db.create_assessment(user_id, {})
        
        if not assessment:
            error_logger.error("❌ Failed to create assessment: database returned null")
            raise HTTPException(status_code=500, detail="Failed to create assessment")
        
        api_logger.info(log_messages.assessment_created(assessment["id"], user_id))
        api_logger.info(f"✅ Assessment creation complete: {assessment['id'][:8]}")
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
        api_logger.info(log_messages.request_received("GET", f"/api/v1/assessments/?limit={limit}&offset={offset}"))
        
        # Use the new async list_assessments method
        assessments_data, total = await db.list_assessments(user_id, limit, offset)
        
        assessments = [AssessmentResponse(**item) for item in assessments_data]
        
        api_logger.info(f"📋 Returning {len(assessments)} assessments for user {user_id[:8]}")
        return AssessmentListResponse(assessments=assessments, total=total)
    
    except Exception as e:
        error_logger.error(f"❌ List assessments failed: {str(e)}")
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
        
        # Update status to completed immediately
        updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        updated = await db.update_assessment(assessment_id, updates)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to complete assessment")

        # ---------------------------------------------------------
        # Trigger Holistic Audio Grading (Background)
        # ---------------------------------------------------------
        from app.services.ai_assessment.audio_grader import audio_grader
        
        async def run_audio_grading(assess_id: str):
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
                
                api_logger.info(f"✅ [Background] Audio grading complete. Score: {total_score}")
                
            except Exception as e:
                error_logger.error(f"❌ [Background] Audio grading task error: {e}")

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
        
        # Update status to cancelled
        updates = {"status": "cancelled"}
        await db.update_assessment(assessment_id, updates)
        
        return SuccessResponse(message="Assessment cancelled successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
