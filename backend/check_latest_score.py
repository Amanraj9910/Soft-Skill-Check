import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service

async def check_score():
    print(f"🔌 Connecting to database...")
    db = get_supabase_service()
    client = db.get_client(use_admin=True)
    
    assessment_id = "58224367-91bd-487a-8bb4-3ec176319432"
    
    response = await asyncio.to_thread(lambda: client.table("assessment_scores")
        .select("*")
        .eq("assessment_id", assessment_id)
        .execute())
    
    if response.data:
        score = response.data[0]
        print(f"✅ Found score for assessment {assessment_id}")
        print(f"Hesitation Penalty: {score.get('hesitation_penalty')}")
        print(f"Total Score: {score.get('total_score')}")
        print(f"Grade: {score.get('grade')}")
        if score.get('hesitation_penalty') <= 0:
             print("SUCCESS: Hesitation is negative or zero.")
        else:
             print("FAILURE: Hesitation is positive!")
    else:
        print("❌ No score found.")

if __name__ == "__main__":
    asyncio.run(check_score())
