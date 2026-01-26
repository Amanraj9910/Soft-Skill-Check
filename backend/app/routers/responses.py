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
    Upload audio -> Transcribe -> AI Analyze -> AI Reply (TTS).
    """

    try:
        api_logger.info(f"🎤 Audio upload received for response_id={response_id}")
        
        # 1. Validation & Metadata
        client = db.get_client(use_admin=True)
        response_result = (
            client.table("assessment_responses")
            .select("*, assessments!inner(user_id)")
            .eq("id", response_id)
            .execute()
        )
        
        if not response_result.data:
            error_logger.error(f"❌ Response not found for ID: {response_id}")
            raise HTTPException(status_code=404, detail="Response not found")
        
        response_data = response_result.data[0]
        question_text = response_data["question_text"]
        section_name = response_data.get("section", "response")
        user_id = response_data["assessments"]["user_id"]
        
        api_logger.info(f"✅ Found response record. Question: {question_text[:30]}...")

        # Fetch user profile for filename
        try:
            profile_result = client.table("profiles").select("full_name").eq("id", user_id).execute()
            user_name = "User"
            if profile_result.data and profile_result.data[0].get("full_name"):
                user_name = profile_result.data[0]["full_name"]
            
            # Sanitize filename components
            safe_user_name = "".join([c for c in user_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
            safe_section = "".join([c for c in section_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
            
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            custom_filename = f"{safe_user_name}_{safe_section}_{date_str}.wav"
        except Exception as e:
            error_logger.warning(f"Failed to generate custom filename: {e}")
            custom_filename = None # Fallback to UUID in storage service

        # 2. Upload Audio to Blob
        audio_bytes = await audio_file.read()
        file_size_kb = len(audio_bytes) / 1024
        api_logger.info(f"📤 Uploading audio ({file_size_kb:.2f} KB) to Azure Blob Storage as {custom_filename}...")
        
        blob_name = storage_service.upload_file(audio_bytes, filename=custom_filename, content_type=audio_file.content_type)
        audio_url = storage_service.generate_sas_url(blob_name)
        api_logger.info(f"✅ Audio uploaded successfully. Blob: {blob_name}")
        
        # 3. Transcribe (STT)
        ai_logger.info("🗣️ Sending audio to Azure Speech-to-Text...")
        transcript = speech_service.transcribe_audio(audio_bytes)
        ai_logger.info(f"✅ Transcription complete. Length: {len(transcript)} chars. Text: \"{transcript[:50]}...\"")
        
        # 4. AI Analysis (Scoring + Reply)
        ai_logger.info("🧠 Sending transcript to GPT-4o for analysis...")
        analysis = scoring_engine.analyze_response(transcript, question_text)
        ai_logger.info(f"✅ AI Analysis complete. Reply: \"{analysis.ai_response_text[:50]}...\"")
        
        # 5. Generate AI Audio (TTS)
        ai_audio_blob = None
        ai_audio_url = None
        if analysis.ai_response_text:
            ai_logger.info("🔊 Generating AI voice response (TTS)...")
            ai_audio_url = speech_service.synthesize_speech(analysis.ai_response_text)
            ai_logger.info("✅ AI Voice generated.")

        # 6. Save to Database
        db_logger.info("💾 Saving results to Supabase...")
        
        # Prepare update data
        update_data = {
            "audio_url": audio_url,
            "user_transcript": transcript,
            "agent_transcript": analysis.ai_response_text,
            "ai_classification": analysis.scores.dict() if analysis.scores else None
        }
        
        # Map individual scores to columns if they exist
        if analysis.scores:
            update_data["fluency_score"] = analysis.scores.fluency
            update_data["pronunciation_score"] = analysis.scores.pronunciation
            update_data["accuracy_score"] = analysis.scores.grammar # Map grammar to accuracy
            # completeness_score not directly in our new rubric, leaving as is or could map storytelling
            
        # Update response record
        client.table("assessment_responses").update(update_data).eq("id", response_id).execute()
        api_logger.info("✅ Database updated. Complete assessment step processed successfully")
        
        # Save detailed scores to a separate table if needed, or just keep in ai_classificationjson
        # For now, we return it to frontend
        
        return AIInteractionResponse(
            transcript=transcript,
            ai_response_text=analysis.ai_response_text,
            ai_audio_url=ai_audio_url,
            scores=analysis.scores.dict() if analysis.scores else {},
            feedback=analysis.scores.feedback if analysis.scores else ""
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error_logger.error(f"Error processing audio upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e)}")


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
