"""
Audio feature extraction - Simplified version without librosa dependency.
This version returns mock data for development/testing when librosa is not available.
"""
from typing import Dict, Any, Optional
import warnings

# Try to import librosa, but don't fail if it's not available
try:
    import librosa
    import numpy as np
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    warnings.warn(
        "Audio analysis libraries (librosa, soundfile) not available. "
        "Audio feature extraction will return mock data. "
        "Install: pip install librosa soundfile"
    )


class AudioAnalysisService:
    """Service for extracting audio features for confidence and fluency scoring."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize audio analysis service.
        
        Args:
            sample_rate: Target sample rate for audio processing
        """
        self.sample_rate = sample_rate
        self.librosa_available = LIBROSA_AVAILABLE
    
    async def extract_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive audio features from file.
        
        Args:
            audio_file_path: Path to audio file
        
        Returns:
            Dictionary of extracted features
        """
        if not self.librosa_available:
            return self._get_mock_features(audio_file_path)
        
        try:
            # Offload CPU-heavy librosa analysis to thread pool
            import asyncio
            
            def _sync_extract():
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
            
            return await asyncio.to_thread(_sync_extract)
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "features": {}
            }
    
    def _get_mock_features(self, audio_file_path: str) -> Dict[str, Any]:
        """Return mock features when librosa is not available."""
        import os
        
        # Estimate duration from file size (very rough estimate)
        try:
            file_size = os.path.getsize(audio_file_path)
            estimated_duration = file_size / 32000  # Rough estimate for 16kHz mono
        except:
            estimated_duration = 10.0
        
        return {
            "success": True,
            "features": {
                # Volume features (mock values based on typical speech)
                "average_volume": -20.0,
                "max_volume": -10.0,
                "min_volume": -40.0,
                "volume_variance": 50.0,
                
                # Pitch features (mock values for typical adult speech)
                "average_pitch": 180.0,
                "max_pitch": 250.0,
                "min_pitch": 120.0,
                "pitch_variance": 400.0,
                "pitch_stability_score": 75.0,
                
                # Silence features (mock values for natural speech)
                "silence_ratio": 0.15,
                "total_silence_duration": estimated_duration * 0.15,
                "average_pause_duration": 0.5,
                "longest_pause_duration": 1.2,
                "pause_count": int(estimated_duration / 5),
                
                # Pace features (mock values for moderate pace)
                "speech_tempo": 3.5,
                "estimated_tempo": 120.0,
                "pace_variance": 0.8,
                
                # Energy features (mock values)
                "energy_level": 0.08,
                "energy_variance": 0.002,
                
                # Spectral features (mock values)
                "spectral_centroid": 2000.0,
                "spectral_rolloff": 4000.0,
                "zero_crossing_rate": 0.05,
                
                "duration": estimated_duration,
                "_note": "Mock data - librosa not installed"
            }
        }
    
    def _extract_volume_features(self, audio) -> Dict[str, float]:
        """Extract volume-related features."""
        rms = librosa.feature.rms(y=audio)[0]
        db = librosa.amplitude_to_db(rms, ref=np.max)
        
        return {
            "average_volume": float(np.mean(db)),
            "max_volume": float(np.max(db)),
            "min_volume": float(np.min(db)),
            "volume_variance": float(np.var(db))
        }
    
    def _extract_pitch_features(self, audio, sr: int) -> Dict[str, float]:
        """Extract pitch-related features."""
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
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
    
    def _extract_silence_features(self, audio, sr: int) -> Dict[str, float]:
        """Extract silence and pause features."""
        intervals = librosa.effects.split(audio, top_db=30)
        
        total_duration = len(audio) / sr
        speech_duration = sum((end - start) / sr for start, end in intervals)
        silence_duration = total_duration - speech_duration
        
        pauses = []
        for i in range(len(intervals) - 1):
            pause_duration = (intervals[i + 1][0] - intervals[i][1]) / sr
            if pause_duration > 0.1:
                pauses.append(pause_duration)
        
        return {
            "silence_ratio": float(silence_duration / total_duration) if total_duration > 0 else 0.0,
            "total_silence_duration": float(silence_duration),
            "average_pause_duration": float(np.mean(pauses)) if pauses else 0.0,
            "longest_pause_duration": float(np.max(pauses)) if pauses else 0.0,
            "pause_count": len(pauses)
        }
    
    def _extract_pace_features(self, audio, sr: int) -> Dict[str, float]:
        """Extract speech pace features."""
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        
        duration = len(audio) / sr
        syllables_per_second = len(onsets) / duration if duration > 0 else 0
        
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        
        return {
            "speech_tempo": float(syllables_per_second),
            "estimated_tempo": float(tempo),
            "pace_variance": float(np.std(onset_env))
        }
    
    def _extract_energy_features(self, audio) -> Dict[str, float]:
        """Extract energy features."""
        rms = librosa.feature.rms(y=audio)[0]
        
        return {
            "energy_level": float(np.mean(rms)),
            "energy_variance": float(np.var(rms))
        }
    
    def _extract_spectral_features(self, audio, sr: int) -> Dict[str, float]:
        """Extract spectral features."""
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
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
        """Detect filler words in transcript."""
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
        """Calculate speech rate metrics."""
        words = transcript.split()
        word_count = len(words)
        
        if duration > 0:
            words_per_minute = (word_count / duration) * 60
            syllable_count = sum(self._count_syllables(word) for word in words)
            syllables_per_minute = (syllable_count / duration) * 60
        else:
            words_per_minute = 0.0
            syllables_per_minute = 0.0
        
        if not LIBROSA_AVAILABLE:
            avg_word_len = sum(len(word) for word in words) / len(words) if words else 0.0
        else:
            import numpy as np
            avg_word_len = np.mean([len(word) for word in words]) if words else 0.0
        
        return {
            "words_per_minute": words_per_minute,
            "syllables_per_minute": syllables_per_minute,
            "average_word_length": float(avg_word_len)
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
        
        if word.endswith('e'):
            syllable_count -= 1
        
        if syllable_count == 0:
            syllable_count = 1
        
        return syllable_count


# Create singleton instance
audio_analysis_service = AudioAnalysisService()


def get_audio_analysis_service() -> AudioAnalysisService:
    """Dependency for accessing audio analysis service."""
    return audio_analysis_service
