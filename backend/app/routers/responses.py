"""
Response management API endpoints.
"""
import asyncio
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from typing import Optional

from app.models.schemas import ResponseCreate, ResponseData, SuccessResponse, AIInteractionResponse
from app.services.supabase_client import SupabaseService, get_supabase_service
from app.services.ai_assessment.azure_storage import storage_service
from app.services.ai_assessment.azure_speech import speech_service
from app.services.ai_assessment.scoring_engine import scoring_engine
from app.agents.conversational_agent import conversational_agent
import httpx
from datetime import datetime
import base64
import os
import tempfile
import io
from pydub import AudioSegment

# Import new structured logging
from app.core.logging import api_logger, ai_logger, db_logger, error_logger
from app.core import log_messages

from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

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


from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks


# Define background task function
async def process_transition_background(
    response_id: str,
    user_id: str,
    assessment_id: str,
    section: str,
    blob_clip_prefix: str,
    update_payload: dict,
    client: SupabaseService
):
    try:
        api_logger.info(f"⏳ [Background] Processing transition for {section}...")
        
        # 1. Download clips from blob, merge into a single WAV
        merged_audio = None
        clip_blobs = await storage_service.list_blobs(blob_clip_prefix)
        # Sort by clip number
        clip_blobs.sort(key=lambda name: int(name.rsplit("clip_", 1)[-1].split(".")[0]))
        
        if clip_blobs:
            api_logger.info(f"Merging {len(clip_blobs)} audio clips from blob storage...")
            frame_rate = 16000
            combined = AudioSegment.silent(duration=500, frame_rate=frame_rate)
            silence_between = AudioSegment.silent(duration=1000, frame_rate=frame_rate)
            
            for i, blob_name in enumerate(clip_blobs):
                try:
                    clip_bytes = await storage_service.download_blob_bytes(blob_name)
                    if clip_bytes:
                        audio_segment = AudioSegment.from_wav(io.BytesIO(clip_bytes))
                        combined += audio_segment
                        if i < len(clip_blobs) - 1:
                            combined += silence_between
                except Exception as e:
                    error_logger.error(f"Failed to merge clip {blob_name}: {str(e)}")
            
            output = io.BytesIO()
            combined.export(output, format='wav')
            merged_audio = output.getvalue()
        
        if merged_audio:
            # 2. Upload merged conversation to blob
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            merged_blob_path = f"audio/merged/{user_id}/{assessment_id}/{section}_{timestamp}.wav"
            merged_url = await storage_service.upload_audio_bytes(
                merged_audio, merged_blob_path, content_type="audio/wav"
            )
            update_payload["audio_url"] = merged_url
            
        # 3. Update DB with Transcript & Audio URL
        await asyncio.to_thread(lambda: client.table("assessment_responses").update(update_payload).eq("id", response_id).execute())
        
        api_logger.info(f"✅ [Background] Transition processing complete for {section}")
        
    except Exception as e:
        error_logger.error(f"❌ [Background] Failed to process transition: {e}")
    finally:
        # 4. Clean up individual clip blobs
        for blob_name in clip_blobs:
            try:
                await storage_service.delete_blob(blob_name)
            except Exception as cleanup_err:
                error_logger.warning(f"Failed to clean up clip blob {blob_name}: {str(cleanup_err)}")


async def finalize_assessment(
    assessment_id: str,
    user_id: str,
    conversation_history: list,
    client: SupabaseService
):
    """
    Background task to perform holistic analysis and finalize assessment.
    """
    try:
        api_logger.info(f"🏁 [Background] Finalizing assessment {assessment_id}...")
        
        # 1. Prepare Data
        full_transcript = " ".join([
            f"User: {turn.get('user','')} Agent: {turn.get('agent','')}" 
            for turn in conversation_history
        ])
        
        # 2. Holistic Analysis
        analysis_result = await scoring_engine.analyze_full_assessment(
            full_transcript=full_transcript,
            conversation_history=conversation_history
        )
        
        scores_obj = analysis_result.scores
        raw_details = analysis_result.raw_json or {}
        
        # 3. Save Scores
        # Map to DB columns + JSON details
        scores_data = {
            "assessment_id": assessment_id,
            "fluency_score": scores_obj.fluency,
            "pronunciation_score": scores_obj.pronunciation,
            "grammar_score": scores_obj.grammar,
            "vocal_confidence_score": scores_obj.vocal_confidence,
            "textual_confidence": scores_obj.textual_confidence,
            "hesitation_score": scores_obj.hesitation,
            "storytelling_score": scores_obj.storytelling,
            "vision_clarity_score": scores_obj.vision_clarity,
            "aim_clarity_score": scores_obj.aim_clarity,
            "total_score": scores_obj.total_step_score,
            "grade": "intermediate", # logic to determine grade based on score could go here
            "details": raw_details,
            "strengths": raw_details.get("strengths", []),
            "weaknesses": raw_details.get("weaknesses", []),
            "recommendations": raw_details.get("recommendations", []),
            "overall_feedback": raw_details.get("overall_review", "")
        }
        
        # Determine Grade
        ts = scores_obj.total_step_score
        if ts >= 90: scores_data["grade"] = "expert"
        elif ts >= 80: scores_data["grade"] = "advanced"
        elif ts >= 65: scores_data["grade"] = "upper_intermediate"
        elif ts >= 50: scores_data["grade"] = "intermediate"
        elif ts >= 30: scores_data["grade"] = "elementary"
        else: scores_data["grade"] = "beginner"

        # Insert into assessment_scores
        try:
           await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())
        except Exception as db_err:
             error_logger.error(f"Failed to insert scores: {db_err}")
             # We might want to re-raise or handle gracefully, but for now just log errors to update DB schema manually if needed.


        # 4. Update Assessment Status
        await asyncio.to_thread(
            lambda: client.table("assessments").update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "total_score": scores_obj.total_step_score,
                "grade": scores_data["grade"]
            }).eq("id", assessment_id).execute()
        )
        
        api_logger.info(f"🏆 [Background] Assessment {assessment_id} finalized. Score: {scores_obj.total_step_score}")
        
    except Exception as e:
        error_logger.error(f"❌ [Background] Failed to finalize assessment: {e}")


@router.post("/{response_id}/audio", response_model=AIInteractionResponse)
@limiter.limit("10/minute")
async def upload_response_audio(
    request: Request,
    response_id: str,
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
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
        response_result = await asyncio.to_thread(
            lambda: client.table("assessment_responses")
            .select("*, assessments!inner(user_id)")
            .eq("id", response_id)
            .execute()
        )
        
        if not response_result.data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        response_data = response_result.data[0]
        assessment_id = response_data["assessment_id"] # Need this for background task
        section_name = response_data.get("section", "response")
        user_id = response_data["assessments"]["user_id"]

        # 2. Fetch or Initialize Context (Replacing in-memory SessionManager)
        conversation_history = response_data.get("conversation_history") or []
        turn_count = len(conversation_history) // 2
        
        # 3. Transcribe User Audio
        audio_bytes = await audio_file.read()
        
        # Validate audio file size (max 10MB)
        MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
        if len(audio_bytes) > MAX_AUDIO_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Maximum size: {MAX_AUDIO_SIZE / 1024 / 1024}MB. Received: {len(audio_bytes) / 1024 / 1024:.2f}MB"
            )
        
        # Convert to standard WAV immediately to avoid pydub/ffmpeg issues downstream
        wav_audio_bytes = await speech_service.convert_to_wav(audio_bytes)
        
        # Stream audio clip directly to blob storage (survives container restarts)
        blob_clip_prefix = f"audio/clips/{response_id}/"
        if wav_audio_bytes:
            clip_blob_path = f"{blob_clip_prefix}clip_{turn_count}.wav"
            await storage_service.upload_audio_bytes(
                wav_audio_bytes, clip_blob_path, content_type="audio/wav"
            )
            api_logger.info(f"Saved audio clip to blob: {clip_blob_path}")
            
        transcript = await speech_service.transcribe_audio(
            wav_audio_bytes if wav_audio_bytes else audio_bytes
        )
        
        # Add to history
        conversation_history.append({"user": transcript})
        turn_count += 1
        
        api_logger.info(f"🗣️ User transcript: {transcript[:50]}...")

        # 4. Get Agent Response
        agent_result = await conversational_agent.get_response(
            user_message=transcript,
            section=section_name,
            conversation_history=conversation_history[:-1], # Exclude current turn for history context
            turn_count=turn_count
        )
        
        ai_response_text = agent_result["agent_message"]
        should_transition = agent_result["should_transition"]
        next_section = agent_result["next_section"]
        
        # Update conversation history with agent response
        conversation_history[-1]["agent"] = ai_response_text
        
        # Save updated history synchronously to DB so the next worker sees it immediately
        try:
            await asyncio.to_thread(lambda: client.table("assessment_responses").update({
                "conversation_history": conversation_history
            }).eq("id", response_id).execute())
        except Exception as e:
            error_logger.error(f"Failed to persist conversation_history to DB: {e}")
        
        # 5. Generate AI Audio (TTS)
        ai_audio_url = None
        if ai_response_text:
            api_logger.info("🔊 Generating AI voice response...")
            
            # Use new method to get bytes directly without blob upload
            ai_audio_bytes = await speech_service.synthesize_speech_bytes(ai_response_text)
            
            if ai_audio_bytes:
                # Convert to Data URI for frontend playback
                b64_audio = base64.b64encode(ai_audio_bytes).decode('utf-8')
                ai_audio_url = f"data:audio/wav;base64,{b64_audio}"
            else:
                 error_logger.error("Failed to generate AI audio bytes, but continuing with text response")
                 # We don't fail the request, allowing the frontend to at least show the text or proceed.
                 ai_audio_url = None

        # 6. Handle Transition (Merge & Finalize)
        final_audio_url = None
        interim_scores = {}
        # Ensure default next_section is set if none provided, UNLESS it's the aim section (end)
        if not next_section and section_name != "aim":
            next_section = "reading"
        
        if should_transition:
            api_logger.info(f"🏁 Section '{section_name}' complete. Signaling transition...")
            
            # PERSIST PROTOCOL: Update assessment current_section in DB immediately
            if next_section:
                try:
                    await asyncio.to_thread(lambda: client.table("assessments").update({
                        "current_section": next_section
                    }).eq("id", assessment_id).execute())
                except Exception as e:
                    error_logger.error(f"Failed to persist assessment progress: {e}")

            # --- 6a. Aggregate Full Transcript ---
            # Extract user text from history for this section
            user_full_transcript = " ".join([
                msg.get("user", "") 
                for msg in conversation_history 
                if msg.get("user")
            ])
            agent_full_transcript = " ".join([
                msg.get("agent", "") 
                for msg in conversation_history 
                if msg.get("agent")
            ])
            
            # --- 6b. Calculate Section Scores ---
            # Use empty/default scores for interim
            interim_scores = {
                "fluency": 0, "pronunciation": 0, "grammar": 0, "confidence": 0,
                "hesitation": 0, "storytelling": 0, "vision_clarity": 0,
                "total_step_score": 0, "feedback": "", "improvement_tips": []
            }
            
            update_payload = {
                "user_transcript": user_full_transcript,
                "agent_transcript": agent_full_transcript,
                "conversation_history": conversation_history
            }

            # --- 6c. Offload Merge & Upload to Background Task ---
            
            # Check if this is the end of the assessment
            is_end_of_assessment = not next_section and section_name == "aim"
            
            # COPY history for background tasks
            history_copy = list(conversation_history)
            
            background_tasks.add_task(
                process_transition_background,
                response_id,
                user_id,
                assessment_id,
                section_name,
                blob_clip_prefix,
                update_payload,
                client
            )
            
            # If finished, schedule final analysis
            if is_end_of_assessment:
                 background_tasks.add_task(
                    finalize_assessment,
                    assessment_id,
                    user_id,
                    history_copy,
                    client
                 )
                 api_logger.info("🏁 Assessment completed. Final analysis scheduled.")
            
            api_logger.info("🚀 Background task scheduled for merge/upload. Returning immediate response.")

        # 7. Return Response
        return AIInteractionResponse(
            transcript=transcript,
            ai_response_text=ai_response_text,
            ai_audio_url=ai_audio_url,
            scores=interim_scores, 
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
        result = await asyncio.to_thread(
            lambda: client.table("assessment_responses")
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
