"""
Admin router for managing users and assessments.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.supabase_client import get_supabase_service, SupabaseService
from app.services.blob_storage import get_blob_storage_service, BlobStorageService
from app.models.schemas import (
    UserProfile,
    AdminDashboardStats,
    AdminAssessmentListResponse,
    AdminAssessmentDetail,
    AdminAssessmentListItem,
    AssessmentStatus,
    AssessmentGrade
)
from app.core.logging import api_logger

router = APIRouter(prefix="/admin", tags=["Admin"])

# mocked admin dependency for now - later integrate with real auth
async def get_current_admin_user(token: str = Depends(lambda: "admin_token")): # Placeholder
    # In real implementation: verify token, check role
    # For now, we assume admin access if they hit this endpoint
    # Retrieve user from token -> check if role is admin
    return {"id": "admin_id", "role": "admin"}

@router.get("/stats", response_model=AdminDashboardStats)
async def get_admin_dashboard_stats(
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Get admin dashboard statistics.
    """
    stats = await supabase.get_admin_stats()
    return stats

@router.get("/users")
async def list_users(
    limit: int = 10,
    offset: int = 0,
    search: Optional[str] = None,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    List all users.
    """
    users, count = await supabase.get_all_users(limit, offset, search)
    # Convert to UserProfile list
    return {
        "users": users,
        "total": count,
        "page": (offset // limit) + 1,
        "limit": limit
    }

@router.get("/assessments", response_model=AdminAssessmentListResponse)
async def list_assessments(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    List all assessments.
    """
    data, count = await supabase.get_all_assessments(limit, offset, status)
    
    # Map to AdminAssessmentListItem
    # Supabase join returns profiles as a nested dict, e.g. profiles: {email: ...}
    assessments = []
    for item in data:
        user_profile = item.get("profiles", {})
        scores = item.get("assessment_scores", {})
        
        # Handle cases where scores might be a list (one-to-many) or dict
        total_score = None
        grade = None
        if isinstance(scores, list) and scores:
            total_score = scores[0].get("total_score")
            grade = scores[0].get("grade")
        elif isinstance(scores, dict):
            total_score = scores.get("total_score")
            grade = scores.get("grade")

        assessments.append(AdminAssessmentListItem(
            id=item["id"],
            user_id=item["user_id"],
            user_email=user_profile.get("email", "Unknown"),
            user_name=user_profile.get("full_name"),
            status=item["status"],
            created_at=item["created_at"],
            completed_at=item.get("completed_at"),
            total_score=total_score,
            grade=grade
        ))

    return {
        "assessments": assessments,
        "total": count,
        "page": (offset // limit) + 1,
        "limit": limit
    }

@router.get("/assessments/{assessment_id}", response_model=AdminAssessmentDetail)
async def get_assessment_detail(
    assessment_id: str,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Get detailed assessment view.
    """
    details = await supabase.get_assessment_details_full(assessment_id)
    if not details:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Construct timeline
    # Timeline includes stages derived from responses or a fixed list
    # For now, we can infer from responses
    responses = details["responses"]
    timeline = []
    for resp in responses:
        timeline.append({
            "stage": resp.get("section"),
            "status": "completed",
            "score": resp.get("pronunciation_score"), # Just an example
            "duration": resp.get("audio_duration")
        })
    
    # If no responses, we might want to show empty timeline or default stages
    if not timeline:
        # Default stages
        stages = ["introduction", "reading", "listening", "storytelling", "opinion", "aim"]
        for stage in stages:
            timeline.append({"stage": stage, "status": "pending"})

    return {
        "assessment": details["assessment"],
        "user": details["user"],
        "scores": details["scores"],
        "responses": responses,
        "timeline": timeline
    }

@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    supabase: SupabaseService = Depends(get_supabase_service),
    blob_storage: BlobStorageService = Depends(get_blob_storage_service)
):
    """
    Delete an assessment and all associated data (DB + Blobs).
    """
    # 1. Fetch assessment to get user_id (needed for blob path)
    assessment = await supabase.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    user_id = assessment["user_id"]
    
    # 2. Delete Blobs (Audio)
    # This deletes all files under user_id/assessment_id/
    success, error = await blob_storage.delete_assessment_audio(user_id, assessment_id)
    if not success:
        # Log error but proceed to delete DB record so we don't end up in inconsistent state
        # (Or maybe we should fail? Usually better to clean up DB even if blobs fail, or use a background task)
        api_logger.warning(f"Failed to delete blobs for assessment {assessment_id}: {error}")

    # 3. Delete DB Record
    # Cascades to responses, scores, etc.
    deleted = await supabase.delete_assessment(assessment_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete assessment from database")
        
    return {"message": "Assessment deleted successfully"}

@router.get("/assessments/{assessment_id}/audio/{section}")
async def get_audio_sas_url(
    assessment_id: str,
    section: str,
    supabase: SupabaseService = Depends(get_supabase_service),
    blob_storage: BlobStorageService = Depends(get_blob_storage_service)
):
    """
    Get SAS URL for audio playback.
    """
    # Verify assessment exists
    assessment = await supabase.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    user_id = assessment["user_id"]
    
    # Query DB to find the actual audio file path for this section
    client = supabase.get_client(use_admin=True)
    response = (
        client.table("assessment_responses")
        .select("audio_url")
        .eq("assessment_id", assessment_id)
        .eq("section", section)
        .execute()
    )
    
    if not response.data or not response.data[0].get("audio_url"):
        raise HTTPException(status_code=404, detail="Audio not found for this section")
        
    saved_url = response.data[0]["audio_url"]
    
    # Extract blob name from URL
    # Format usually: https://account.blob.core.windows.net/container/BlobName.wav?sas...
    # We need just 'BlobName.wav'
    container_name = blob_storage.container_name
    try:
        # Split by container name to get the path after it
        file_part = saved_url.split(f"/{container_name}/")[-1]
        # Remove any existing query params (SAS token)
        blob_name = file_part.split("?")[0]
        # Decode URL encoding if needed (though usually fine)
        from urllib.parse import unquote
        blob_name = unquote(blob_name)
    except Exception as e:
        error_logger.error(f"Failed to parse blob name from URL {saved_url}: {e}")
        raise HTTPException(status_code=500, detail="Invalid audio record")

    if not blob_storage.check_blob_exists(blob_name):
        raise HTTPException(status_code=404, detail="Audio file missing from storage")

    sas_url = blob_storage.generate_sas_url(blob_name)
    
    return {"url": sas_url}
