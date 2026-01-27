"""
Audio Merger Service.
Merges user and AI audio clips chronologically into a single conversation recording.
"""
from pydub import AudioSegment
import io
import time
from typing import List, Dict, Optional
from app.core.logging import api_logger, error_logger


class AudioMerger:
    """Manages accumulation and merging of audio clips for a conversation."""
    
    def __init__(self):
        self.audio_clips: List[Dict] = []
    
    def add_clip(self, audio_bytes: bytes, speaker: str = 'user'):
        """
        Add an audio clip to the conversation.
        
        Args:
            audio_bytes: Raw audio data (WAV format)
            speaker: 'user' or 'agent'
        """
        self.audio_clips.append({
            'timestamp': time.time(),
            'audio': audio_bytes,
            'speaker': speaker
        })
        api_logger.info(f"Added {speaker} audio clip ({len(audio_bytes)} bytes). Total clips: {len(self.audio_clips)}")
    
    def merge_conversation(self) -> Optional[bytes]:
        """
        Merge all accumulated audio clips chronologically with silence between turns.
        
        Returns:
            Merged WAV audio as bytes, or None if no clips
        """
        if not self.audio_clips:
            api_logger.warning("No audio clips to merge")
            return None
        
        try:
            api_logger.info(f"Merging {len(self.audio_clips)} audio clips...")
            
            # Sort by timestamp
            # Sort by timestamp
            sorted_clips = sorted(self.audio_clips, key=lambda x: x['timestamp'])
            
            # Filter for user clips only (redundant if we only add user clips, but safe)
            user_clips = [c for c in sorted_clips if c.get('speaker') == 'user']
            
            if not user_clips:
                api_logger.warning("No user clips to merge")
                return None
                
            # Determine format from first clip if possible, or default to 16k
            frame_rate = 16000
            
            # Start with brief silence (matching 16k to avoid resampling)
            combined = AudioSegment.silent(duration=500, frame_rate=frame_rate)
            silence_between = AudioSegment.silent(duration=1000, frame_rate=frame_rate)
            
            for i, clip in enumerate(user_clips):
                try:
                    # Load audio segment
                    # input is already WAV bytes from convert_to_wav
                    # Use from_wav to force using python's wave module and avoid ffmpeg fallback
                    audio_segment = AudioSegment.from_wav(io.BytesIO(clip['audio']))
                    
                    # Add to combined audio
                    combined += audio_segment
                    
                    # Add silence after (except for last clip)
                    if i < len(user_clips) - 1:
                        combined += silence_between
                    
                    api_logger.debug(f"Merged clip {i+1}/{len(user_clips)} ({clip['speaker']})")
                    
                except Exception as e:
                    error_logger.error(f"Failed to merge clip {i}: {str(e)}")
                    continue
            
            # Export to bytes
            output = io.BytesIO()
            combined.export(output, format='wav')
            merged_bytes = output.getvalue()
            
            api_logger.info(f"✅ Merged conversation: {len(merged_bytes)} bytes ({len(combined)/1000:.1f}s)")
            return merged_bytes
            
        except Exception as e:
            error_logger.error(f"Audio merge failed: {str(e)}")
            return None
    
    def clear(self):
        """Clear all accumulated clips."""
        clip_count = len(self.audio_clips)
        self.audio_clips = []
        api_logger.info(f"Cleared {clip_count} audio clips from merger")
    
    def get_clip_count(self) -> int:
        """Get number of accumulated clips."""
        return len(self.audio_clips)
