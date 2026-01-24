"""
Assessment API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
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


from jose import jwt

# ...

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Decode token to get user_id (sub)
        # In production, you would verify the signature here
        payload = jwt.get_unverified_claims(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
            
        return user_id
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")


@router.post("/", response_model=AssessmentResponse)
async def create_assessment(
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
        # Ensure profile exists (Self-healing)
        profile = await db.get_profile(user_id)
        if not profile:
            api_logger.info(log_messages.profile_not_found(user_id))
            await db.create_profile(user_id, {"full_name": "User"})
            api_logger.info(log_messages.profile_created(user_id))

        # Create assessment
        metadata = {
            "user_agent": assessment_data.user_agent,
            "ip_address": assessment_data.ip_address
        }
        
        assessment = await db.create_assessment(user_id, metadata)
        
        if not assessment:
            error_logger.error("Failed to create assessment: database returned null")
            raise HTTPException(status_code=500, detail="Failed to create assessment")
        
        api_logger.info(log_messages.assessment_created(assessment["id"], user_id))
        return AssessmentResponse(**assessment)
    
    except Exception as e:
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
        # Query assessments
        client = db.get_client(use_admin=True)
        response = (
            client.table("assessments")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        assessments = [AssessmentResponse(**item) for item in response.data]
        
        # Get total count
        count_response = (
            client.table("assessments")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        
        total = count_response.count if hasattr(count_response, 'count') else len(response.data)
        
        return AssessmentListResponse(assessments=assessments, total=total)
    
    except Exception as e:
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
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Mark assessment as complete.
    
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
        
        # Update status
        updates = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # ---------------------------------------------------------
        # AI Report Generation
        # ---------------------------------------------------------
        try:
            client = db.get_client(use_admin=True)
            
            # 1. Fetch all responses with AI scores
            responses_result = (
                client.table("assessment_responses")
                .select("ai_classification")
                .eq("assessment_id", assessment_id)
                .execute()
            )
            
            scores_list = [
                r["ai_classification"] 
                for r in responses_result.data 
                if r.get("ai_classification")
            ]
            
            if scores_list:
                # 2. Generate Report
                api_logger.info(log_messages.report_generation_started(assessment_id, len(scores_list)))
                report = report_generator.generate_report(scores_list)
                metrics = report.get("metrics", {})
                
                # 3. Update Assessment Total Score
                updates["total_score"] = metrics.get("total_score", 0)
                
                # 4. Save Detailed Report to 'assessment_scores'
                scores_data = {
                    "assessment_id": assessment_id,
                    "fluency_score": metrics.get("fluency", 0),
                    "pronunciation_score": metrics.get("pronunciation", 0),
                    "grammar_score": metrics.get("grammar", 0),
                    "confidence_score": metrics.get("confidence", 0),
                    "hesitation_penalty": metrics.get("hesitation", 0),
                    "storytelling_score": metrics.get("storytelling", 0),
                    "vision_clarity_score": metrics.get("vision_clarity", 0),
                    "total_score": metrics.get("total_score", 0),
                    "overall_feedback": report.get("summary", ""),
                    "strengths": report.get("strengths", []),
                    "weaknesses": report.get("weaknesses", []),
                    "recommendations": report.get("recommendations", [])
                }
                await db.save_scores(scores_data)
                api_logger.info(log_messages.report_generation_completed(assessment_id, metrics.get("total_score", 0)))
                
        except Exception as e:
            error_logger.error(log_messages.report_generation_failed(assessment_id, str(e)))
            # Don't fail the completion just because report failed
            pass
            
        updated = await db.update_assessment(assessment_id, updates)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to complete assessment")
        
        return SuccessResponse(message="Assessment completed successfully")
    
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
