"""
Conversation API endpoints for real-time assessment interaction.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import Optional
import tempfile
import os

from app.models.schemas import (
    ConversationRequest,
    ConversationResponse,
    SpeechToTextRequest,
    SpeechToTextResponse,
    AudioUploadResponse
)
from app.services.azure_speech import AzureSpeechService, get_azure_speech_service
from app.services.azure_openai import AzureOpenAIService, get_azure_openai_service
from app.services.blob_storage import BlobStorageService, get_blob_storage_service
from app.services.supabase_client import SupabaseService, get_supabase_service

router = APIRouter(prefix="/api/v1/conversation", tags=["Conversation"])


@router.post("/generate-response", response_model=ConversationResponse)
async def generate_agent_response(
    request: ConversationRequest,
    openai_service: AzureOpenAIService = Depends(get_azure_openai_service),
    speech_service: AzureSpeechService = Depends(get_azure_speech_service)
):
    """
    Generate AI agent response for conversation.
    
    Args:
        request: Conversation request with history and user message
        openai_service: Azure OpenAI service
        speech_service: Azure Speech service
    
    Returns:
        Agent response with text and audio URL
    """
    try:
        # Convert conversation history to format expected by OpenAI
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        # Generate text response
        response = await openai_service.generate_agent_response(
            conversation_history=history,
            current_section=request.section.value,
            user_message=request.user_message
        )
        
        if not response["success"]:
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to generate response"))
        
        agent_message = response["message"]
        
        # Generate audio from text
        success, audio_path, error = await speech_service.text_to_speech(agent_message)
        
        audio_url = None
        if success and audio_path:
            # For now, audio is in temp file
            # In production, upload to blob storage
            audio_url = f"/api/v1/conversation/audio/{os.path.basename(audio_path)}"
        
        return ConversationResponse(
            agent_message=agent_message,
            audio_url=audio_url,
            tokens_used=response.get("tokens_used")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def convert_speech_to_text(
    audio_file: UploadFile = File(...),
    reference_text: Optional[str] = None,
    speech_service: AzureSpeechService = Depends(get_azure_speech_service)
):
    """
    Convert speech audio to text with optional pronunciation assessment.
    
    Args:
        audio_file: Uploaded audio file
        reference_text: Expected text for pronunciation assessment
        speech_service: Azure Speech service
    
    Returns:
        Transcript and pronunciation scores
    """
    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_audio_path = os.path.join(temp_dir, f"upload_{os.urandom(8).hex()}_{audio_file.filename}")
        
        with open(temp_audio_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Perform speech-to-text
        result = await speech_service.speech_to_text(
            audio_file_path=temp_audio_path,
            enable_pronunciation_assessment=bool(reference_text),
            reference_text=reference_text
        )
        
        # Clean up temp file
        try:
            os.remove(temp_audio_path)
        except:
            pass
        
        return SpeechToTextResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(
    audio_file: UploadFile = File(...),
    user_id: str = "",
    assessment_id: str = "",
    section: str = "",
    is_full_conversation: bool = False,
    storage_service: BlobStorageService = Depends(get_blob_storage_service)
):
    """
    Upload audio file to blob storage.
    
    Args:
        audio_file: Audio file to upload
        user_id: User UUID
        assessment_id: Assessment UUID
        section: Section name
        is_full_conversation: Whether this is the full conversation audio
        storage_service: Blob storage service
    
    Returns:
        Upload status and blob URL
    """
    try:
        # Read audio bytes
        audio_bytes = await audio_file.read()
        
        # Upload to blob storage
        success, blob_url, error = await storage_service.upload_audio_bytes(
            audio_bytes=audio_bytes,
            user_id=user_id,
            assessment_id=assessment_id,
            section=section,
            is_full_conversation=is_full_conversation
        )
        
        if not success:
            return AudioUploadResponse(
                success=False,
                error=error
            )
        
        # Calculate duration (simplified - use actual audio processing)
        duration = len(audio_bytes) / 32000  # Rough estimate
        
        return AudioUploadResponse(
            success=True,
            audio_url=blob_url,
            duration=duration
        )
    
    except Exception as e:
        return AudioUploadResponse(
            success=False,
            error=str(e)
        )


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve temporary audio file.
    
    Args:
        filename: Audio filename
    
    Returns:
        Audio file response
    """
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file  not found")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )
