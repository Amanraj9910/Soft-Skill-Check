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


from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks

# ... imports ...

# Define background task function
async def process_transition_background(
    response_id: str,
    user_id: str,
    assessment_id: str,
    section: str,
    session: dict,
    update_payload: dict,
    client: SupabaseService
):
    try:
        api_logger.info(f"⏳ [Background] Processing transition for {section}...")
        
        # 1. Merge Conversation
        merged_audio = session['audio_merger'].merge_conversation()
        
        if merged_audio:
            # Generate filename
            try:
                # We can't reuse client here if it's not thread safe, but for now we passed the service or client.
                # Ideally create new client or use passed one if robust.
                # Let's re-fetch profile to be safe or just use ID
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"user_{user_id}_{section}_{timestamp}.wav"
            except:
                filename = f"conversation_{response_id}_{datetime.now().timestamp()}.wav"
            
            # 2. Upload to Blob
            blob_name = storage_service.upload_file(merged_audio, filename=filename, content_type="audio/wav")
            final_audio_url = storage_service.generate_sas_url(blob_name)
            
            update_payload["audio_url"] = final_audio_url
            
        # 3. Update DB with Transcript & Audio URL
        # We need to run this in asyncio loop since this function is async
        # Supabase client is synchronous or async depending on usage. 
        # Our `client` from dependency `db.get_client` is synchronous `supabase.Client`.
        # So we wrap in to_thread if needed, but here we can just call it if it's thread-safe enough or just run it.
        # However, `process_transition_background` being async means we should await async calls.
        # But `client.table(...).execute()` is synchronous in the python supabase library usually, unless using async client.
        # The previous code used `await client...` which implies we might need to wrap it.
        # Wait, the previous code was: `client.table(...).execute()` (Sync) inside a route?
        # Actually looking at previous code: `response_result = client.table(...).execute()` -> Sync
        # But `supabase_client.py` uses `asyncio.to_thread`.
        # Let's use `asyncio.to_thread` here too for safety.
        
        import asyncio
        await asyncio.to_thread(lambda: client.table("assessment_responses").update(update_payload).eq("id", response_id).execute())
        
        api_logger.info(f"✅ [Background] Transition processing complete for {section}")
        
    except Exception as e:
        error_logger.error(f"❌ [Background] Failed to process transition: {e}")
    finally:
        # 4. Clear Session
        # Only clear if NO final analysis is pending? 
        # Actually session_manager.clear_session removes it. 
        # If we need history for final analysis, we must have passed it already.
        session_manager.clear_session(response_id)


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
            "confidence_score": scores_obj.confidence,
            "hesitation_penalty": scores_obj.hesitation,
            "storytelling_score": scores_obj.storytelling,
            "vision_clarity_score": scores_obj.vision_clarity,
            "total_score": scores_obj.total_step_score,
            "grade": "intermediate", # logic to determine grade based on score could go here
            "ai_classification": raw_details, # Store detailed reasoning/breakdown here
            "details": raw_details # Redundant backup if column names vary
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
        # We try/except specific columns if 'details' or 'ai_classification' fails
        # But for now we try to push all.
        try:
           await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())
        except Exception as db_err:
             # Fallback if 'details' column doesn't exist, try 'ai_classification' only
             error_logger.warning(f"Failed to insert scores with current schema, retrying without redundant field: {db_err}")
             if "details" in scores_data: del scores_data["details"]
             await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())

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
async def upload_response_audio(
    response_id: str,
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None, # Add BackgroundTasks dependency
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
        assessment_id = response_data["assessment_id"] # Need this for background task
        section_name = response_data.get("section", "response")
        user_id = response_data["assessments"]["user_id"]

        # 2. Get/Create Session
        session = session_manager.get_session(response_id)
        
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
        wav_audio_bytes = speech_service.convert_to_wav(audio_bytes)
        
        # Add user audio to session (ONLY user audio is merged now, as requested)
        if wav_audio_bytes:
            session['audio_merger'].add_clip(wav_audio_bytes, speaker='user')
            
        transcript = speech_service.transcribe_audio(wav_audio_bytes if wav_audio_bytes else audio_bytes)
        
        # Add to history
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
            
            # Update session to mark transition
            if session_manager.has_session(response_id):
                session_manager.update_session(response_id, transition=True, next_section=next_section)

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
                for msg in session['conversation_history'] 
                if msg.get("user")
            ])
            agent_full_transcript = " ".join([
                msg.get("agent", "") 
                for msg in session['conversation_history'] 
                if msg.get("agent")
            ])
            
            # --- 6b. Calculate Section Scores ---
            try:
                api_logger.info("📊 Calculating section scores...")
                analysis_result = scoring_engine.analyze_response(
                    transcript=user_full_transcript,
                    question=section_name,
                    context={"history": session['conversation_history']}
                )
                
                scores_obj = analysis_result.scores
                
                # Map to DB fields
                update_payload = {
                    "user_transcript": user_full_transcript,
                    "agent_transcript": agent_full_transcript,
                    # Scores
                    "fluency_score": scores_obj.fluency,
                    "pronunciation_score": scores_obj.pronunciation,
                    "completeness_score": scores_obj.storytelling, # Mapping storytelling as completeness for now, or calculate separate
                    # Detailed fields if available in `analysis_result` or calculated elsewhere
                    # For now, we populate what we have from the scoring engine rubric
                    "pronunciation_score": scores_obj.pronunciation,
                    "fluency_score": scores_obj.fluency,
                    "ai_classification": scores_obj.dict(), # Save full scores object for report generation
                    "conversation_history": session['conversation_history'] # Save history
                }
                
                interim_scores = scores_obj.dict()
                
            except Exception as score_err:
                error_logger.error(f"Failed to calculate section scores: {score_err}")
                # Don't fail the request, just log
                update_payload = {
                     "user_transcript": user_full_transcript,
                     "agent_transcript": agent_full_transcript,
                     "conversation_history": session['conversation_history']
                }

            # --- 6c. Offload Merge & Upload to Background Task ---
            
            # Check if this is the end of the assessment
            is_end_of_assessment = not next_section and section_name == "aim"
            # Or if agent explicitly signaled end by returning None for next_section
            # But we had a line ensuring next_section="reading" if none. We must fix that logic upstream or here.
            
            # COPY history for background tasks (to avoid race conditions with session clearing)
            history_copy = list(session['conversation_history'])
            
            background_tasks.add_task(
                process_transition_background,
                response_id,
                user_id,
                assessment_id,
                section_name,
                session, # Pass session reference (logic inside clears it)
                update_payload,
                client
            )
            
            # If finished, schedule final analysis
            if is_end_of_assessment or (not next_section and section_name == "aim"):
                 background_tasks.add_task(
                    finalize_assessment,
                    assessment_id,
                    user_id,
                    history_copy,
                    client
                 )
                 api_logger.info("🏁 Assessment completed. Final analysis scheduled.")

            # Note: We do NOT clear session here immediately if we pass the session object to background task.
            # The background task will clear it.
            
            # OR better: pass the *data* from session needed for merging.
            # `session['audio_merger']` IS the data.
            # `session['conversation_history']` is already in payload.
            # The background task clears the session from manager using response_id.
            
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
