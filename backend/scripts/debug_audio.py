"""
Debug script to check audio URLs for a specific assessment.
"""
import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service
import httpx

async def debug_audio(assessment_id: str):
    print(f"🔍 Checking audio for assessment: {assessment_id}")
    
    db = get_supabase_service()
    client = db.get_client(use_admin=True)
    
    # Fetch responses
    result = client.table("assessment_responses").select("*").eq("assessment_id", assessment_id).order("created_at").execute()
    
    if not result.data:
        print("❌ No responses found for this assessment!")
        return
    
    print(f"📋 Found {len(result.data)} responses:")
    
    for resp in result.data:
        section = resp.get("section", "unknown")
        audio_url = resp.get("audio_url")
        
        print(f"\n--- Section: {section} ---")
        print(f"  Response ID: {resp.get('id')}")
        
        if not audio_url:
            print(f"  ❌ No audio_url in response")
            continue
        
        print(f"  📎 Audio URL: {audio_url[:100]}...")
        
        # Try to download and check
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(audio_url, timeout=30.0)
                print(f"  📥 HTTP Status: {response.status_code}")
                print(f"  📦 Content Length: {len(response.content)} bytes")
                
                if len(response.content) < 1000:
                    print(f"  ⚠️ Audio file seems too small!")
                else:
                    print(f"  ✅ Audio file looks valid")
                    
        except Exception as e:
            print(f"  ❌ Error downloading: {e}")

if __name__ == "__main__":
    TARGET_ID = "58224367-91bd-487a-8bb4-3ec176319432"
    asyncio.run(debug_audio(TARGET_ID))
