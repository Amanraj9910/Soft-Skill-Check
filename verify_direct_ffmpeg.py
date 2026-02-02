
import subprocess
import imageio_ffmpeg
import os
import wave
import struct

def test_conversion():
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"Using ffmpeg exe: {ffmpeg_exe}")
        
        # Create a dummy WebM file (or whatever format we want to test)
        # Actually create a WAV file and rename it to .webm to trick it, 
        # or just create a valid small WAV file and try convert WAV->WAV.
        # FFMPEG handles both.
        
        temp_in_path = "test_input.wav"
        temp_out_path = "test_output.wav"
        
        # Create input file
        with wave.open(temp_in_path, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(16000)
            f.writeframes(struct.pack('h', 0) * 16000) # 1 sec silence
            
        print(f"Input file created: {temp_in_path}")
        
        # Run conversion using subprocess
        cmd = [ffmpeg_exe, "-i", temp_in_path, "-y", temp_out_path]
        print(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            print("Conversion successful!")
            if os.path.exists(temp_out_path):
                size = os.path.getsize(temp_out_path)
                print(f"Output file size: {size} bytes")
            else:
                print("Output file missing!")
        else:
            print(f"Conversion failed with return code {result.returncode}")
            print(f"Stderr: {result.stderr.decode()}")

    except Exception as e:
        print(f"Test failed with exception: {e}")
    finally:
        if os.path.exists("test_input.wav"):
            os.remove("test_input.wav")
        if os.path.exists("test_output.wav"):
            os.remove("test_output.wav")

if __name__ == "__main__":
    test_conversion()
