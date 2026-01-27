"""
Session Manager Service.
Tracks conversation state and audio clips per assessment response session.
"""
from typing import Dict, Any
from app.services.audio_merger import AudioMerger
from app.core.logging import api_logger


class SessionManager:
    """
    Manages in-memory session state for ongoing assessment conversations.
    Each session is tied to a response_id.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, response_id: str) -> Dict[str, Any]:
        """
        Get or create a session for a response.
        
        Args:
            response_id: Assessment response UUID
        
        Returns:
            Session dictionary with audio_merger, conversation_history, etc.
        """
        if response_id not in self.sessions:
            api_logger.info(f"Creating new session for response {response_id[:8]}")
            self.sessions[response_id] = {
                'audio_merger': AudioMerger(),
                'conversation_history': [],
                'turn_count': 0,
                'section': None,
                'started_at': None
            }
        
        return self.sessions[response_id]
    
    def update_session(self, response_id: str, **kwargs):
        """Update session data."""
        session = self.get_session(response_id)
        session.update(kwargs)
    
    def clear_session(self, response_id: str):
        """
        Clear session data after stage completes.
        
        Args:
            response_id: Assessment response UUID
        """
        if response_id in self.sessions:
            api_logger.info(f"Clearing session for response {response_id[:8]}")
            del self.sessions[response_id]
    
    def get_active_sessions(self) -> int:
        """Get count of active sessions."""
        return len(self.sessions)


# Singleton instance
session_manager = SessionManager()
