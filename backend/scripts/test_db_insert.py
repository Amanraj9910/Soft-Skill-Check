import asyncio
import sys
import os
import uuid

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service
from app.config import settings

async def test_insert():
    print(f"🔌 Connecting to database...")
    db = get_supabase_service()
    client = db.get_client(use_admin=True)
    
    assessment_id = "58224367-91bd-487a-8bb4-3ec176319432"
    
    scores_data = {
        "assessment_id": assessment_id,
        "fluency_score": 10,
        "pronunciation_score": 10,
        "grammar_score": 10,
        "confidence_score": 10,
        "hesitation_penalty": 0,
        "storytelling_score": 10,
        "vision_clarity_score": 10,
        "total_score": 60,
        "grade": "intermediate", # Testing this column
        "overall_feedback": "Test feedback",
        "strengths": ["Strength 1"],
        "weaknesses": ["Weakness 1"],
        "recommendations": ["Rec 1"],
        "details": {"test": "data"} 
    }
    
    print("💾 Attempting to insert scores...")
    try:
        # Delete old first to avoid unique constraint if any (though we usually insert, not update in this table? No, it's 1-to-1 usually)
        # Table has assessment_id as UNIQUE? Yes.
        await asyncio.to_thread(lambda: client.table("assessment_scores").delete().eq("assessment_id", assessment_id).execute())
        
        # Insert
        response = await asyncio.to_thread(lambda: client.table("assessment_scores").insert(scores_data).execute())
        print(f"✅ Insert success! Data: {response.data}")
        
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_insert())
