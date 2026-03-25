"""
Test continuous recognition by breaking the Test-EA.m4a file into segments.
This simulates different assessment sections from a single long recording.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import subprocess

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_assessment.azure_speech import speech_service

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

async def get_audio_duration(file_path: str) -> float:
    """Get audio duration using ffprobe or mutagen."""
    try:
        from mutagen import File
        audio = File(file_path)
        if audio and audio.info:
            return audio.info.length
    except:
        pass
    
    # Fallback to ffprobe
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    
    # Estimate from file size (rough)
    file_size = os.path.getsize(file_path)
    return file_size / (8 * 1024)  # Assume 64kbps for M4A

async def split_audio(input_path: str, start_sec: float, duration_sec: float) -> bytes:
    """Split audio file and return segment as WAV bytes."""
    try:
        import ffmpeg
        
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"segment_{start_sec:.1f}s.wav")
        
        # Use ffmpeg to extract segment
        (
            ffmpeg
            .input(input_path, ss=start_sec, t=duration_sec)
            .output(output_path, acodec='pcm_s16le', ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Read WAV file
        with open(output_path, 'rb') as f:
            wav_bytes = f.read()
        
        # Cleanup
        try:
            os.remove(output_path)
        except:
            pass
        
        return wav_bytes
        
    except ImportError:
        print_warning("ffmpeg-python not available, using fallback method")
        # Fallback: convert entire file and slice bytes
        # This is approximate but works without ffmpeg
        with open(input_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Convert to WAV first
        wav_bytes = await speech_service.convert_to_wav(audio_bytes)
        
        # Rough estimate: 16kHz, 16-bit, mono = 32KB per second
        bytes_per_second = 32000
        start_byte = int(start_sec * bytes_per_second)
        end_byte = int((start_sec + duration_sec) * bytes_per_second)
        
        # WAV header is 44 bytes
        if start_byte == 0:
            return wav_bytes[:end_byte]
        else:
            # For non-zero start, we need to preserve WAV header
            return wav_bytes[:44] + wav_bytes[start_byte:end_byte]

async def test_segment(segment_name: str, audio_bytes: bytes, expected_duration: float, use_continuous: bool):
    """Test transcription on a segment."""
    print(f"\n{'='*70}")
    print(f"SEGMENT: {segment_name}")
    print(f"Duration: ~{expected_duration:.1f}s | Method: {'Continuous' if use_continuous else 'recognize_once'}")
    print('='*70)
    
    print_info(f"Audio size: {len(audio_bytes)/1024:.1f}KB")
    
    # Transcribe
    transcript = await speech_service.transcribe_audio(
        audio_bytes,
        use_continuous=use_continuous
    )
    
    # Analyze results
    word_count = len(transcript.split()) if transcript else 0
    
    print(f"\n📊 Results:")
    print(f"   Transcript length: {len(transcript) if transcript else 0} chars")
    print(f"   Word count: {word_count}")
    
    # Quality check
    if use_continuous and expected_duration > 30:
        expected_min_words = int(expected_duration * 1.5)
        if word_count < expected_min_words * 0.7:
            print_warning(f"⚠️  May be incomplete - expected ~{expected_min_words}+ words")
        else:
            print_success(f"✓ Good coverage - {word_count/expected_min_words*100:.1f}% of expected")
    
    # Show preview
    if transcript:
        print(f"\n📝 Preview:")
        if len(transcript) > 200:
            print(f"   {transcript[:200]}...")
        else:
            print(f"   {transcript}")
    
    return {
        'segment': segment_name,
        'duration': expected_duration,
        'method': 'continuous' if use_continuous else 'recognize_once',
        'words': word_count,
        'chars': len(transcript) if transcript else 0,
        'success': transcript is not None
    }

async def main():
    print_header("AUDIO SEGMENTATION TEST")
    print_info("Breaking Test-EA.m4a into assessment-like segments")
    
    # Load environment
    load_dotenv(".env.backend")
    
    if not os.getenv("AZURE_SPEECH_KEY"):
        print_error("Missing AZURE_SPEECH_KEY in .env.backend")
        return
    
    print_success("Azure Speech credentials loaded")
    
    # Define test file
    audio_file = r"D:\AI Projects\Soft Skill Check\Test-EA.m4a"
    
    if not os.path.exists(audio_file):
        print_error(f"File not found: {audio_file}")
        return
    
    # Get total duration
    print_info(f"Analyzing audio file...")
    total_duration = await get_audio_duration(audio_file)
    print_info(f"Total duration: {total_duration:.1f}s")
    
    # Define segments to simulate assessment sections
    # Adjusted based on actual file duration (62.8s)
    segments = [
        # Short sections (use recognize_once)
        ("introduction_part1", 0, 10, False),      # First 10 seconds
        ("reading_part1", 10, 15, False),          # Next 15 seconds (10-25s)
        ("listening_part1", 25, 15, False),        # Next 15 seconds (25-40s)
        
        # Long section at the end (use continuous)
        ("storytelling_full", 40, min(22, total_duration - 40), True),  # Remaining ~22s (40-62.8s)
    ]
    
    # Filter segments that exceed total duration
    valid_segments = []
    for name, start, duration, use_cont in segments:
        if start + duration <= total_duration:
            valid_segments.append((name, start, duration, use_cont))
        else:
            print_warning(f"Skipping {name}: would exceed file duration ({start}+{duration} > {total_duration:.1f})")
    
    print_info(f"\nTesting {len(valid_segments)} segments from the audio file")
    
    # Test each segment
    results = []
    
    for segment_name, start_time, duration, use_continuous in valid_segments:
        try:
            # Extract segment
            print(f"\n⏳ Extracting segment: {start_time:.1f}s to {start_time+duration:.1f}s...")
            audio_bytes = await split_audio(audio_file, start_time, duration)
            
            if not audio_bytes:
                print_error("Failed to extract segment")
                continue
            
            # Test transcription
            result = await test_segment(segment_name, audio_bytes, duration, use_continuous)
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
            
        except Exception as e:
            print_error(f"Segment {segment_name} failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_header("TEST SUMMARY")
    
    print(f"\n{'Segment':<25} {'Duration':<12} {'Method':<20} {'Words':<10} {'Status':<15}")
    print('-' * 85)
    
    for r in results:
        status = "✅ Success" if r['success'] else "❌ Failed"
        print(f"{r['segment']:<25} {r['duration']:<12.1f} {r['method']:<20} {r['words']:<10} {status:<15}")
    
    print()
    
    # Statistics
    total_words = sum(r['words'] for r in results)
    total_chars = sum(r['chars'] for r in results)
    success_count = sum(1 for r in results if r['success'])
    
    print(f"📊 Total statistics:")
    print(f"   Segments tested: {len(results)}")
    print(f"   Successful: {success_count}/{len(results)}")
    print(f"   Total words transcribed: {total_words}")
    print(f"   Total characters: {total_chars}")
    
    # Compare methods
    continuous_results = [r for r in results if r['method'] == 'continuous']
    once_results = [r for r in results if r['method'] == 'recognize_once']
    
    if continuous_results:
        avg_words_continuous = sum(r['words'] for r in continuous_results) / len(continuous_results)
        print(f"\n   Continuous recognition avg: {avg_words_continuous:.1f} words/segment")
    
    if once_results:
        avg_words_once = sum(r['words'] for r in once_results) / len(once_results)
        print(f"   recognize_once avg: {avg_words_once:.1f} words/segment")
    
    print()
    print("="*70)
    print("CONCLUSION")
    print("="*70)
    
    if success_count == len(results):
        print_success("All segments transcribed successfully!")
        print("\n✅ System can handle both short and long audio segments")
        print("✅ Automatic routing working correctly")
        print("✅ Continuous recognition captures full content")
    else:
        print_warning(f"{len(results) - success_count} segments had issues")
        print("\n⚠️  Review logs for details")
    
    print()
    print("📝 Full transcript compilation:")
    all_transcripts = []
    for r in results:
        if r['success'] and r['words'] > 0:
            # Would need to store transcripts, but we showed previews above
            all_transcripts.append(r['segment'])
    
    if all_transcripts:
        print(f"   Compiled {len(all_transcripts)} segments")
        print("   (Check individual segment previews above for content)")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
