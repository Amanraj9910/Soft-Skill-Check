"""
Test transcription using CONTINUOUS RECOGNITION for long audio.
This demonstrates the fix for the 30-second limit issue.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import azure.cognitiveservices.speech as speechsdk
from app.config import settings

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

async def transcribe_continuous(audio_bytes: bytes) -> str:
    """
    Transcribe audio using continuous recognition.
    This handles audio longer than 30 seconds.
    """
    def _sync_transcribe():
        all_results = []
        done_flag = False
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Setup speech config
                speech_config = speechsdk.SpeechConfig(
                    subscription=settings.AZURE_SPEECH_KEY,
                    region=settings.AZURE_SPEECH_REGION
                )
                speech_config.speech_recognition_language = settings.AZURE_SPEECH_LANGUAGE
                
                # Setup audio config
                audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
                
                # Create recognizer
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=speech_config, 
                    audio_config=audio_config
                )
                
                # Handle recognized utterances
                def handle_recognized(evt):
                    if evt.result.text:
                        all_results.append(evt.result.text)
                        print_info(f"Recognized segment ({len(evt.result.text)} chars): {evt.result.text[:50]}...")
                
                # Handle cancellation
                def handle_canceled(evt):
                    nonlocal done_flag
                    done_flag = True
                    print_warning(f"Recognition canceled: {evt.reason}")
                    if evt.reason == speechsdk.CancellationReason.Error:
                        print_error(f"Error: {evt.cancellation_details.error_details}")
                
                # Connect event handlers
                recognizer.recognized.connect(handle_recognized)
                recognizer.canceled.connect(handle_canceled)
                
                # Start continuous recognition
                print_info("Starting continuous recognition...")
                recognizer.start_continuous_recognition()
                
                # Wait for recognition to complete (file ends or long silence)
                import time
                wait_count = 0
                max_wait = 300  # Max 5 minutes for very long files
                
                while not done_flag and wait_count < max_wait:
                    time.sleep(0.5)
                    wait_count += 1
                
                # Stop recognition
                print_info("Stopping recognition...")
                recognizer.stop_continuous_recognition()
                
                # Combine all results
                full_transcript = " ".join(all_results)
                print_success(f"Transcription complete: {len(full_transcript)} chars, {len(all_results)} segments")
                return full_transcript
                
            finally:
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
        except Exception as e:
            print_error(f"Transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    return await asyncio.to_thread(_sync_transcribe)

async def test_audio_with_continuous(audio_path: str):
    """Test continuous transcription on audio file."""
    print_header("CONTINUOUS RECOGNITION TEST")
    print_info("This method handles audio > 30 seconds")
    print()
    
    # Check if file exists
    if not os.path.exists(audio_path):
        print_error(f"File not found: {audio_path}")
        return
    
    # Get file info
    file_size = os.path.getsize(audio_path)
    print_info(f"File: {audio_path}")
    print_info(f"Size: {file_size/1024:.1f} KB")
    print()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv(".env.backend")
    
    if not os.getenv("AZURE_SPEECH_KEY"):
        print_error("Missing AZURE_SPEECH_KEY in .env.backend")
        return
    
    print_success("Azure Speech credentials loaded")
    print()
    
    # Read and convert audio
    print_info("Reading audio file...")
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    
    print_info(f"Loaded {len(audio_bytes)/1024:.1f} KB")
    print()
    
    # Convert to WAV
    from app.services.ai_assessment.azure_speech import speech_service
    print_info("Converting to WAV...")
    wav_bytes = await speech_service.convert_to_wav(audio_bytes)
    
    if not wav_bytes:
        print_error("Failed to convert audio")
        return
    
    print_success(f"Converted: {len(wav_bytes)/1024:.1f} KB")
    print()
    
    # Transcribe with continuous recognition
    print("="*70)
    print("TRANSCRIBING WITH CONTINUOUS RECOGNITION")
    print("="*70)
    print()
    
    transcript = await transcribe_continuous(wav_bytes)
    
    # Analyze results
    print_header("RESULTS")
    
    words = transcript.split()
    word_count = len(words)
    
    print(f"📝 Total characters: {len(transcript)}")
    print(f"📊 Total words: {word_count}")
    print(f"📈 Segments recognized: {transcript.count('.') + transcript.count('!') + transcript.count('?')}")
    print()
    
    # Save to file
    output_file = "test_transcript_continuous.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Audio File: {audio_path}\n")
        f.write(f"Method: Continuous Recognition\n")
        f.write(f"Characters: {len(transcript)}\n")
        f.write(f"Words: {word_count}\n")
        f.write(f"\n{'='*70}\n\n")
        f.write(transcript)
    
    print_success(f"Full transcript saved to: {output_file}")
    print()
    
    # Show preview
    print("="*70)
    print("TRANSCRIPT PREVIEW")
    print("="*70)
    print()
    
    if len(transcript) < 1000:
        print(transcript)
    else:
        print(f"First 1000 chars:\n{transcript[:1000]}...\n")
        print(f"...\n\nLast 1000 chars:\n...{transcript[-1000:]}")
    
    print()
    print("="*70)
    
    # Compare with recognize_once
    print_header("COMPARISON")
    print()
    print("Previous method (recognize_once):")
    print("  - Only 4 words: 'Hello my name is.'")
    print("  - Truncated after ~30 seconds")
    print()
    print(f"Continuous recognition:")
    print(f"  - {word_count} words transcribed")
    print(f"  - Full {len(transcript)} characters captured")
    improvement = ((word_count - 4) / 4 * 100) if word_count > 4 else 0
    print(f"  - ✅ {improvement:.0f}% MORE content captured!")
    print()
    
    if word_count > 50:
        print_success("Continuous recognition successfully handled long audio!")
    else:
        print_warning("Still low word count - may indicate other issues")
    
    print()

if __name__ == "__main__":
    # Test the specified audio file
    audio_file = r"D:\AI Projects\Soft Skill Check\Test-EA.m4a"
    
    if not os.path.exists(audio_file):
        print(f"\n❌ Error: File not found at {audio_file}")
        sys.exit(1)
    
    asyncio.run(test_audio_with_continuous(audio_file))
