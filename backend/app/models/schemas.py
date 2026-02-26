"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class AssessmentStatus(str, Enum):
    """Assessment status enumeration."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssessmentGrade(str, Enum):
    """Assessment grade enumeration."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AssessmentSection(str, Enum):
    """Assessment section enumeration."""
    INTRODUCTION = "introduction"
    READING = "reading"
    LISTENING = "listening"
    STORYTELLING = "storytelling"
    OPINION = "opinion"
    AIM = "aim"


# ============================================
# USER & PROFILE MODELS
# ============================================

class UserProfile(BaseModel):
    """User profile model."""
    id: str
    email: str
    full_name: Optional[str] = None
    role: str = "candidate"  # 'candidate', 'employee', 'hr', 'onboarder', 'admin'
    created_at: datetime
    total_assessments: int = 0
    average_score: float = 0.0
    last_assessment_at: Optional[datetime] = None
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================
# ASSESSMENT MODELS
# ============================================

class AssessmentCreate(BaseModel):
    """Model for creating new assessment."""
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class AssessmentResponse(BaseModel):
    """Assessment response model."""
    id: str
    user_id: str
    status: AssessmentStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_score: Optional[float] = None
    grade: Optional[AssessmentGrade] = None
    full_audio_url: Optional[str] = None
    total_duration_seconds: Optional[int] = None
    current_section: Optional[AssessmentSection] = None
    
    model_config = ConfigDict(use_enum_values=True)


class AssessmentListResponse(BaseModel):
    """List of assessments."""
    assessments: List[AssessmentResponse]
    total: int


# ============================================
# RESPONSE MODELS
# ============================================

class ResponseCreate(BaseModel):
    """Model for creating assessment response."""
    assessment_id: str
    section: AssessmentSection
    section_order: int
    question_text: str
    user_transcript: Optional[str] = None
    agent_transcript: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[int] = None
    
    model_config = ConfigDict(use_enum_values=True)


class ResponseData(BaseModel):
    """Assessment response data."""
    id: str
    assessment_id: str
    section: AssessmentSection
    question_text: str
    user_transcript: Optional[str] = None
    audio_url: Optional[str] = None
    words_per_minute: Optional[float] = None
    pronunciation_score: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================
# SCORING MODELS
# ============================================

class ScoresData(BaseModel):
    """Detailed scores data."""
    assessment_id: str
    fluency_score: float = Field(..., ge=0, le=20)
    pronunciation_score: float = Field(..., ge=0, le=10)
    grammar_score: float = Field(..., ge=0, le=10)
    vocal_confidence_score: float = Field(..., ge=0, le=20)
    hesitation_score: float = Field(..., ge=0, le=10)
    storytelling_score: float = Field(..., ge=0, le=20)
    vision_clarity_score: float = Field(..., ge=0, le=10)
    aim_clarity_score: float = Field(..., ge=0, le=10)
    textual_confidence: float = Field(..., ge=0, le=10)
    total_score: Optional[float] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    overall_feedback: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)
    
    # New fields for holistic scoring
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed score breakdown with reasoning")
    grade: Optional[AssessmentGrade] = None
    
    @validator('total_score', always=True)
    def calculate_total(cls, v, values):
        """Auto-calculate total score."""
        if v is not None:
            return v
        return (
            values.get('fluency_score', 0) +
            values.get('pronunciation_score', 0) +
            values.get('grammar_score', 0) +
            values.get('vocal_confidence_score', 0) +
            values.get('hesitation_score', 0) +
            values.get('storytelling_score', 0) +
            values.get('vision_clarity_score', 0) +
            values.get('aim_clarity_score', 0) +
            values.get('textual_confidence', 0)
        )


class ScoresResponse(BaseModel):
    """Complete scores response."""
    assessment_id: str
    fluency_score: Optional[float] = 0.0
    pronunciation_score: Optional[float] = 0.0
    grammar_score: Optional[float] = 0.0
    vocal_confidence_score: Optional[float] = 0.0
    hesitation_score: Optional[float] = 0.0
    storytelling_score: Optional[float] = 0.0
    vision_clarity_score: Optional[float] = 0.0
    aim_clarity_score: Optional[float] = 0.0
    textual_confidence: Optional[float] = 0.0
    total_score: Optional[float] = 0.0
    grade: Optional[AssessmentGrade] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    overall_feedback: Optional[str] = "Assessment completed."
    details: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================
# CONVERSATION MODELS
# ============================================

class ConversationMessage(BaseModel):
    """Single conversation message."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ConversationRequest(BaseModel):
    """Request for AI conversation."""
    assessment_id: str
    section: AssessmentSection
    user_message: Optional[str] = None
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    
    model_config = ConfigDict(use_enum_values=True)


class ConversationResponse(BaseModel):
    """AI agent response."""
    agent_message: str
    audio_url: Optional[str] = None
    tokens_used: Optional[int] = None


# ============================================
# AUDIO MODELS
# ============================================

class AudioUploadResponse(BaseModel):
    """Response for audio upload."""
    success: bool
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


class AIInteractionResponse(BaseModel):
    """Response containing AI analysis and reply."""
    transcript: str
    ai_response_text: str
    ai_audio_url: Optional[str] = None
    scores: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    should_transition: bool = False
    next_section: Optional[str] = None


class SpeechToTextRequest(BaseModel):
    """Request for speech-to-text."""
    audio_url: Optional[str] = None
    reference_text: Optional[str] = None  # For pronunciation assessment


class SpeechToTextResponse(BaseModel):
    """Response from speech-to-text."""
    success: bool
    transcript: str
    confidence: float = 0.0
    pronunciation_assessment: Optional[Dict[str, float]] = None
    error: Optional[str] = None


# ============================================
# VISION MODELS
# ============================================

class VisionMetricsData(BaseModel):
    """Vision metrics data."""
    response_id: str
    eye_contact_score: float = Field(..., ge=0, le=10)
    head_stability_score: float = Field(..., ge=0, le=10)
    facial_confidence_score: float = Field(..., ge=0, le=10)
    overall_clarity_score: Optional[float] = None
    frames_analyzed: int = 0
    faces_detected: int = 0


# ============================================
# GENERIC RESPONSES
# ============================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)







