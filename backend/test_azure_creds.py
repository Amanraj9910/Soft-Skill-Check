import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env.backend")

async def test_azure_speech():
    try:
        import azure.cognitiveservices.speech as speechsdk
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION")
        print(f"Testing Azure Speech (Region: {speech_region})...")
        
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # This will trigger the auth process
        result = synthesizer.speak_text_async("Test").get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Azure Speech Auth Successful")
        else:
            print(f"❌ Azure Speech Auth Failed: {result.cancellation_details.error_details}")
    except Exception as e:
        print(f"❌ Azure Speech Error: {e}")

async def test_azure_openai():
    try:
        import httpx
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_MINI", "gpt-4o-mini")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        print(f"\nTesting Azure OpenAI (Endpoint: {endpoint})...")
        
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                print("✅ Azure OpenAI Auth Successful")
            else:
                print(f"❌ Azure OpenAI Auth Failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Azure OpenAI Error: {e}")

async def main():
    await test_azure_speech()
    await test_azure_openai()

if __name__ == "__main__":
    asyncio.run(main())
