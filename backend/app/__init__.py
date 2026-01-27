"""
App package initialization.
"""
import os
import imageio_ffmpeg
from pydub import AudioSegment

__version__ = "1.0.0"

# Get ffmpeg path
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_path)

# Add to PATH (helps subprocess calls)
if ffmpeg_dir not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + ffmpeg_dir

# Configure pydub to use the installed ffmpeg binary
AudioSegment.converter = ffmpeg_path
