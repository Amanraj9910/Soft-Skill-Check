"""
Custom domain-specific exceptions for the AI assessment platform.

These exceptions provide clear, actionable error messages and proper
HTTP status code mapping for API responses.
"""
from typing import Optional, Dict, Any


class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code for API response
            context: Additional contextual information
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.context = context or {}


# ========================
# ASSESSMENT EXCEPTIONS
# ========================

class AssessmentNotFoundError(BaseAppException):
    """Raised when an assessment cannot be found."""
    
    def __init__(self, assessment_id: str):
        super().__init__(
            message=f"Assessment not found: {assessment_id}",
            status_code=404,
            context={"assessment_id": assessment_id}
        )


class AssessmentAlreadyCompletedError(BaseAppException):
    """Raised when trying to modify a completed assessment."""
    
    def __init__(self, assessment_id: str):
        super().__init__(
            message=f"Assessment already completed: {assessment_id}",
            status_code=400,
            context={"assessment_id": assessment_id}
        )


class UnauthorizedAssessmentAccessError(BaseAppException):
    """Raised when user tries to access another user's assessment."""
    
    def __init__(self, assessment_id: str, user_id: str):
        super().__init__(
            message="Not authorized to access this assessment",
            status_code=403,
            context={"assessment_id": assessment_id, "user_id": user_id}
        )


# ========================
# AUDIO EXCEPTIONS
# ========================

class InvalidAudioDataError(BaseAppException):
    """Raised when audio data is invalid or corrupted."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid audio data: {reason}",
            status_code=400,
            context={"reason": reason}
        )


class EmptyAudioError(BaseAppException):
    """Raised when audio file is empty or too short."""
    
    def __init__(self):
        super().__init__(
            message="Audio file is empty or too short to process",
            status_code=400
        )


class AudioTooLongError(BaseAppException):
    """Raised when audio exceeds maximum duration."""
    
    def __init__(self, duration_seconds: int, max_duration: int):
        super().__init__(
            message=f"Audio duration ({duration_seconds}s) exceeds maximum allowed ({max_duration}s)",
            status_code=400,
            context={"duration": duration_seconds, "max_duration": max_duration}
        )


# ========================
# AI SERVICE EXCEPTIONS
# ========================

class AIServiceError(BaseAppException):
    """Raised when Azure OpenAI service fails."""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"AI service error during {operation}: {error}",
            status_code=500,
            context={"operation": operation, "error": error}
        )


class SpeechServiceError(BaseAppException):
    """Raised when Azure Speech service fails."""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Speech service error during {operation}: {error}",
            status_code=500,
            context={"operation": operation, "error": error}
        )


class TranscriptionFailedError(BaseAppException):
    """Raised when speech-to-text conversion fails."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Speech transcription failed: {reason}",
            status_code=500,
            context={"reason": reason}
        )


class SynthesisFailedError(BaseAppException):
    """Raised when text-to-speech synthesis fails."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Speech synthesis failed: {reason}",
            status_code=500,
            context={"reason": reason}
        )


# ========================
# STORAGE EXCEPTIONS
# ========================

class StorageServiceError(BaseAppException):
    """Raised when Azure Blob Storage operation fails."""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Storage service error during {operation}: {error}",
            status_code=500,
            context={"operation": operation, "error": error}
        )


class BlobUploadError(BaseAppException):
    """Raised when blob upload fails."""
    
    def __init__(self, blob_name: str, error: str):
        super().__init__(
            message=f"Failed to upload blob '{blob_name}': {error}",
            status_code=500,
            context={"blob_name": blob_name, "error": error}
        )


class BlobNotFoundError(BaseAppException):
    """Raised when blob cannot be found."""
    
    def __init__(self, blob_name: str):
        super().__init__(
            message=f"Blob not found: {blob_name}",
            status_code=404,
            context={"blob_name": blob_name}
        )


# ========================
# DATABASE EXCEPTIONS
# ========================

class DatabaseConnectionError(BaseAppException):
    """Raised when database connection fails."""
    
    def __init__(self, error: str):
        super().__init__(
            message=f"Database connection failed: {error}",
            status_code=503,
            context={"error": error}
        )


class DatabaseOperationError(BaseAppException):
    """Raised when database operation fails."""
    
    def __init__(self, operation: str, table: str, error: str):
        super().__init__(
            message=f"Database operation failed: {operation} on {table}",
            status_code=500,
            context={"operation": operation, "table": table, "error": error}
        )


# ========================
# VALIDATION EXCEPTIONS
# ========================

class ValidationError(BaseAppException):
    """Raised when business logic validation fails."""
    
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            status_code=400,
            context={"field": field, "reason": reason}
        )


class MissingRequiredFieldError(BaseAppException):
    """Raised when a required field is missing."""
    
    def __init__(self, field: str):
        super().__init__(
            message=f"Missing required field: {field}",
            status_code=400,
            context={"field": field}
        )


class InvalidFormatError(BaseAppException):
    """Raised when data format is invalid."""
    
    def __init__(self, field: str, expected_format: str):
        super().__init__(
            message=f"Invalid format for '{field}': expected {expected_format}",
            status_code=400,
            context={"field": field, "expected_format": expected_format}
        )


# ========================
# AUTHENTICATION EXCEPTIONS
# ========================

class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"Authentication failed: {reason}",
            status_code=401,
            context={"reason": reason}
        )


class InvalidTokenError(BaseAppException):
    """Raised when authentication token is invalid."""
    
    def __init__(self, detail: str):
        super().__init__(
            message=f"Invalid authentication token: {detail}",
            status_code=401,
            context={"detail": detail}
        )


class UserNotFoundError(BaseAppException):
    """Raised when user cannot be found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User not found: {user_id}",
            status_code=404,
            context={"user_id": user_id}
        )
