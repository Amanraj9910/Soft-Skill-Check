
import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service

async def verify_scores(assessment_id: str):
    db = get_supabase_service()
    client = db.get_client(use_admin=True)
    
    print(f"Verifying scores for: {assessment_id}")
    
    response = await asyncio.to_thread(
         lambda: client.table("assessment_scores")
         .select("*")
         .eq("assessment_id", assessment_id)
         .execute()
    )
    
    if response.data:
        score = response.data[0]
        # Dump to JSON file for safe reading
        with open("score_report.json", "w", encoding="utf-8") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Score saved to score_report.json")
    else:
        print("No score record found.")

if __name__ == "__main__":
    TARGET_ID = "58224367-91bd-487a-8bb4-3ec176319432"
    asyncio.run(verify_scores(TARGET_ID))
