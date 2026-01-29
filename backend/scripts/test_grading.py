import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_assessment.audio_grader import audio_grader
from app.services.supabase_client import get_supabase_service
from app.core.logging import api_logger, error_logger

async def test_grading(assessment_id: str):
    print(f"🚀 Starting manual grading test for: {assessment_id}")
    db = get_supabase_service()
    from app.config import settings
    print(f"🔧 Using API Version: {settings.AZURE_OPENAI_API_VERSION}")
    
    try:
        # 1. Run Grading
        print("🎧 Calling AudioGrader...")
        result = await audio_grader.grade_assessment(assessment_id)
        
        if result.get("error"):
            print(f"❌ Grading Error: {result['error']}")
            return

        print("✅ Analysis Complete. Processing results...")
        
        # 2. Calculate Totals
        def get_s(cat): return result.get(cat, {}).get("score", 0)
        
        total_score = (
            get_s("fluency") + get_s("pronunciation") + get_s("grammar") + 
            get_s("confidence") + get_s("storytelling") + 
            get_s("vision_clarity") + get_s("hesitation")
        )
        total_score = max(0, min(100, total_score))
        
        # Determine Grade
        grade = "beginner"
        if total_score >= 90: grade = "expert"
        elif total_score >= 80: grade = "advanced"
        elif total_score >= 65: grade = "upper_intermediate"
        elif total_score >= 50: grade = "intermediate"
        elif total_score >= 30: grade = "elementary"

        print(f"📊 Calculated Score: {total_score} ({grade})")

        # 3. Save to DB
        scores_data = {
            "assessment_id": assessment_id,
            "fluency_score": get_s("fluency"),
            "pronunciation_score": get_s("pronunciation"),
            "grammar_score": get_s("grammar"),
            "confidence_score": get_s("confidence"),
            "hesitation_score": get_s("hesitation"),
            "storytelling_score": get_s("storytelling"),
            "vision_clarity_score": get_s("vision_clarity"),
            "total_score": total_score,
            "grade": grade,
            "overall_feedback": result.get("overall_review", ""),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "recommendations": result.get("recommendations", []),
            "details": result # Store full JSON
        }
        
        print("💾 Saving scores to database...")
        client = db.get_client(use_admin=True)
        
        # Delete old scores
        await asyncio.to_thread(lambda: client.table("assessment_scores").delete().eq("assessment_id", assessment_id).execute())
        
        # Insert new scores
        await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())
        
        print("✅ Scores saved.")

        # 4. Update Assessment Status
        print("📝 Updating assessment status to 'completed'...")
        await asyncio.to_thread(lambda: client.table("assessments").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "total_score": total_score, 
            "grade": grade
        }).eq("id", assessment_id).execute())
        
        print("🏆 Assessment updated successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Assessment ID from user
    TARGET_ID = "58224367-91bd-487a-8bb4-3ec176319432"
    asyncio.run(test_grading(TARGET_ID))
