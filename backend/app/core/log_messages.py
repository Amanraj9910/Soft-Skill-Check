"""
Human-readable log message templates.

All log messages should be generated through these helpers to ensure:
- Consistent formatting
- Natural language sentences
- Proper contextualization
- No hardcoded strings scattered across codebase
"""
from typing import Optional, Dict, Any


# ========================
# REQUEST/RESPONSE MESSAGES
# ========================

def request_received(method: str, path: str, client_host: Optional[str] = None) -> str:
    """Generate message for incoming request."""
    if client_host:
        return f"Request received: {method} {path} from {client_host}"
    return f"Request received: {method} {path}"


def request_completed(method: str, path: str, status_code: int, duration_ms: float) -> str:
    """Generate message for completed request."""
    from app.core.logging import format_duration, get_emoji
    
    emoji = get_emoji(status_code)
    duration_str = format_duration(duration_ms)
    
    if 200 <= status_code < 300:
        result = "successful"
    elif 400 <= status_code < 500:
        result = "failed with client error"
    elif 500 <= status_code < 600:
        result = "failed with server error"
    else:
        result = "completed"
    
    return f"{emoji}Request {result}: {method} {path} responded with {status_code} in {duration_str}"


# ========================
# ASSESSMENT MESSAGES
# ========================

def assessment_created(assessment_id: str, user_id: str) -> str:
    """Generate message for assessment creation."""
    return f"Assessment created successfully: id={assessment_id}, user={user_id}"


def assessment_not_found(assessment_id: str) -> str:
    """Generate message for missing assessment."""
    return f"Assessment not found: id={assessment_id}"


def assessment_completed(assessment_id: str, total_score: Optional[float] = None) -> str:
    """Generate message for assessment completion."""
    if total_score is not None:
        return f"Assessment completed: id={assessment_id}, total_score={total_score}"
    return f"Assessment completed: id={assessment_id}"


def assessment_cancelled(assessment_id: str) -> str:
    """Generate message for assessment cancellation."""
    return f"Assessment cancelled: id={assessment_id}"


# ========================
# AI PIPELINE MESSAGES
# ========================

def speech_to_text_started(audio_file: Optional[str] = None) -> str:
    """Generate message for STT operation start."""
    if audio_file:
        return f"Speech-to-text conversion started: audio_file={audio_file}"
    return "Speech-to-text conversion started"


def speech_to_text_completed(transcript: str, duration_ms: float, confidence: Optional[float] = None) -> str:
    """Generate message for successful STT."""
    from app.core.logging import format_duration
    
    duration_str = format_duration(duration_ms)
    words = len(transcript.split())
    
    if confidence:
        return f"Speech recognized successfully: {words} words transcribed in {duration_str}, confidence={confidence:.2f}"
    return f"Speech recognized successfully: {words} words transcribed in {duration_str}"


def speech_to_text_failed(reason: str) -> str:
    """Generate message for failed STT."""
    return f"Speech-to-text conversion failed: {reason}"


def text_to_speech_started(text_length: int) -> str:
    """Generate message for TTS operation start."""
    return f"Text-to-speech synthesis started: {text_length} characters to synthesize"


def text_to_speech_completed(audio_file: str, duration_ms: float) -> str:
    """Generate message for successful TTS."""
    from app.core.logging import format_duration
    
    duration_str = format_duration(duration_ms)
    return f"Text-to-speech synthesis completed in {duration_str}: audio={audio_file}"


def text_to_speech_failed(reason: str) -> str:
    """Generate message for failed TTS."""
    return f"Text-to-speech synthesis failed: {reason}"


def agent_response_generated(section: str, message_length: int, tokens_used: Optional[int] = None) -> str:
    """Generate message for AI agent response."""
    if tokens_used:
        return f"Agent response generated for section '{section}': {message_length} characters, {tokens_used} tokens used"
    return f"Agent response generated for section '{section}': {message_length} characters"


def pronunciation_assessment_enabled(reference_text: str) -> str:
    """Generate message for pronunciation assessment."""
    words = len(reference_text.split())
    return f"Pronunciation assessment enabled: reference text has {words} words"


# ========================
# SCORING MESSAGES
# ========================

def report_generation_started(assessment_id: str, response_count: int) -> str:
    """Generate message for report generation start."""
    return f"Generating AI assessment report: assessment_id={assessment_id}, responses={response_count}"


def report_generation_completed(assessment_id: str, total_score: float) -> str:
    """Generate message for report generation completion."""
    return f"AI assessment report generated successfully: assessment_id={assessment_id}, total_score={total_score}"


def report_generation_failed(assessment_id: str, reason: str) -> str:
    """Generate message for report generation failure."""
    return f"Failed to generate assessment report for {assessment_id}: {reason}"


def scores_saved(assessment_id: str, scores: Dict[str, Any]) -> str:
    """Generate message for score persistence."""
    total = scores.get('total_score', 0)
    return f"Assessment scores saved: assessment_id={assessment_id}, total_score={total}"


# ========================
# DATABASE MESSAGES
# ========================

def db_query_executed(table: str, operation: str, count: Optional[int] = None) -> str:
    """Generate message for database query."""
    if count is not None:
        return f"Database query executed: table={table}, operation={operation}, rows={count}"
    return f"Database query executed: table={table}, operation={operation}"


def db_connection_error(error: str) -> str:
    """Generate message for database connection error."""
    return f"Database connection failed: {error}"


def profile_created(user_id: str) -> str:
    """Generate message for profile creation."""
    return f"User profile created: user_id={user_id}"


def profile_not_found(user_id: str) -> str:
    """Generate message for missing profile."""
    return f"User profile not found for user_id={user_id}, creating new profile"


# ========================
# STORAGE MESSAGES
# ========================

def blob_uploaded(blob_name: str, size_bytes: int, container: str) -> str:
    """Generate message for blob upload."""
    size_kb = size_bytes / 1024
    return f"Audio blob uploaded: blob={blob_name}, size={size_kb:.1f}KB, container={container}"


def blob_upload_failed(reason: str) -> str:
    """Generate message for blob upload failure."""
    return f"Blob upload failed: {reason}"


def sas_url_generated(blob_name: str, expiry_hours: int) -> str:
    """Generate message for SAS URL generation."""
    return f"SAS URL generated for blob={blob_name}, expires_in={expiry_hours}h"


# ========================
# AUTHENTICATION MESSAGES
# ========================

def user_authenticated(user_id: str) -> str:
    """Generate message for successful authentication."""
    return f"User authenticated successfully: user_id={user_id}"


def authentication_failed(reason: str) -> str:
    """Generate message for authentication failure."""
    return f"Authentication failed: {reason}"


def invalid_token(detail: str) -> str:
    """Generate message for invalid token."""
    return f"Invalid authentication token: {detail}"


# ========================
# ERROR MESSAGES
# ========================

def validation_error(field: str, error: str) -> str:
    """Generate message for validation error."""
    return f"Validation failed for field '{field}': {error}"


def missing_required_field(field: str) -> str:
    """Generate message for missing field."""
    return f"Missing required field: {field}"


def invalid_format(field: str, expected_format: str) -> str:
    """Generate message for format error."""
    return f"Invalid format for {field}: expected {expected_format}"


def empty_data_error(data_type: str) -> str:
    """Generate message for empty data."""
    return f"Empty or null {data_type} provided"


def service_unavailable(service_name: str, reason: str) -> str:
    """Generate message for service unavailability."""
    return f"Service unavailable: {service_name} - {reason}"


def unexpected_error(operation: str, error: str) -> str:
    """Generate message for unexpected errors."""
    return f"Unexpected error during {operation}: {error}"


# ========================
# STARTUP/SHUTDOWN MESSAGES
# ========================

def app_starting(app_name: str, environment: str, debug: bool, host: str, port: int) -> str:
    """Generate message for application startup."""
    mode = "debug" if debug else "production"
    return f"Application starting: {app_name} | environment={environment} | mode={mode} | listening on {host}:{port}"


def app_ready(app_name: str) -> str:
    """Generate message when app is ready."""
    return f"✅ {app_name} is ready to accept requests"


def app_shutting_down(app_name: str) -> str:
    """Generate message for graceful shutdown."""
    return f"Application shutting down gracefully: {app_name}"


def config_loaded(config_items: Dict[str, Any]) -> str:
    """Generate message for configuration loading."""
    items = ", ".join(f"{k}={v}" for k, v in config_items.items())
    return f"Configuration loaded successfully: {items}"
