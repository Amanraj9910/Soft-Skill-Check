
import sys
import os

try:
    import imageio_ffmpeg
    print(f"imageio_ffmpeg exe: {imageio_ffmpeg.get_ffmpeg_exe()}")
except ImportError:
    print("imageio_ffmpeg not installed")
except Exception as e:
    print(f"Error getting ffmpeg exe: {e}")
