"""
Human-readable log message templates with emoji categories.

All log messages should be generated through these helpers to ensure:
- Consistent formatting with emoji visual markers
- Natural language sentences
- Scannable at a glance
- No hardcoded strings scattered across codebase

Emoji Legend:
  📥  Request incoming        ✅  Success / Ready
  ⚠️  Client error (4xx)      🔴  Server error (5xx)
  🚀  Startup                 🛑  Shutdown
  🔐  Auth success            🚫  Auth failure
  📝  Assessment flow         🤖  AI / Agent
  🎤  Speech-to-text          🔊  Text-to-speech
  🗄️  Database                ☁️  Storage / Blob
  📊  Scoring / Reports       ⚙️  Config
  ❌  Error / Failure
"""
from typing import Optional, Dict, Any


# ========================
# REQUEST/RESPONSE MESSAGES
# ========================

def request_received(method: str, path: str, client_host: Optional[str] = None) -> str:
    """Generate message for incoming request."""
    if client_host:
        return f"📥 {method} {path} from {client_host}"
    return f"📥 {method} {path}"


def request_completed(method: str, path: str, status_code: int, duration_ms: float) -> str:
    """Generate message for completed request."""
    from app.core.logging import format_duration

    duration_str = format_duration(duration_ms)

    if 200 <= status_code < 300:
        return f"✅ {method} {path} → {status_code} in {duration_str}"
    elif 400 <= status_code < 500:
        return f"⚠️ {method} {path} → {status_code} in {duration_str}"
    elif 500 <= status_code < 600:
        return f"🔴 {method} {path} → {status_code} in {duration_str}"
    else:
        return f"  {method} {path} → {status_code} in {duration_str}"


# ========================
# ASSESSMENT MESSAGES
# ========================

def assessment_created(assessment_id: str, user_id: str) -> str:
    """Generate message for assessment creation."""
    return f"📝 Assessment created: id={assessment_id}, user={user_id}"


def assessment_not_found(assessment_id: str) -> str:
    """Generate message for missing assessment."""
    return f"⚠️ Assessment not found: id={assessment_id}"


def assessment_completed(assessment_id: str, total_score: Optional[float] = None) -> str:
    """Generate message for assessment completion."""
    if total_score is not None:
        return f"📝 Assessment completed: id={assessment_id}, score={total_score}"
    return f"📝 Assessment completed: id={assessment_id}"


def assessment_cancelled(assessment_id: str) -> str:
    """Generate message for assessment cancellation."""
    return f"🛑 Assessment cancelled: id={assessment_id}"


# ========================
# AI PIPELINE MESSAGES
# ========================

def speech_to_text_started(audio_file: Optional[str] = None) -> str:
    """Generate message for STT operation start."""
    if audio_file:
        return f"🎤 Speech-to-text started: {audio_file}"
    return "🎤 Speech-to-text started"


def speech_to_text_completed(transcript: str, duration_ms: float, confidence: Optional[float] = None) -> str:
    """Generate message for successful STT."""
    from app.core.logging import format_duration

    duration_str = format_duration(duration_ms)
    words = len(transcript.split())

    if confidence:
        return f"🎤 Speech recognized: {words} words in {duration_str} (confidence={confidence:.2f})"
    return f"🎤 Speech recognized: {words} words in {duration_str}"


def speech_to_text_failed(reason: str) -> str:
    """Generate message for failed STT."""
    return f"❌ Speech-to-text failed: {reason}"


def text_to_speech_started(text_length: int) -> str:
    """Generate message for TTS operation start."""
    return f"🔊 Text-to-speech started: {text_length} chars"


def text_to_speech_completed(audio_file: str, duration_ms: float) -> str:
    """Generate message for successful TTS."""
    from app.core.logging import format_duration

    duration_str = format_duration(duration_ms)
    return f"🔊 Text-to-speech done in {duration_str}: {audio_file}"


def text_to_speech_failed(reason: str) -> str:
    """Generate message for failed TTS."""
    return f"❌ Text-to-speech failed: {reason}"


def agent_response_generated(section: str, message_length: int, tokens_used: Optional[int] = None) -> str:
    """Generate message for AI agent response."""
    if tokens_used:
        return f"🤖 Agent response for '{section}': {message_length} chars, {tokens_used} tokens"
    return f"🤖 Agent response for '{section}': {message_length} chars"


def pronunciation_assessment_enabled(reference_text: str) -> str:
    """Generate message for pronunciation assessment."""
    words = len(reference_text.split())
    return f"🎤 Pronunciation assessment enabled: {words} words"


# ========================
# SCORING MESSAGES
# ========================

def report_generation_started(assessment_id: str, response_count: int) -> str:
    """Generate message for report generation start."""
    return f"📊 Generating report: assessment={assessment_id}, responses={response_count}"


def report_generation_completed(assessment_id: str, total_score: float) -> str:
    """Generate message for report generation completion."""
    return f"📊 Report generated: assessment={assessment_id}, total_score={total_score}"


def report_generation_failed(assessment_id: str, reason: str) -> str:
    """Generate message for report generation failure."""
    return f"❌ Report generation failed for {assessment_id}: {reason}"


def scores_saved(assessment_id: str, scores: Dict[str, Any]) -> str:
    """Generate message for score persistence."""
    total = scores.get('total_score', 0)
    return f"📊 Scores saved: assessment={assessment_id}, total={total}"


# ========================
# DATABASE MESSAGES
# ========================

def db_query_executed(table: str, operation: str, count: Optional[int] = None) -> str:
    """Generate message for database query."""
    if count is not None:
        return f"🗄️ DB {operation} on {table}: {count} rows"
    return f"🗄️ DB {operation} on {table}"


def db_connection_error(error: str) -> str:
    """Generate message for database connection error."""
    return f"❌ Database connection failed: {error}"


def profile_created(user_id: str) -> str:
    """Generate message for profile creation."""
    return f"🗄️ Profile created: user={user_id}"


def profile_not_found(user_id: str) -> str:
    """Generate message for missing profile."""
    return f"🗄️ Profile not found for user={user_id}, creating new"


# ========================
# STORAGE MESSAGES
# ========================

def blob_uploaded(blob_name: str, size_bytes: int, container: str) -> str:
    """Generate message for blob upload."""
    size_kb = size_bytes / 1024
    return f"☁️ Blob uploaded: {blob_name} ({size_kb:.1f}KB) → {container}"


def blob_upload_failed(reason: str) -> str:
    """Generate message for blob upload failure."""
    return f"❌ Blob upload failed: {reason}"


def sas_url_generated(blob_name: str, expiry_hours: int) -> str:
    """Generate message for SAS URL generation."""
    return f"☁️ SAS URL generated: {blob_name}, expires in {expiry_hours}h"


# ========================
# AUTHENTICATION MESSAGES
# ========================

def user_authenticated(user_id: str) -> str:
    """Generate message for successful authentication."""
    return f"🔐 User authenticated: user_id={user_id}"


def authentication_failed(reason: str) -> str:
    """Generate message for authentication failure."""
    return f"🚫 Authentication failed: {reason}"


def invalid_token(detail: str) -> str:
    """Generate message for invalid token."""
    return f"🚫 Invalid token: {detail}"


# ========================
# ERROR MESSAGES
# ========================

def validation_error(field: str, error: str) -> str:
    """Generate message for validation error."""
    return f"⚠️ Validation failed for '{field}': {error}"


def missing_required_field(field: str) -> str:
    """Generate message for missing field."""
    return f"⚠️ Missing required field: {field}"


def invalid_format(field: str, expected_format: str) -> str:
    """Generate message for format error."""
    return f"⚠️ Invalid format for {field}: expected {expected_format}"


def empty_data_error(data_type: str) -> str:
    """Generate message for empty data."""
    return f"⚠️ Empty or null {data_type} provided"


def service_unavailable(service_name: str, reason: str) -> str:
    """Generate message for service unavailability."""
    return f"❌ Service unavailable: {service_name} — {reason}"


def unexpected_error(operation: str, error: str) -> str:
    """Generate message for unexpected errors."""
    return f"❌ Unexpected error during {operation}: {error}"


# ========================
# STARTUP/SHUTDOWN MESSAGES
# ========================

def app_starting(app_name: str, environment: str, debug: bool, host: str, port: int) -> str:
    """Generate message for application startup."""
    mode = "debug" if debug else "production"
    return f"🚀 {app_name} starting | env={environment} | mode={mode} | {host}:{port}"


def app_ready(app_name: str) -> str:
    """Generate message when app is ready."""
    return f"✅ {app_name} is ready to accept requests"


def app_shutting_down(app_name: str) -> str:
    """Generate message for graceful shutdown."""
    return f"🛑 {app_name} shutting down gracefully"


def config_loaded(config_items: Dict[str, Any]) -> str:
    """Generate message for configuration loading."""
    items = ", ".join(f"{k}={v}" for k, v in config_items.items())
    return f"⚙️ Config loaded: {items}"
