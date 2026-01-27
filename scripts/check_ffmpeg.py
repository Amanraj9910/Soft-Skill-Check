import sys
import os

try:
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"ffmpeg exe path: {exe}")
    print(f"exists: {os.path.exists(exe)}")
    
    import subprocess
    subprocess.run([exe, "-version"])
    print("✅ subprocess run successful")
except ImportError:
    print("❌ imageio_ffmpeg not installed")
except Exception as e:
    print(f"❌ Error: {e}")
