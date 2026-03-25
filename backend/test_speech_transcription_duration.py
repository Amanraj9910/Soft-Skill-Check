"""
Diagnostic script to test Azure Speech transcription with different audio lengths.
This will help identify if the 30-second limit is affecting your assessments.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

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

async def test_transcription_with_duration(audio_path: str, expected_duration: float):
    """Test transcription and check if it's complete."""
    try:
        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        print_info(f"Testing audio: {expected_duration:.1f}s duration, {len(audio_bytes)/1024:.1f}KB")
        
        # Transcribe using current method (recognize_once)
        transcript = await speech_service.transcribe_audio(audio_bytes)
        
        # Calculate words per second (rough estimate)
        words = transcript.split()
        word_count = len(words)
        wps = word_count / expected_duration if expected_duration > 0 else 0
        
        print(f"📝 Transcript length: {len(transcript)} chars, {word_count} words")
        print(f"📊 Speech rate: {wps:.2f} words/second")
        
        # Check if likely truncated
        if expected_duration > 30:
            expected_min_words = int(expected_duration * 1.5)  # Conservative estimate
            if word_count < expected_min_words * 0.7:  # Less than 70% of expected
                print_warning(f"⚠️  LIKELY TRUNCATED! Expected ~{expected_min_words}+ words, got {word_count}")
                print_warning(f"   This suggests the 30s limit cut off your audio!")
            else:
                print_success(f"✓ Transcript appears complete ({word_count} words)")
        else:
            print_success(f"✓ Short audio transcribed successfully")
        
        # Show first/last parts
        if len(transcript) > 100:
            print(f"\n   First 100 chars: {transcript[:100]}...")
            print(f"   Last 100 chars: ...{transcript[-100:]}")
        else:
            print(f"\n   Full transcript: {transcript}")
        
        print()
        return {
            'duration': expected_duration,
            'transcript_length': len(transcript),
            'word_count': word_count,
            'likely_truncated': expected_duration > 30 and word_count < int(expected_duration * 1.5) * 0.7
        }
        
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        return None

async def generate_test_audio(duration_seconds: float, output_path: str):
    """Generate a test WAV file with simulated speech."""
    import wave
    import struct
    import math
    
    sample_rate = 16000
    num_samples = int(sample_rate * duration_seconds)
    
    # Generate a simple tone pattern (simulates speech-like audio)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Mix of frequencies to sound more like speech
        value = 0.5 * math.sin(2 * math.pi * 200 * t)  # Base frequency
        value += 0.3 * math.sin(2 * math.pi * 300 * (t + 0.1))  # Harmonic
        value += 0.2 * math.sin(2 * math.pi * 150 * (t + 0.2))  # Another harmonic
        
        # Add some "pauses" every few seconds
        if int(t) % 5 == 4 and t % 1 > 0.5:
            value = 0
        
        samples.append(int(value * 10000))
    
    # Write WAV file
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(struct.pack(f'{num_samples}h', *samples))
    
    print_info(f"Generated test audio: {output_path} ({duration_seconds:.1f}s)")

async def main():
    print_header("AZURE SPEECH TRANSCRIPTION DIAGNOSTIC")
    
    # Load environment
    load_dotenv(".env.backend")
    
    if not os.getenv("AZURE_SPEECH_KEY"):
        print_error("Missing AZURE_SPEECH_KEY in .env.backend")
        return
    
    print_success("Azure Speech credentials loaded")
    print()
    
    # Test scenarios
    test_durations = [10, 20, 30, 40, 50, 60]
    results = []
    
    temp_dir = tempfile.gettempdir()
    
    for duration in test_durations:
        print(f"\n{'='*70}")
        print(f"TEST {duration} SECONDS")
        print('='*70)
        
        # Generate test audio
        test_file = os.path.join(temp_dir, f"test_audio_{duration}s.wav")
        await generate_test_audio(duration, test_file)
        
        # Test transcription
        result = await test_transcription_with_duration(test_file, duration)
        if result:
            results.append(result)
        
        # Cleanup
        try:
            os.remove(test_file)
        except:
            pass
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    print(f"{'Duration':<12} {'Words':<10} {'Status':<20}")
    print('-' * 50)
    
    for r in results:
        status = "⚠️  TRUNCATED" if r['likely_truncated'] else "✅ Complete"
        print(f"{r['duration']:<12.1f} {r['word_count']:<10} {status:<20}")
    
    print()
    
    # Count issues
    truncated_count = sum(1 for r in results if r['likely_truncated'])
    
    if truncated_count > 0:
        print_error(f"FOUND ISSUE: {truncated_count}/{len(results)} tests show truncation")
        print_warning("\nThe 30-second recognize_once() limit IS affecting your assessments!")
        print_info("\nRecommended fix:")
        print("1. Use start_continuous_recognition_async() for long sections")
        print("2. See: backend/SPEECH_API_LONG_AUDIO_FIX.md for implementation guide")
    else:
        print_success("No truncation detected in synthetic tests")
        print_warning("Note: Real speech may behave differently - test with actual user recordings")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
