import sys
import os

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.services.ai_assessment.speech_scoring import SpeechScoringService

def create_mock_word(word, duration_sec, pause_after_sec=0.1):
    """Creates a mock word dict."""
    return {
        "word": word,
        "duration": duration_sec * 10_000_000, # Ticks
        "offset": 0, # Will calculate in sequence
        "pause_after": pause_after_sec
    }

def generate_sentence(words_with_durations):
    """
    Generates a list of word dicts with offsets calculated.
    Input: list of (word, duration_sec, pause_after_sec)
    """
    result = []
    current_offset = 0
    
    for i, (w, dur, pause) in enumerate(words_with_durations):
        # Offset is start time
        obj = {
            "word": w,
            "duration": int(dur * 10_000_000),
            "offset": int(current_offset * 10_000_000)
        }
        result.append(obj)
        current_offset += dur + pause
        
    return result

def test_scenario(name, words, transcript, expected_range=None):
    service = SpeechScoringService()
    
    # Mock Azure transcript data
    data = {
        "words": words,
        "transcript": transcript,
        "pronunciation_result": {
            "pronunciation_score": 90.0 # Good pronunciation base
        }
    }
    
    scores = service.calculate_scores(data)
    
    print(f"\n--- Scenario: {name} ---")
    print(f"Transcript: {transcript[:50]}...")
    print(f"Scores: {scores}")
    
    if expected_range:
        for key, (min_v, max_v) in expected_range.items():
            val = scores.get(key)
            if min_v <= val <= max_v:
                 print(f"✅ {key}: {val} is within [{min_v}, {max_v}]")
            else:
                 print(f"❌ {key}: {val} is OUT of range [{min_v}, {max_v}]")

def run_calibration():
    # 1. Perfect Scenario (Fast, smooth, no hesitations)
    # 120 WPM ~ 2 words per second. 0.3s word, 0.2s pause.
    words_perfect = [("word", 0.3, 0.1)] * 60 # 60 words
    # Total time approx: 60 * 0.4 = 24s.
    # WPM = 60 / (24/60) = 60 / 0.4 = 150 WPM. (Ideal)
    mock_input_1 = generate_sentence(words_perfect)
    test_scenario("Perfect Flow (150 WPM)", mock_input_1, "word "*60, 
                  {"fluency_score": (18, 20), "hesitation_score": (9, 10)})

    # 2. Slow & Hesitant
    # 40 WPM. Long pauses. Fillers.
    # Words: 20 words.
    # 1s duration words (slow), 1s pauses.
    # Plus "um" fillers.
    words_slow = [("hello", 0.5, 0.5), ("um", 0.5, 2.0), ("world", 0.5, 1.0)] * 5
    # Includes 'um' -> filler. 
    # Includes 2.0s pause -> long pause.
    mock_input_2 = generate_sentence(words_slow)
    transcript_2 = "hello um world " * 5
    test_scenario("Slow with Fillers", mock_input_2, transcript_2,
                  {"fluency_score": (0, 8), "hesitation_score": (0, 5)})
                  
    # 3. Fast but Stable
    # 180 WPM
    words_fast = [("fast", 0.2, 0.05)] * 100
    mock_input_3 = generate_sentence(words_fast)
    test_scenario("Fast (180+ WPM)", mock_input_3, "fast "*100,
                 {"fluency_score": (15, 20)})

if __name__ == "__main__":
    run_calibration()
