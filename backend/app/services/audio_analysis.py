"""
Audio feature extraction and analysis using librosa.
"""
import librosa
import numpy as np
from typing import Dict, Any, Optional
import soundfile as sf


class AudioAnalysisService:
    """Service for extracting audio features for confidence and fluency scoring."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize audio analysis service.
        
        Args:
            sample_rate: Target sample rate for audio processing
        """
        self.sample_rate = sample_rate
    
    async def extract_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive audio features from file.
        
        Args:
            audio_file_path: Path to audio file
        
        Returns:
            Dictionary of extracted features
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_file_path, sr=self.sample_rate)
            
            # Extract all features
            volume_features = self._extract_volume_features(audio)
            pitch_features = self._extract_pitch_features(audio, sr)
            silence_features = self._extract_silence_features(audio, sr)
            pace_features = self._extract_pace_features(audio, sr)
            energy_features = self._extract_energy_features(audio)
            spectral_features = self._extract_spectral_features(audio, sr)
            
            # Combine all features
            all_features = {
                **volume_features,
                **pitch_features,
                **silence_features,
                **pace_features,
                **energy_features,
                **spectral_features,
                "duration": float(len(audio) / sr)
            }
            
            return {
                "success": True,
                "features": all_features
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "features": {}
            }
    
    def _extract_volume_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract volume-related features."""
        # Convert to dB
        rms = librosa.feature.rms(y=audio)[0]
        db = librosa.amplitude_to_db(rms, ref=np.max)
        
        return {
            "average_volume": float(np.mean(db)),
            "max_volume": float(np.max(db)),
            "min_volume": float(np.min(db)),
            "volume_variance": float(np.var(db))
        }
    
    def _extract_pitch_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract pitch-related features."""
        # Extract pitch using piptrack
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        
        # Get pitch values where magnitude is highest
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # Valid pitch
                pitch_values.append(pitch)
        
        if len(pitch_values) > 0:
            pitch_array = np.array(pitch_values)
            return {
                "average_pitch": float(np.mean(pitch_array)),
                "max_pitch": float(np.max(pitch_array)),
                "min_pitch": float(np.min(pitch_array)),
                "pitch_variance": float(np.var(pitch_array)),
                "pitch_stability_score": float(100 - min(np.std(pitch_array), 100))
            }
        else:
            return {
                "average_pitch": 0.0,
                "max_pitch": 0.0,
                "min_pitch": 0.0,
                "pitch_variance": 0.0,
                "pitch_stability_score": 0.0
            }
    
    def _extract_silence_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract silence and pause features."""
        # Detect silence intervals
        intervals = librosa.effects.split(audio, top_db=30)
        
        # Calculate silence
        total_duration = len(audio) / sr
        speech_duration = sum((end - start) / sr for start, end in intervals)
        silence_duration = total_duration - speech_duration
        
        # Calculate pauses (gaps between speech intervals)
        pauses = []
        for i in range(len(intervals) - 1):
            pause_duration = (intervals[i + 1][0] - intervals[i][1]) / sr
            if pause_duration > 0.1:  # Minimum 100ms to count as pause
                pauses.append(pause_duration)
        
        return {
            "silence_ratio": float(silence_duration / total_duration) if total_duration > 0 else 0.0,
            "total_silence_duration": float(silence_duration),
            "average_pause_duration": float(np.mean(pauses)) if pauses else 0.0,
            "longest_pause_duration": float(np.max(pauses)) if pauses else 0.0,
            "pause_count": len(pauses)
        }
    
    def _extract_pace_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract speech pace features."""
        # Use onset detection to estimate syllable rate
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        
        duration = len(audio) / sr
        syllables_per_second = len(onsets) / duration if duration > 0 else 0
        
        # Calculate tempo variation
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        
        return {
            "speech_tempo": float(syllables_per_second),
            "estimated_tempo": float(tempo),
            "pace_variance": float(np.std(onset_env))
        }
    
    def _extract_energy_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract energy features."""
        # RMS energy
        rms = librosa.feature.rms(y=audio)[0]
        
        return {
            "energy_level": float(np.mean(rms)),
            "energy_variance": float(np.var(rms))
        }
    
    def _extract_spectral_features(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Extract spectral features."""
        # Spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        
        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        
        return {
            "spectral_centroid": float(np.mean(spectral_centroids)),
            "spectral_rolloff": float(np.mean(spectral_rolloff)),
            "zero_crossing_rate": float(np.mean(zcr))
        }
    
    async def detect_filler_words(
        self,
        transcript: str,
        filler_words: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Detect filler words in transcript.
        
        Args:
            transcript: Speech transcript
            filler_words: List of filler words to detect
        
        Returns:
            Dictionary with filler word counts
        """
        if filler_words is None:
            filler_words = [
                "um", "uh", "er", "ah", "like", "you know",
                "sort of", "kind of", "i mean", "basically",
                "actually", "literally", "right", "okay", "well"
            ]
        
        transcript_lower = transcript.lower()
        
        filler_counts = {}
        total_count = 0
        
        for filler in filler_words:
            count = transcript_lower.count(filler)
            if count > 0:
                filler_counts[filler] = count
                total_count += count
        
        return {
            "total_filler_count": total_count,
            "filler_breakdown": filler_counts,
            "filler_density": total_count / len(transcript.split()) if transcript else 0.0
        }
    
    async def calculate_speech_rate(
        self,
        transcript: str,
        duration: float
    ) -> Dict[str, float]:
        """
        Calculate speech rate metrics.
        
        Args:
            transcript: Speech transcript
            duration: Audio duration in seconds
        
        Returns:
            Speech rate metrics
        """
        words = transcript.split()
        word_count = len(words)
        
        if duration > 0:
            words_per_minute = (word_count / duration) * 60
            syllable_count = sum(self._count_syllables(word) for word in words)
            syllables_per_minute = (syllable_count / duration) * 60
        else:
            words_per_minute = 0.0
            syllables_per_minute = 0.0
        
        return {
            "words_per_minute": words_per_minute,
            "syllables_per_minute": syllables_per_minute,
            "average_word_length": np.mean([len(word) for word in words]) if words else 0.0
        }
    
    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count in a word (simple heuristic)."""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        # Every word has at least one syllable
        if syllable_count == 0:
            syllable_count = 1
        
        return syllable_count


# Create singleton instance
audio_analysis_service = AudioAnalysisService()


def get_audio_analysis_service() -> AudioAnalysisService:
    """Dependency for accessing audio analysis service."""
    return audio_analysis_service
