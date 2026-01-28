import asyncio
import logging
from app.services.supabase_client import get_supabase_service

# Configure logging to see our retry logs if they happen (unlikely on sunny day)
logging.basicConfig(level=logging.INFO)

async def main():
    print("Initializing SupabaseService...")
    service = get_supabase_service()
    
    assessment_id = "ba659dfa-e5f1-4e34-bc45-ea59b5c0e814"
    print(f"Fetching assessment {assessment_id} using service...")
    
    try:
        assessment = await service.get_assessment(assessment_id)
        if assessment:
            print(f"✅ Successfully fetched assessment: {assessment.get('id')}")
        else:
            print("❌ Assessment not found (but no error raised)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
