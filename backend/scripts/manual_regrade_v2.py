
import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service
from app.services.ai_assessment.scoring_engine import scoring_engine
from app.core.logging import api_logger, error_logger

async def regrade_assessment(assessment_id: str):
    print(f"🚀 Starting manual REGRADE (Scoring Engine V2) for: {assessment_id}")
    db = get_supabase_service()
    
    try:
        # 1. Fetch Responses to reconstruct transcript
        print("📥 Fetching assessment responses...")
        client = db.get_client(use_admin=True)
        resp_result = await asyncio.to_thread(
             lambda: client.table("assessment_responses")
             .select("*")
             .eq("assessment_id", assessment_id)
             .order("created_at")
             .execute()
        )
        
        responses = resp_result.data if resp_result.data else []
        if not responses:
            print("❌ No responses found for this assessment.")
            return

        # 2. Reconstruct History & Transcript
        full_transcript_parts = []
        conversation_history = []
        
        for r in responses:
            u_text = r.get("user_transcript") or ""
            a_text = r.get("agent_transcript") or "" # If available
            
            if u_text:
                full_transcript_parts.append(f"User: {u_text}")
                conversation_history.append({"role": "user", "content": u_text})
            if a_text:
                full_transcript_parts.append(f"Agent: {a_text}")
                conversation_history.append({"role": "assistant", "content": a_text})
                
        full_transcript = "\n".join(full_transcript_parts)
        print(f"📄 Reconstructed Transcript Length: {len(full_transcript)} chars")
        
        # 3. Call Scoring Engine
        print("🧠 Calling ScoringEngine...")
        analysis_result = await scoring_engine.analyze_full_assessment(
            full_transcript=full_transcript,
            conversation_history=conversation_history
        )
        
        scores_obj = analysis_result.scores
        raw_details = analysis_result.raw_json or {}
        
        # 4. Save Scores (Using the exact logic from responses.py)
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
            "grade": "intermediate", 
            "details": raw_details,
            "strengths": raw_details.get("strengths", []),
            "weaknesses": raw_details.get("weaknesses", []),
            "recommendations": raw_details.get("recommendations", []),
            "overall_feedback": raw_details.get("overall_review", "")
        }
        
        # Calculate grade
        ts = scores_obj.total_step_score
        if ts >= 90: scores_data["grade"] = "expert"
        elif ts >= 80: scores_data["grade"] = "advanced"
        elif ts >= 65: scores_data["grade"] = "upper_intermediate"
        elif ts >= 50: scores_data["grade"] = "intermediate"
        elif ts >= 30: scores_data["grade"] = "elementary"
        else: scores_data["grade"] = "beginner"

        print("📊 New Scores Calculated:")
        print(json.dumps({k:v for k,v in scores_data.items() if k != 'details'}, indent=2))

        # 5. DB Update
        print("💾 Saving to DB (assessment_scores)...")
        # Delete old scores first to avoid conflicts if ID is unique or multiple entries issue
        await asyncio.to_thread(lambda: client.table("assessment_scores").delete().eq("assessment_id", assessment_id).execute())
        
        # Insert
        await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())
        print("✅ Scores inserted.")
        
        # Update Assessment Status
        print("📝 Updating assessment status...")
        await asyncio.to_thread(
            lambda: client.table("assessments").update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "total_score": scores_obj.total_step_score,
                "grade": scores_data["grade"]
            }).eq("id", assessment_id).execute()
        )
        print("🏆 Regrade Complete.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    TARGET_ID = "efb35a60-072c-4298-8919-3e59f717c1ca"
    asyncio.run(regrade_assessment(TARGET_ID))
