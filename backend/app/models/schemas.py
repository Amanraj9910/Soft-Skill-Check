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
    role: str = "user"  # 'user' or 'admin'
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
    confidence_score: float = Field(..., ge=0, le=20)
    hesitation_penalty: float = Field(..., ge=-10, le=0)
    storytelling_score: float = Field(..., ge=0, le=20)
    vision_clarity_score: float = Field(..., ge=0, le=10)
    total_score: Optional[float] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    overall_feedback: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)
    
    @validator('total_score', always=True)
    def calculate_total(cls, v, values):
        """Auto-calculate total score."""
        if v is not None:
            return v
        return (
            values.get('fluency_score', 0) +
            values.get('pronunciation_score', 0) +
            values.get('grammar_score', 0) +
            values.get('confidence_score', 0) +
            values.get('hesitation_penalty', 0) +
            values.get('storytelling_score', 0) +
            values.get('vision_clarity_score', 0)
        )


class ScoresResponse(BaseModel):
    """Complete scores response."""
    assessment_id: str
    fluency_score: Optional[float] = 0.0
    pronunciation_score: Optional[float] = 0.0
    grammar_score: Optional[float] = 0.0
    confidence_score: Optional[float] = 0.0
    hesitation_penalty: Optional[float] = 0.0
    storytelling_score: Optional[float] = 0.0
    vision_clarity_score: Optional[float] = 0.0
    total_score: Optional[float] = 0.0
    grade: Optional[AssessmentGrade] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    overall_feedback: Optional[str] = "Assessment completed."
    
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


# ============================================
# ADMIN MODELS
# ============================================

class AdminDashboardStats(BaseModel):
    """Admin dashboard statistics."""
    total_assessments: int
    total_users: int
    assessments_today: int
    average_score: float
    score_distribution: Dict[str, int]  # e.g. {'low': 10, 'medium': 20, 'high': 5}


class AdminRecentActivity(BaseModel):
    """Recent activity item."""
    id: str
    user_email: str
    user_name: Optional[str]
    type: str  # 'assessment_completed', 'user_signup', etc.
    timestamp: datetime
    details: Optional[str]


class AdminAssessmentListItem(BaseModel):
    """Assessment list item for admin."""
    id: str
    user_id: str
    user_email: str
    user_name: Optional[str]
    status: AssessmentStatus
    created_at: datetime
    completed_at: Optional[datetime]
    total_score: Optional[float]
    grade: Optional[AssessmentGrade]


class AdminAssessmentListResponse(BaseModel):
    """Response for admin assessment list."""
    assessments: List[AdminAssessmentListItem]
    total: int
    page: int
    limit: int


class AdminAssessmentDetail(BaseModel):
    """Detailed assessment view for admin."""
    assessment: AssessmentResponse
    user: UserProfile
    scores: Optional[ScoresResponse]
    responses: List[ResponseData]
    timeline: List[Dict[str, Any]]  # Stage-wise timeline data

