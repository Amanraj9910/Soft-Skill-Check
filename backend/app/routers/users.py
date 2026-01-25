"""
Authentication and user management endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.models.schemas import UserProfile, SuccessResponse
from app.services.supabase_client import SupabaseService, get_supabase_service

# Import logging and messages
from app.core.logging import api_logger
from app.core import log_messages

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


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
        payload = jwt.get_unverified_claims(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
            
        return user_id
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")


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
            # Auto-create profile if it doesn't exist (Self-healing)
            api_logger.info(log_messages.profile_not_found(user_id))
            profile = await db.create_profile(user_id, {"full_name": "User"})
            api_logger.info(log_messages.profile_created(user_id))
            
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found and could not be created")
        
        # Log successful authentication with user name
        user_name = profile.get("full_name", "Unknown User")
        api_logger.info(f"✅ User authenticated: {user_name} (user_id={user_id})")
        
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
            # Auto-create profile if missing
            profile = await db.create_profile(user_id, {"full_name": "User"})
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


@router.post("/login-event", response_model=SuccessResponse)
async def track_login_event(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Track user login event (called from frontend after Supabase auth).
    
    Args:
        user_id: Current user ID from auth
        db: Database service
    
    Returns:
        Success response
    """
    try:
        profile = await db.get_profile(user_id)
        user_name = profile.get("full_name", "Unknown User") if profile else "Unknown User"
        
        # Log login event with user name
        api_logger.info(f"🔐 User logged in: {user_name} (user_id={user_id})")
        
        return SuccessResponse(message="Login event tracked")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout-event", response_model=SuccessResponse)
async def track_logout_event(
    user_id: str = Depends(get_current_user_id),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Track user logout event (called from frontend before clearing Supabase session).
    
    Args:
        user_id: Current user ID from auth
        db: Database service
    
    Returns:
        Success response
    """
    try:
        profile = await db.get_profile(user_id)
        user_name = profile.get("full_name", "Unknown User") if profile else "Unknown User"
        
        # Log logout event with user name
        api_logger.info(f"🚪 User logged out: {user_name} (user_id={user_id})")
        
        return SuccessResponse(message="Logout event tracked")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
