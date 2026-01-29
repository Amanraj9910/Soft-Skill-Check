"""
Test Azure Speech with a downloaded audio file.
"""
import asyncio
import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.supabase_client import get_supabase_service
from app.services.ai_assessment.azure_speech import AzureSpeechService
import httpx

async def test_azure_speech():
    print("🔍 Testing Azure Speech with real audio...")
    
    db = get_supabase_service()
    client = db.get_client(use_admin=True)
    azure_speech = AzureSpeechService()
    
    # Get first response with audio
    result = client.table("assessment_responses").select("section, audio_url").eq("assessment_id", "58224367-91bd-487a-8bb4-3ec176319432").limit(1).execute()
    
    if not result.data or not result.data[0].get("audio_url"):
        print("❌ No audio URL found")
        return
    
    section = result.data[0]["section"]
    audio_url = result.data[0]["audio_url"]
    
    print(f"📂 Section: {section}")
    print(f"📎 URL: {audio_url[:80]}...")
    
    # Download audio
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(audio_url, timeout=30.0)
        print(f"📥 Downloaded: {len(response.content)} bytes")
        print(f"📄 Content-Type: {response.headers.get('content-type')}")
        
        # Check first bytes for WAV header
        header = response.content[:12]
        print(f"🔎 File header: {header}")
        
        if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
            print("✅ Valid WAV file detected")
        else:
            print("⚠️ Not a standard WAV file!")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        print(f"💾 Saved to: {tmp_path}")
        
        # Try Azure Speech
        print("\n🎙️ Calling Azure Speech...")
        result = await azure_speech.analyze_audio(tmp_path, reference_text=None)
        
        print(f"\n📊 Result:")
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
        else:
            print(f"📝 Transcript: {result.get('transcript', '')[:200]}...")
            print(f"🎯 Confidence: {result.get('confidence')}")
            print(f"📊 Words: {len(result.get('words', []))} words")
        
        # Cleanup
        os.remove(tmp_path)

if __name__ == "__main__":
    asyncio.run(test_azure_speech())
