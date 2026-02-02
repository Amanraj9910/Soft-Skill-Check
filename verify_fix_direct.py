
import os
import sys

# Mock settings
class MockSettings:
    AZURE_SPEECH_KEY = "dummy"
    AZURE_SPEECH_REGION = "dummy"
    AZURE_SPEECH_LANGUAGE = "en-US"

sys.modules['app.config'] = type('config', (), {'settings': MockSettings()})

from app.services.ai_assessment.azure_speech import AzureSpeechService

def test_conversion():
    service = AzureSpeechService()
    
    # Test conversion using audio bytes
    # Create input file
    import wave
    import struct
    temp_wav = "test_input_verify.wav"
    
    try:
        with wave.open(temp_wav, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            f.writeframes(struct.pack('h', 0) * 16000) # 1 sec silence
            
        with open(temp_wav, 'rb') as f:
            audio_bytes = f.read()
            
        print(f"Testing conversion of {len(audio_bytes)} bytes...")
        
        # This calls verify_fix which uses azure_speech.py
        # Now azure_speech.py uses subprocess.run([exe, ...])
        
        converted = service.convert_to_wav(audio_bytes)
        
        if converted and len(converted) > 0:
            print(f"Conversion returned {len(converted)} bytes.")
            # Verify it's a valid wav
            if converted.startswith(b'RIFF'):
                print("VERIFICATION SUCCESS: Output appears to be a valid WAV file.")
            else:
                print("VERIFICATION WARNING: Output does not start with RIFF header.")
        else:
            print("Conversion returned empty or None")

    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    test_conversion()
