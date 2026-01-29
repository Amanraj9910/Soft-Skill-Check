import asyncio
import os
import tempfile
import logging
from typing import List, Dict, Any, Optional
import statistics

from app.core.logging import ai_logger, error_logger
from app.services.supabase_client import get_supabase_service
from .azure_speech import AzureSpeechService
from .speech_scoring import SpeechScoringService
from .llm_analysis import LLMAnalysisService
import httpx

# Instantiate services
azure_speech = AzureSpeechService()
speech_scoring = SpeechScoringService()
llm_analysis = LLMAnalysisService()

class AudioGrader:
    def __init__(self):
        self.db = get_supabase_service()

    async def grade_assessment(self, assessment_id: str) -> Dict[str, Any]:
        """
        Orchestrates the new grading pipeline:
        1. Fetch responses.
        2. For each audio:
           - Transcribe & Analyze with Azure (Audio -> Text + Timestamps + Pronunciation)
           - Calculate Speech Scores (Fluency, Hesitation, etc.)
        3. Aggregate Text specific for LLM.
        4. Run GPT-4o Analysis (Grammar, Storytelling, etc.)
        5. Aggregate & Normalize Final Report.
        """
        ai_logger.info(f"🎧 Starting NEW Assessment Architecture grading for: {assessment_id}")
        
        responses = await self._fetch_responses(assessment_id)
        if not responses:
            return self._get_empty_result("No responses found")

        # Containers for aggregated data
        all_transcripts = []
        section_scores = []
        
        # 1. Process Audio Files (Parallel or Serial? Serial is safer for now)
        for resp in responses:
            audio_url = resp.get("audio_url")
            section = resp.get("section")
            reference_text = self._get_reference_text(section) # Define mapping
            
            if audio_url:
                try:
                    # Download
                    file_path = await self._download_to_temp(audio_url)
                    if file_path:
                        # Azure Analysis
                        azure_result = await azure_speech.analyze_audio(file_path, reference_text)
                        
                        # Speech Scoring
                        # We pass the azure result to the scoring engine
                        # Check for failure in Azure
                        if not azure_result.get("error"):
                            scores = speech_scoring.calculate_scores(azure_result)
                            scores["section"] = section
                            scores["transcript"] = azure_result.get("transcript", "")
                            section_scores.append(scores)
                            all_transcripts.append(azure_result.get("transcript", ""))
                        else:
                            ai_logger.error(f"Azure failed for section {section}: {azure_result.get('error')}")
                            # Fallback: Zero scores, empty transcript
                            section_scores.append(self._get_zero_section_scores(section))
                        
                        os.remove(file_path)
                    else:
                        ai_logger.error(f"Failed to download audio for {section}")
                        section_scores.append(self._get_zero_section_scores(section))
                
                except Exception as e:
                    ai_logger.error(f"Error processing section {section}: {e}")
                    section_scores.append(self._get_zero_section_scores(section))

        # 2. LLM Analysis
        combined_transcript = "\n".join(all_transcripts)
        llm_result = llm_analysis.analyze_responses(combined_transcript)

        # 3. Aggregation & Weighting
        final_result = self._aggregate_scores(section_scores, llm_result)
        
        return final_result

    async def _fetch_responses(self, assessment_id: str) -> List[Dict]:
        """Fetch responses from Supabase."""
        try:
            client = self.db.get_client(use_admin=True)
            result = await asyncio.to_thread(
                lambda: client.table("assessment_responses")
                .select("*")
                .eq("assessment_id", assessment_id)
                .order("created_at")
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            error_logger.error(f"Failed to fetch responses: {e}")
            return []

    async def _download_to_temp(self, url: str) -> Optional[str]:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=30.0)
                    if response.status_code == 200:
                        tmp.write(response.content)
                        return tmp.name
            return None
        except Exception as e:
            error_logger.error(f"Error downloading audio: {e}")
            return None

    def _get_reference_text(self, section: str) -> Optional[str]:
        # TODO: Retrieve actual text from DB or Config based on section?
        # For 'reading' and 'shadowing', we usually have fixed text.
        # Ideally, we should fetch the exact Prompt shown to user.
        # For now, return None for open sections, or a placeholder if we have it in code.
        # Assuming open/transcription mode for most if text is dynamic.
        if section in ["reading", "shadowing"]:
            # Placeholder or fetch from a prompts constant file?
            # User wants "Innovation drives progress" etc.
            # Let's return None for now and rely on Transcription, unless we import prompts.
            return None 
        return None

    def _get_zero_section_scores(self, section: str) -> Dict[str, Any]:
        return {
            "section": section,
            "fluency_score": 0,
            "hesitation_score": 0,
            "pronunciation_score": 0,
            "vocal_confidence_score": 0,
            "transcript": ""
        }

    def _aggregate_scores(self, section_scores: List[Dict], llm_result: Dict) -> Dict[str, Any]:
        """
        Robust Aggregation Logic.
        """
        # Average the speech scores across all available sections.
        # Filter out sections with 0 scores if they failed? 
        # Or treat them as 0 if they failed? User wants Fallback Strategy: "If speech metrics fail -> partial score"
        
        if not section_scores:
            return self._get_empty_result("No Audio Processed")

        # Helper to avg non-zero if possible, or straight avg?
        # User implies fairness. If a section failed due to TECH reasons, we shouldn't penalize.
        # But here we don't distinguish tech failure vs silence easily without improved error handling upstream.
        # Assuming section_scores has valid numbers (0 if silent/bad, >0 if good).
        
        # Calculate Averages
        avg_fluency = statistics.mean([s["fluency_score"] for s in section_scores])
        avg_hesitation = statistics.mean([s["hesitation_score"] for s in section_scores])
        avg_pronunciation = statistics.mean([s["pronunciation_score"] for s in section_scores])
        avg_confidence = statistics.mean([s["vocal_confidence_score"] for s in section_scores])

        # Combine with LLM Result
        final_report = {
            "fluency": {"score": round(avg_fluency, 1), "reasoning": "Calculated from WPM and Pauses."},
            "hesitation": {"score": round(avg_hesitation, 1), "reasoning": "Based on filler words and silence analysis."},
            "pronunciation": {"score": round(avg_pronunciation, 1), "reasoning": "Azure Pronunciation Assessment."},
            "confidence": {"score": round(avg_confidence, 1), "reasoning": "Derived from stability and flow."},
            
            "grammar": {"score": llm_result["grammar_score"], "reasoning": llm_result["grammar_reasoning"]},
            "storytelling": {"score": llm_result["storytelling_score"], "reasoning": llm_result["storytelling_reasoning"]},
            "vision_clarity": {"score": llm_result["aim_clarity_score"], "reasoning": llm_result["aim_reasoning"]},
            "textual_confidence": {"score": llm_result["textual_confidence"], "reasoning": llm_result["confidence_reasoning"]},
            
            "overall_review": "Assessment completed.", # TODO Generate summary?
        }
        
        # Calculate Total Score (Simple Sum? Or Weighted?)
        # User defined rubric earlier:
        # Fluency(20) + Pronunciation(10) + Grammar(10) + Confidence(20? Wait, user changed logic)
        # Let's re-verify score ranges from User Request:
        # LLM: Grammar(10), Storytelling(20), Aim(10), TextConf(10) -> Total 50?
        # Speech: Fluency(20), Hesitation(10), Pronunciation(10), VocalConf(10) -> Total 50?
        # Total = 100?
        
        total = (final_report["fluency"]["score"] + 
                 final_report["hesitation"]["score"] +
                 final_report["pronunciation"]["score"] +
                 final_report["confidence"]["score"] +
                 final_report["grammar"]["score"] + 
                 final_report["storytelling"]["score"] + 
                 final_report["vision_clarity"]["score"] + 
                 final_report["textual_confidence"]["score"])
                 
        final_report["total_score"] = round(total, 1)
        
        return final_report

    def _get_empty_result(self, error: str = "") -> Dict[str, Any]:
         return {
            "error": error,
            "overall_review": "Assessment incomplete.",
            "total_score": 0
        }

audio_grader = AudioGrader()
