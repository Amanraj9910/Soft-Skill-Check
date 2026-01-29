from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class AssessmentStepScore(BaseModel):
    fluency: int
    pronunciation: int
    grammar: int
    confidence: int  # Kept for backward compatibility, represents vocal confidence
    vocal_confidence: int = 0
    textual_confidence: int = 0
    hesitation: int
    storytelling: int
    vision_clarity: int
    aim_clarity: int = 0
    total_step_score: float
    feedback: str
    improvement_tips: List[str]

class AIAnalysisResult(BaseModel):
    transcript: str
    scores: AssessmentStepScore
    ai_response_text: str
    ai_response_audio_url: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None
