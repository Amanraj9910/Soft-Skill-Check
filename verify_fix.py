

import sys

# Mock config
class MockSettings:
    AZURE_SPEECH_KEY = "dummy"
    AZURE_SPEECH_REGION = "dummy"
    AZURE_SPEECH_LANGUAGE = "en-US"

sys.modules['app.config'] = type('config', (), {'settings': MockSettings()})

# Mock pydub if it fails to import (e.g. on Python 3.13+)
try:
    import pydub
except ImportError:
    print("Mocking pydub for verification due to ImportError")
    from unittest.mock import MagicMock
    pydub = MagicMock()
    sys.modules["pydub"] = pydub
    pydub.AudioSegment = MagicMock()
    # Ensure we can set attributes on AudioSegment class
    pydub.AudioSegment.converter = "ffmpeg" 

from app.services.ai_assessment.azure_speech import AzureSpeechService

def test_conversion():
    service = AzureSpeechService()
    
    # We want to verify that calling convert_to_wav sets AudioSegment.converter
    # and calls export.
    
    # Mock imageio_ffmpeg to returning a known path
    import imageio_ffmpeg
    original_get_exe = imageio_ffmpeg.get_ffmpeg_exe
    imageio_ffmpeg.get_ffmpeg_exe = lambda: "mock_ffmpeg_path"
    
    try:
        # If we are mocking pydub, we need to make sure the import inside the function works.
        # It does "from pydub import AudioSegment"
        # If sys.modules["pydub"] is set, it should work.
        
        # If real pydub is loaded, we might actually try to run things.
        # But if pydub is broken (ImportError), we mocked it.
        
        # We need to spy on AudioSegment
        from pydub import AudioSegment
        
        # Run conversion
        service.convert_to_wav(b"dummy_bytes")
        
        print(f"AudioSegment.converter set to: {AudioSegment.converter}")
        
        if AudioSegment.converter == "mock_ffmpeg_path":
            print("VERIFICATION SUCCESS: AudioSegment.converter was set correctly.")
        else:
            print(f"VERIFICATION FAILED: Converter is {AudioSegment.converter}")

    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        imageio_ffmpeg.get_ffmpeg_exe = original_get_exe

if __name__ == "__main__":
    test_conversion()

