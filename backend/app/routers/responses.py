"""
Response management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional

from app.models.schemas import ResponseCreate, ResponseData, SuccessResponse, AIInteractionResponse
from app.services.supabase_client import SupabaseService, get_supabase_service
# Import new AI Assessment services
from app.services.ai_assessment.azure_storage import storage_service
from app.services.ai_assessment.azure_speech import speech_service
from app.services.ai_assessment.scoring_engine import scoring_engine
from app.agents.conversational_agent import conversational_agent
from app.services.session_manager import session_manager
import httpx
from datetime import datetime
import base64

# Import new structured logging
from app.core.logging import api_logger, ai_logger, db_logger, error_logger
from app.core import log_messages

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
        api_logger.info(f"Creating assessment response: assessment_id={response_data.assessment_id}, section={response_data.section}")
        
        # Create response
        response = await db.create_response(response_data.dict())
        
        if not response:
            error_logger.error("Failed to create response: database returned null")
            raise HTTPException(status_code=500, detail="Failed to create response")
        
        api_logger.info(f"Assessment response created successfully: response_id={response['id']}")
        return ResponseData(**response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{response_id}/audio", response_model=AIInteractionResponse)
async def upload_response_audio(
    response_id: str,
    audio_file: UploadFile = File(...),
    db: SupabaseService = Depends(get_supabase_service)
):
    """
    Upload audio -> STT -> Agent Logic -> TTS -> Session Storage.
    Only merges and uploads full conversation to blob when transitioning sections.
    """
    try:
        api_logger.info(f"🎤 conversational audio upload for response_id={response_id}")
        
        # 1. Validation & Metadata
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
        section_name = response_data.get("section", "response")
        user_id = response_data["assessments"]["user_id"]

        # 2. Get/Create Session
        session = session_manager.get_session(response_id)
        
        # 3. Transcribe User Audio
        audio_bytes = await audio_file.read()
        
        # Convert to standard WAV immediately to avoid pydub/ffmpeg issues downstream
        wav_audio_bytes = speech_service.convert_to_wav(audio_bytes)
        
        # Add user audio to session (ONLY user audio is merged now, as requested)
        if wav_audio_bytes:
            session['audio_merger'].add_clip(wav_audio_bytes, speaker='user')
            
        transcript = speech_service.transcribe_audio(wav_audio_bytes if wav_audio_bytes else audio_bytes)
        
        # Add to history
        session['conversation_history'].append({"user": transcript})
        session['conversation_history'].append({"user": transcript})
        session['turn_count'] += 1
        
        api_logger.info(f"🗣️ User transcript: {transcript[:50]}...")

        # 4. Get Agent Response
        agent_result = conversational_agent.get_response(
            user_message=transcript,
            section=section_name,
            conversation_history=session['conversation_history'][:-1], # Exclude current turn for history context if needed, or include it. Agent logic handles it.
            turn_count=session['turn_count']
        )
        
        ai_response_text = agent_result["agent_message"]
        should_transition = agent_result["should_transition"]
        next_section = agent_result["next_section"]
        
        # Update session with agent response
        session['conversation_history'][-1]["agent"] = ai_response_text
        
        # 5. Generate AI Audio (TTS)
        ai_audio_url = None
        if ai_response_text:
            api_logger.info("🔊 Generating AI voice response...")
            
            # Use new method to get bytes directly without blob upload
            ai_audio_bytes = speech_service.synthesize_speech_bytes(ai_response_text)
            
            if ai_audio_bytes:
                # Add to session merger - SKIPPED FOR MERGING as per user request
                # We only want user response in blob, merged with pauses.
                # session['audio_merger'].add_clip(ai_audio_bytes, speaker='agent')
                
                # Convert to Data URI for frontend playback
                b64_audio = base64.b64encode(ai_audio_bytes).decode('utf-8')
                ai_audio_url = f"data:audio/wav;base64,{b64_audio}"
            else:
                 error_logger.error("Failed to generate AI audio bytes")

        # 6. Handle Transition (Merge & Finalize)
        final_audio_url = None
        
        if should_transition:
            api_logger.info(f"🏁 Section '{section_name}' complete. Merging conversation...")
            
            merged_audio = session['audio_merger'].merge_conversation()
            
            if merged_audio:
                # Generate filename: UserName_Section_Date.wav
                try:
                    profile = client.table("profiles").select("full_name").eq("id", user_id).execute()
                    user_name = profile.data[0].get("full_name", "User") if profile.data else "User"
                    safe_name = "".join([c for c in user_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
                    safe_section = section_name.replace(' ', '_')
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"{safe_name}_{safe_section}_{timestamp}.wav"
                except:
                    filename = f"conversation_{response_id}_{datetime.now().timestamp()}.wav"
                
                # Upload final merged conversation
                blob_name = storage_service.upload_file(merged_audio, filename=filename, content_type="audio/wav")
                final_audio_url = storage_service.generate_sas_url(blob_name)
                
                # Update DB
                client.table("assessment_responses").update({
                    "audio_url": final_audio_url,
                    "conversation_history": session['conversation_history'],
                    # Maybe score here too? For now we score at the end or valid transition
                }).eq("id", response_id).execute()
                
                # Clear session
                session_manager.clear_session(response_id)
            
        # 7. Return Response
        return AIInteractionResponse(
            transcript=transcript,
            ai_response_text=ai_response_text,
            ai_audio_url=ai_audio_url,
            scores={}, # We can add interim scores if needed
            feedback="",
            should_transition=should_transition,
            next_section=next_section
        )

    except Exception as e:
        error_logger.error(f"Error in conversational upload: {str(e)}", exc_info=True)
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
        api_logger.info(f"Saving vision metrics for response_id={response_id}")
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
