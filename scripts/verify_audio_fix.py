import sys
import os
import asyncio
from pydub import AudioSegment
import io

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

# Load env backend manually to ensure settings validation passes
def load_env(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k] = v

load_env(os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env.backend')))

from app.services.ai_assessment.azure_speech import speech_service
from app.services.audio_merger import AudioMerger

async def verify_audio_logic():
    print("🧪 Starting Audio Logic Verification...")

    # 1. Create a dummy WAV file (simulating input)
    # in reality input might be WebM, but let's test the flow
    print("   Creating dummy audio input...")
    dummy_audio = AudioSegment.silent(duration=1000) # 1 sec silent
    buf = io.BytesIO()
    dummy_audio.export(buf, format="wav")
    input_bytes = buf.getvalue()
    print(f"   Created {len(input_bytes)} bytes of input audio.")

    # 2. Test Convert to WAV (mocking the actual ffmpeg call if needed, but let's try real first)
    # We expect azure_speech.py to have convert_to_wav method after we apply fixes
    try:
        if not hasattr(speech_service, 'convert_to_wav'):
             print("❌ speech_service.convert_to_wav method NOT FOUND (Fix not applied yet?)")
             return
        
        print(f"   Testing convert_to_wav...")
        wav_bytes = speech_service.convert_to_wav(input_bytes)
        if len(wav_bytes) > 0:
            print(f"   ✅ Conversion successful: {len(wav_bytes)} bytes")
        else:
            print(f"   ❌ Conversion returned empty bytes")
            return
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        return

    # 3. Test Audio Merger
    print("   Testing Audio Merger...")
    merger = AudioMerger()
    
    # Add user clip
    merger.add_clip(wav_bytes, speaker='user')
    
    # Add AI clip (should be ignored based on new logic)
    merger.add_clip(wav_bytes, speaker='agent')
    
    print(f"   Added 2 clips (user + agent).")
    
    # Merge
    merged = merger.merge_conversation()
    
    if merged:
        print(f"   ✅ Merge successful: {len(merged)} bytes")
        # Verify duration roughly
        seg = AudioSegment.from_file(io.BytesIO(merged))
        print(f"   Merged duration: {len(seg)}ms")
        
        # We expect ~1000ms (user) + 0ms (agent ignored) + silence (if multiple user clips?)
        # Wait, if we only have 1 user clip, no silence added typically, or silence at start?
        # Logic says: for i, clip... if i < len-1 add silence.
        # If we have 1 user clip, duration should be ~1000ms (plus maybe initial silence if code does that)
        
        if len(seg) >= 1000: 
             print("   ✅ Duration looks correct.")
        else:
             print("   ⚠️ Duration too short.")
    else:
        print("   ❌ Merge returned None")

if __name__ == "__main__":
    asyncio.run(verify_audio_logic())
