import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(".env.backend")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env.backend")
    exit(1)

async def main():
    print(f"Connecting to Supabase at {url}")
    supabase = create_client(url, key)
    
    assessment_id = "ba659dfa-e5f1-4e34-bc45-ea59b5c0e814"
    
    print(f"Fetching assessment {assessment_id}...")
    try:
        # Replicating the call layout from get_assessment in supabase_client.py
        # It runs in a thread because the client is sync
        response = await asyncio.to_thread(
            lambda: supabase.table("assessments").select("*").eq("id", assessment_id).execute()
        )
        print("Success!")
        print(response.data)
    except Exception as e:
        print(f"Error fetching assessment: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
