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
from datetime import datetime

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
        # Create assessment
        metadata = {
            "user_agent": assessment_data.user_agent,
            "ip_address": assessment_data.ip_address
        }
        
        assessment = await db.create_assessment(user_id, metadata)
        
        if not assessment:
            raise HTTPException(status_code=500, detail="Failed to create assessment")
        
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
