import asyncio
from app.services.supabase_client import get_supabase_service

async def debug_scores():
    try:
        db = get_supabase_service()
        client = db.get_client(use_admin=True)
        
        print("Fetching COMPLETED assessments...")
        assessments = client.table("assessments").select("id, status, created_at").eq("status", "completed").order("created_at", desc=True).limit(5).execute()
        
        if not assessments.data:
            print("No completed assessments found.")
            return

        for assess in assessments.data:
            print(f"\nAssessment: {assess['id']} ({assess['status']})")
            
            # Fetch scores
            scores = client.table("assessment_scores").select("*").eq("assessment_id", assess['id']).execute()
            if scores.data:
                print("  Scores found:")
                print(f"  {scores.data[0]}")
            else:
                print("  No scores record found.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_scores())
