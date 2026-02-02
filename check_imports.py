
import sys
import traceback
import os

print(f"Python executable: {sys.executable}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not Set')}")

try:
    import imageio_ffmpeg
    print(f"imageio_ffmpeg imported: {imageio_ffmpeg.__file__}")
    print(f"ffmpeg path: {imageio_ffmpeg.get_ffmpeg_exe()}")
except ImportError:
    print("Failed to import imageio_ffmpeg")
    traceback.print_exc()

try:
    import pydub
    from pydub import AudioSegment
    print(f"pydub imported: {pydub.__file__}")
except ImportError:
    print("Failed to import pydub")
    traceback.print_exc()
