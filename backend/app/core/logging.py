"""
Production-grade logging with dual output:
  1. JSON lines  — structured, machine-readable (Azure Monitor / ELK / Datadog)
  2. Human lines — colorized, scannable for dev console

Architecture
------------
* trace_id is generated per-request in middleware and stored in a ContextVar.
  All loggers automatically pick it up from context.
* event_log() is the single entry-point for business events.
* Standard Python logging still works — api_logger, ai_logger, db_logger,
  error_logger all emit via the same handler pipeline.

Log levels
----------
  DEBUG   — Internal detail, heartbeats, token verification (dev only)
  INFO    — Business events: ASSESSMENT_STARTED, STAGE_COMPLETED, etc.
  WARNING — Recoverable issues: slow queries, retries, abandoned sessions
  ERROR   — Failures needing attention
  CRITICAL— System-breaking failures
"""

import json
import logging
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import colorlog
    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False


# ---------------------------------------------------------------------------
# Trace ID context variable — set once per request in middleware
# ---------------------------------------------------------------------------
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


def set_trace_id(trace_id: str) -> None:
    _trace_id_var.set(trace_id)


def get_trace_id() -> str:
    return _trace_id_var.get()


# ---------------------------------------------------------------------------
# JSON formatter — emits one JSON object per log line
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """
    Emits structured JSON log lines compatible with Azure Monitor / ELK.

    Schema:
        {
            "timestamp": "2026-04-28T10:55:21Z",
            "level": "INFO",
            "event": "STAGE_COMPLETED",
            "trace_id": "a1b2c3d4-...",
            "logger": "soft_skill_check.assessment",
            "message": "human readable message",
            "metadata": { ... }
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        log: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "event": getattr(record, "event", record.levelname),
            "trace_id": get_trace_id(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach optional metadata dict if provided
        metadata = getattr(record, "metadata", None)
        if metadata:
            log["metadata"] = metadata

        # Attach error info for ERROR+ levels
        if record.exc_info:
            log["stack_trace"] = self.formatException(record.exc_info)
        elif record.levelno >= logging.ERROR:
            tb = traceback.format_stack()
            # Only include if it looks like a real exception context
            if any("raise" in line or "Error" in line for line in tb):
                log["stack_trace"] = "".join(tb[-6:])

        # Attach severity classification
        if record.levelno >= logging.CRITICAL:
            log["severity"] = "CRITICAL"
        elif record.levelno >= logging.ERROR:
            log["severity"] = "HIGH"
        elif record.levelno >= logging.WARNING:
            log["severity"] = "MEDIUM"
        else:
            log["severity"] = "LOW"

        return json.dumps(log, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Human formatter — short, colorized, scannable lines for dev console
# ---------------------------------------------------------------------------
_EVENT_WIDTH = 22  # pad event name to this width for alignment


class HumanFormatter(logging.Formatter):
    """
    Emits short human-readable lines:
        [10:55:21] STAGE_COMPLETE   Introduction (1/6)  user=Jatin
        [10:55:22] AI_RESPONSE      completeness=1/10  transition=False
    """

    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[41m",   # red bg
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        event = getattr(record, "event", record.levelname)
        msg = record.getMessage()

        line = f"[{ts}] {event:<{_EVENT_WIDTH}} {msg}"

        if self.use_colors and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, "")
            line = f"{color}{line}{self.RESET}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


# ---------------------------------------------------------------------------
# Dual handler — writes JSON to stderr, human text to stdout
# ---------------------------------------------------------------------------
class DualHandler(logging.Handler):
    """Routes each log record to both a JSON handler and a human handler."""

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self._json_handler = logging.StreamHandler(sys.stderr)
        self._json_handler.setFormatter(JsonFormatter())

        self._human_handler = logging.StreamHandler(sys.stdout)
        self._human_handler.setFormatter(HumanFormatter(use_colors=use_colors))

    def emit(self, record: logging.LogRecord) -> None:
        self._json_handler.emit(record)
        self._human_handler.emit(record)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_logging_configured = False


def configure_logging(
    log_level: str = "INFO",
    use_colors: bool = True,
) -> None:
    """
    Configure application-wide dual-output logging.
    Call once at startup.
    """
    global _logging_configured
    if _logging_configured:
        return

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(DualHandler(use_colors=use_colors))

    # ── Suppress third-party noise ──────────────────────────────────────────
    for name in (
        "httpx", "httpcore", "uvicorn.access",
        "azure.core", "azure.storage",
        "azure.core.pipeline.policies.http_logging_policy",
        "gunicorn.access", "gunicorn.error",
        "opentelemetry",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    _logging_configured = True


# ---------------------------------------------------------------------------
# Named loggers (same names as before — zero import changes in other files)
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"soft_skill_check.{name}")


api_logger   = get_logger("api")
error_logger = get_logger("error")
ai_logger    = get_logger("ai")
db_logger    = get_logger("db")


# ---------------------------------------------------------------------------
# Structured business-event helper
# ---------------------------------------------------------------------------
def event_log(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
    exc_info: bool = False,
) -> None:
    """
    Emit a structured business event through both JSON and human formatters.

    Usage:
        event_log(api_logger, logging.INFO, "ASSESSMENT_STARTED",
                  f"user=Jatin id={assessment_id[:8]}",
                  metadata={"user_id": user_id, "assessment_id": assessment_id})
    """
    extra: Dict[str, Any] = {"event": event}
    if metadata:
        extra["metadata"] = metadata
    logger.log(level, message, extra=extra, exc_info=exc_info)


# ---------------------------------------------------------------------------
# Backwards-compatible helpers (used by existing code)
# ---------------------------------------------------------------------------
def format_duration(milliseconds: float) -> str:
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    elif milliseconds < 60_000:
        return f"{milliseconds / 1000:.1f}s"
    else:
        return f"{milliseconds / 60_000:.1f}min"


def get_emoji(status_code: int) -> str:
    """Legacy helper kept for error_handlers.py compatibility."""
    if 200 <= status_code < 300:
        return "✅ "
    elif 400 <= status_code < 500:
        return "⚠️ "
    elif 500 <= status_code < 600:
        return "🔴 "
    return ""
