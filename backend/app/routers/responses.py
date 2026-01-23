"""
Response management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional

from app.models.schemas import ResponseCreate, ResponseData, SuccessResponse
from app.services.supabase_client import SupabaseService, get_supabase_service
from app.services.audio_analysis import AudioAnalysisService, get_audio_analysis_service
from app.services.blob_storage import BlobStorageService, get_blob_storage_service

router = APIRouter(prefix="/api/v1/responses", tags=["Responses"])


@router.post("/", response_model=ResponseData)
async def create_response(
    response_data: ResponseCreate,
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Create an assessment response.
    
    Args:
        response_data: Response data
        db: Database service
    
    Returns:
        Created response
    """
    try:
        # Create response
        response = await db.create_response(response_data.dict())
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to create response")
        
        return ResponseData(**response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{response_id}/audio", response_model=SuccessResponse)
async def upload_response_audio(
    response_id: str,
    audio_file: UploadFile = File(...),
    db: SupabaseService = Depends(get_supabase_service),
    storage: BlobStorageService = Depends(get_blob_storage_service),
    audio_service: AudioAnalysisService = Depends(get_audio_analysis_service)
):
    """
    Upload audio for a response and extract features.
    
    Args:
        response_id: Response UUID
        audio_file: Audio file
        db: Database service
        storage: Blob storage service
        audio_service: Audio analysis service
    
    Returns:
        Success response
    """
    try:
        # Get response to get assessment_id and user_id
        client = db.get_client(use_admin=True)
        response_result = (
            client.table("assessment_responses")
            .select("*, assessments!inner(user_id)")
            .eq("id", response_id)
            .execute()
        )
        
        if not response_result.data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        response_data = response_result.data[0]
        user_id = response_data["assessments"]["user_id"]
        assessment_id = response_data["assessment_id"]
        section = response_data["section"]
        
        # Read audio bytes
        audio_bytes = await audio_file.read()
        
        # Upload to blob storage
        success, blob_url, error = await storage.upload_audio_bytes(
            audio_bytes=audio_bytes,
            user_id=user_id,
            assessment_id=assessment_id,
            section=section,
            is_full_conversation=False
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to upload audio: {error}")
        
        # Save audio temporarily for feature extraction
        import tempfile
        import os
        temp_path = os.path.join(tempfile.gettempdir(), f"temp_{response_id}.wav")
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        
        # Extract audio features
        features_result = await audio_service.extract_features(temp_path)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        # Update response with audio URL
        client.table("assessment_responses").update({
            "audio_url": blob_url,
            "audio_duration": int(features_result.get("features", {}).get("duration", 0))
        }).eq("id", response_id).execute()
        
        # Save audio features if extraction succeeded
        if features_result.get("success"):
            features_data = {
                "response_id": response_id,
                **features_result["features"]
            }
            await db.save_audio_features(features_data)
        
        return SuccessResponse(message="Audio uploaded and features extracted successfully")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{response_id}/vision", response_model=SuccessResponse)
async def save_vision_metrics(
    response_id: str,
    metrics: dict,
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Save vision metrics for a response.
    
    Args:
        response_id: Response UUID
        metrics: Vision metrics data
        db: Database service
    
    Returns:
        Success response
    """
    try:
        metrics["response_id"] = response_id
        
        saved = await db.save_vision_metrics(metrics)
        
        if not saved:
            raise HTTPException(status_code=500, detail="Failed to save vision metrics")
        
        return SuccessResponse(message="Vision metrics saved successfully")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{response_id}", response_model=ResponseData)
async def get_response(
    response_id: str,
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Get a specific response.
    
    Args:
        response_id: Response UUID
        db: Database service
    
    Returns:
        Response data
    """
    try:
        client = db.get_client(use_admin=True)
        result = (
            client.table("assessment_responses")
            .select("*")
            .eq("id", response_id)
            .execute()
        )
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        return ResponseData(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
