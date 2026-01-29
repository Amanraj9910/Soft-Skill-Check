import statistics
from typing import List, Dict, Any

class SpeechScoringService:
    """
    Calculates detailed speech metrics based on Azure Speech analysis results.
    """

    def calculate_scores(self, transcript_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Main entry point.
        Expects transcript_data to contain:
        - "words": List[Dict] with "offset", "duration", "word"
        - "transcript": Full text
        - "pronunciation_result": Dict with "fluency_score", "pronunciation_score", etc. (Optional)
        """
        words = transcript_data.get("words", [])
        if not words:
            return self._get_empty_scores()

        # 1. Fluency Metrics
        wpm_score = self._calculate_wpm_score(words)
        pause_score = self._calculate_pause_score(words)
        stability_score = self._calculate_stability_score(words)
        
        fluency_score = (0.5 * wpm_score) + (0.3 * pause_score) + (0.2 * stability_score)
        fluency_score = self._validate_score(fluency_score, 0, 20)

        # 2. Hesitation Metrics
        hesitation_score = self._calculate_hesitation_score(words, transcript_data.get("transcript", ""))
        hesitation_score = self._validate_score(hesitation_score, 0, 10)

        # 3. Pronunciation Metrics (Directly from Azure if available)
        pronunciation_raw = 0
        if transcript_data.get("pronunciation_result"):
            pronunciation_raw = transcript_data["pronunciation_result"].get("pronunciation_score", 0)
        
        # Normalize Azure (0-100) to (0-10)
        pronunciation_score = self._validate_score(pronunciation_raw / 10.0, 0, 10)

        # 4. Vocal Confidence
        # Formula: 0.6 * (hesitation_score) + 0.4 * stability_score
        # Note: stability_score is 0-20 scale usually from my helper? 
        # Actually I normalized stability_score to 0-20? Let's check below.
        # User Formula: 0.6 * (hesitation_score / 10) + 0.4 * stability_score 
        # Wait, Hesitation is 0-10. Stability is part of Fluency (0-20?).
        # Let's assume stability_score returned below is normalized to 0-10 for this formula or we adjust.
        # Let's standardize internal metrics to 0-10 for easy mixing, then scale up for final outputs if needed.
        
        # Adjusting approach:
        # User said: fluency_score = 0.5 * wpm_score + ... (Target 0-20)
        # So wpm_score, pause_score, stability_score should be on 0-20 scale?
        # Let's ensure helper methods return 0-20 scale.
        
        # User said: vocal_confidence = 0.6 * (hesitation_score / 10) + 0.4 * stability_score
        # Issues: 
        # - Hesitation is 0-10. So (hesitation/10) is 0-1.
        # - Stability: If it's 0-20, then 0.4 * 20 = 8.
        # - Result would be 0.6*1 + 8 = 8.6 max?
        # Maybe user meant stability_score normalized 0-1?
        # Or maybe vocal_confidence is 0-10 scale?
        # "Vocal Confidence (0-10)" -> Yes.
        # So if stability is 0-20, we need to normalize it to 0-10 or 0-1 for the formula.
        # Let's assume stability_score (0-10) for this calculation.
        
        # Let's get stability on 0-10 scale for Confidence calc, and 0-20 for Fluency calc.
        stability_10 = stability_score / 2.0 
        
        # Re-reading user formula:
        # "vocal_confidence = 0.6 * (hesitation_score / 10) + 0.4 * stability_score"
        # If result is 0-10 at end:
        # If Hesitation=10 (perfect), part1 = 0.6 * 1 = 0.6 (This is small!)
        # Maybe user meant: 0.6 * HesitationScore + 0.4 * StabilityScore?
        # If Hesitation=10, Stability=10 -> 6 + 4 = 10. This matches nicely.
        # So I will use: 0.6 * Hesitation (0-10) + 0.4 * Stability (0-10)
        
        vocal_confidence = (0.6 * hesitation_score) + (0.4 * stability_10)
        vocal_confidence = self._validate_score(vocal_confidence, 0, 10)

        return {
            "fluency_score": round(fluency_score, 1),
            "hesitation_score": round(hesitation_score, 1),
            "pronunciation_score": round(pronunciation_score, 1),
            "vocal_confidence_score": round(vocal_confidence, 1)
        }

    def _get_empty_scores(self):
        return {
            "fluency_score": 0.0,
            "hesitation_score": 0.0,
            "pronunciation_score": 0.0,
            "vocal_confidence_score": 0.0
        }

    def _validate_score(self, score, min_val, max_val):
        """Clamp score to range."""
        if score is None:
            return min_val
        return max(min_val, min(score, max_val))

    def _normalize(self, value, min_val, max_val, target_min=0, target_max=10):
        """Linearly map value to target range."""
        if value < min_val: return target_min
        if value > max_val: return target_max
        ratio = (value - min_val) / (max_val - min_val)
        return target_min + (ratio * (target_max - target_min))

    # --- Metrics Calculations ---

    def _calculate_wpm_score(self, words: List[Dict]) -> float:
        """
        Returns WPM Score (0-20).
        Target: 100-150 WPM is ideal (Score 20).
        < 50 WPM is poor. > 200 WPM is poor.
        """
        if not words: return 0
        
        duration_ticks = words[-1]['offset'] + words[-1]['duration'] - words[0]['offset']
        duration_min = (duration_ticks / 10_000_000) / 60.0
        
        if duration_min <= 0: return 0
        
        wpm = len(words) / duration_min
        
        # Simple trapezoid function for scoring
        # 0-50: 0 -> 10
        # 50-100: 10 -> 20
        # 100-150: 20
        # 150-200: 20 -> 10
        # 200+: 10 -> 0
        
        if wpm < 50:
            return self._normalize(wpm, 0, 50, 0, 10)
        elif wpm < 100:
            return self._normalize(wpm, 50, 100, 10, 20)
        elif wpm <= 160:
            return 20.0
        elif wpm < 220:
            return self._normalize(wpm, 160, 220, 20, 10)
        else:
            return 10.0 # Cap at 10 even for very fast speech? Or 0? Let's say 5.
            # User wants fairness. Extremely fast speech (auctioneer) is bad fluency. 
            # But 220 is reasonable for excited storytelling.
            # Let's return self.normalize for 220-250 -> 10-0
            if wpm < 250:
                 return self._normalize(wpm, 220, 250, 10, 0)
            return 0.0

    def _calculate_pause_score(self, words: List[Dict]) -> float:
        """
        Returns Pause Score (0-20).
        Ideal average pause: 0.5s - 1.0s?
        Too short (< 0.1s) -> rushed?
        Too long (> 2.0s) -> hesitant?
        
        Actually, we want to penalize *unnatural* pauses.
        User said: Based on Average pause length.
        
        Let's assume ideal avg pause between words is small (0.1-0.3s). 
        But this depends on sentence boundaries. 
        For now, let's map:
        Avg Pause < 0.5s: 20 (Good flow)
        Avg Pause 0.5-1.5s: Linear drop 20->5
        Avg Pause > 1.5s: 0
        """
        if len(words) < 2: return 20.0
        
        pauses = []
        for i in range(len(words) - 1):
            # End of Word[i] to Start of Word[i+1]
            end_prev = words[i]['offset'] + words[i]['duration']
            start_next = words[i+1]['offset']
            gap_sec = (start_next - end_prev) / 10_000_000
            if gap_sec > 0:
                pauses.append(gap_sec)
        
        if not pauses: return 20.0
        
        avg_pause = statistics.mean(pauses)
        
        if avg_pause <= 0.5:
             return 20.0
        elif avg_pause <= 2.0:
            return self._normalize(avg_pause, 0.5, 2.0, 20, 0)
        else:
            return 0.0

    def _calculate_stability_score(self, words: List[Dict]) -> float:
        """
        Returns Pace Stability Score (0-20).
        Inverse of variance/stdev of word durations?
        Or varience of inter-word gaps?
        User said: Pace stability.
        Let's use 20 - (Standard Deviation of pauses * factor).
        """
        if len(words) < 3: return 20.0
        
        pauses = []
        for i in range(len(words) - 1):
            end_prev = words[i]['offset'] + words[i]['duration']
            start_next = words[i+1]['offset']
            gap_sec = (start_next - end_prev) / 10_000_000
            pauses.append(gap_sec)
            
        if not pauses: return 20.0
        
        if len(pauses) < 2: return 20.0
        
        stdev = statistics.stdev(pauses)
        
        # If stdev is high (irregular pauses), score is low.
        # If stdev is 0 (robotic), score might be high?
        # Ideally, natural speech has some rhythm.
        # Let's penalize high variance.
        # Max expected stdev might be ~1.5s.
        
        score = 20 - (stdev * 10)
        return self._validate_score(score, 0, 20)

    def _calculate_hesitation_score(self, words: List[Dict], transcript: str) -> float:
        """
        User Formula: 10 * (1 - normalize(hesitation_ratio, 0.00, 0.12))
        hesitation_events = filler_count + long_pause_count
        hesitation_ratio = hesitation_events / total_words
        """
        # 1. Count Fillers
        fillers = ["um", "uh", "er", "ah", "like", "you know"]
        filler_count = 0
        
        # Simple text matching (case insensitive)
        # Note: Transcript from Azure might not contain 'um/uh' unless configured to 'TrueText' or similar.
        # But we assume they might be there or we rely on pauses primarily if Azure cleans them.
        # If Azure cleans them, we rely on Long Pauses.
        
        cleaned_words = transcript.lower().split()
        total_words = len(cleaned_words)
        if total_words == 0: return 0.0 # No speech?
        
        for w in cleaned_words:
            if w in fillers:
                filler_count += 1
                
        # 2. Count Long Pauses (> 1.5s)
        long_pause_count = 0
        if len(words) > 1:
            for i in range(len(words) - 1):
                end_prev = words[i]['offset'] + words[i]['duration']
                start_next = words[i+1]['offset']
                gap_sec = (start_next - end_prev) / 10_000_000
                if gap_sec > 1.5:
                    long_pause_count += 1
        
        hesitation_events = filler_count + long_pause_count
        ratio = hesitation_events / total_words
        
        # User formula: 10 * (1 - normalize(ratio, 0.00, 0.12))
        # My _normalize maps x to [min, max].
        # User wants ratio 0.00 -> 0, ratio 0.12 -> 1 (normalized value)
        # So NormalizedRatio = (ratio - 0) / (0.12 - 0)
        # Then Score = 10 * (1 - NormalizedRatio)
        
        normalized_ratio = ratio / 0.12
        if normalized_ratio > 1: normalized_ratio = 1
        if normalized_ratio < 0: normalized_ratio = 0
        
        score = 10 * (1 - normalized_ratio)
        return score

speech_scoring_service = SpeechScoringService()
