import asyncio
import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load env directly to check if they are picked up
load_dotenv(".env.backend")

KEY = os.getenv("AZURE_SPEECH_KEY")
REGION = os.getenv("AZURE_SPEECH_REGION")
VOICE = os.getenv("AZURE_TTS_VOICE_NAME", "en-US-JennyNeural")

print(f"Loaded Config: Region={REGION}, Voice={VOICE}, KeyLength={len(KEY) if KEY else 0}")

def test_tts():
    if not KEY or not REGION:
        print("❌ Missing Azure Speech credentials in .env.backend")
        return

    print("Attempting TTS synthesis...")
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=REGION)
    speech_config.speech_synthesis_voice_name = VOICE
    
    # Null output to avoid playing audio on server
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False, filename="debug_tts_output.wav")
    
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    result = synthesizer.speak_text_async("Hello, this is a test of the Azure Speech service.").get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("✅ TTS Success! Audio generated.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"❌ TTS Failed: {cancellation_details.reason}")
        if cancellation_details.error_details:
            print(f"❌ Error Details: {cancellation_details.error_details}")
    else:
        print(f"❌ TTS Failed with unknown reason: {result.reason}")

if __name__ == "__main__":
    test_tts()
