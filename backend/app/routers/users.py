"""
Authentication and user management endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.models.schemas import UserProfile, SuccessResponse
from app.services.supabase_client import SupabaseService, get_supabase_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from authorization header.
    
    For development, this is simplified. In production, implement proper JWT verification.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    # TODO: Implement proper JWT verification with Supabase
    # For now, accepting token as user_id for development
    return token


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Get current user's profile.
    
    Args:
        user_id: Current user ID from auth
        db: Database service
    
    Returns:
        User profile
    """
    try:
        profile = await db.get_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return UserProfile(**profile)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/me", response_model=UserProfile)
async def update_current_user(
    updates: dict,
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Update current user's profile.
    
    Args:
        updates: Fields to update
        user_id: Current user ID
        db: Database service
    
    Returns:
        Updated profile
    """
    try:
        client = db.get_client(use_admin=True)
        
        # Only allow updating specific fields
        allowed_fields = ["full_name", "bio", "avatar_url", "language_preference", "timezone"]
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        result = (
            client.table("profiles")
            .update(filtered_updates)
            .eq("id", user_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return UserProfile(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_user_stats(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Get user's assessment statistics.
    
    Args:
        user_id: Current user ID
        db: Database service
    
    Returns:
        Statistics dictionary
    """
    try:
        profile = await db.get_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get additional stats from assessments
        client = db.get_client(use_admin=True)
        
        # Count by status
        completed = (
            client.table("assessments")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
        )
        
        in_progress = (
            client.table("assessments")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "in_progress")
            .execute()
        )
        
        # Get score distribution
        scores = (
            client.table("assessments")
            .select("total_score")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .not_.is_("total_score", "null")
            .execute()
        )
        
        score_list = [s["total_score"] for s in scores.data if s["total_score"] is not None]
        
        return {
            "total_assessments": profile.get("total_assessments", 0),
            "average_score": profile.get("average_score", 0),
            "completed_assessments": completed.count if hasattr(completed, 'count') else 0,
            "in_progress_assessments": in_progress.count if hasattr(in_progress, 'count') else 0,
            "highest_score": max(score_list) if score_list else 0,
            "lowest_score": min(score_list) if score_list else 0,
            "last_assessment_at": profile.get("last_assessment_at")
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
