"""
Structured assessment lifecycle logger.

Produces clear, grep-friendly, actionable log lines for every assessment event.
Every log line includes: student name, email, assessment ID, stage number, event type.

Usage:
    from app.core.assessment_logger import assessment_event_logger
    assessment_event_logger.started(assessment_id, student_name, email)
    assessment_event_logger.stage_entered(assessment_id, student_name, stage_num, stage_name)

Log format:
    📋 [EVENT_TYPE] student="John Doe" | email="john@ex.com" | assessment=a3f2b1c8 | stage=3/7 (Storytelling)
"""
import logging
from typing import Optional

from app.core.logging import get_logger

# Dedicated logger for assessment lifecycle events
_logger = get_logger("assessment")

# Stage mapping — canonical order used across the platform
STAGE_ORDER = [
    "introduction",   # Stage 1
    "reading",         # Stage 2
    "listening",       # Stage 3
    "storytelling",    # Stage 4
    "opinion",         # Stage 5
    "aim",             # Stage 6
]
TOTAL_STAGES = len(STAGE_ORDER)


def _stage_label(stage_name: str) -> str:
    """Return 'Stage N/6 (StageName)' or 'unknown' if not found."""
    try:
        idx = STAGE_ORDER.index(stage_name) + 1
        display = stage_name.replace("_", " ").title()
        return f"Stage {idx}/{TOTAL_STAGES} ({display})"
    except ValueError:
        return f"Stage ?/{TOTAL_STAGES} ({stage_name})"


def _stage_number(stage_name: str) -> int:
    """Return 1-based stage number, 0 if unknown."""
    try:
        return STAGE_ORDER.index(stage_name) + 1
    except ValueError:
        return 0


def _fmt(
    event: str,
    assessment_id: str,
    student_name: str = "Unknown",
    email: str = "",
    stage_name: str = "",
    extra: str = "",
) -> str:
    """Build a structured log line."""
    parts = [f'📋 [{event}]']
    parts.append(f'student="{student_name}"')
    if email:
        parts.append(f'email="{email}"')
    parts.append(f'assessment={assessment_id[:8]}')
    if stage_name:
        parts.append(_stage_label(stage_name))
    if extra:
        parts.append(extra)
    return " | ".join(parts)


class AssessmentEventLogger:
    """Structured assessment event logger."""

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------
    def started(
        self,
        assessment_id: str,
        student_name: str,
        email: str = "",
    ) -> None:
        """Log assessment creation."""
        _logger.info(
            _fmt("ASSESSMENT_STARTED", assessment_id, student_name, email,
                 extra=f"total_stages={TOTAL_STAGES}")
        )

    def completed(
        self,
        assessment_id: str,
        student_name: str,
        stages_done: int,
        total_duration_sec: Optional[float] = None,
    ) -> None:
        """Log successful assessment completion."""
        dur = f"duration={total_duration_sec:.0f}s" if total_duration_sec else ""
        _logger.info(
            _fmt("ASSESSMENT_COMPLETED", assessment_id, student_name,
                 extra=f"stages={stages_done}/{TOTAL_STAGES} | {dur}".rstrip(" | "))
        )

    def abandoned(
        self,
        assessment_id: str,
        student_name: str,
        last_stage: str,
        reason: str,
    ) -> None:
        """Log assessment abandonment (browser closed, network error, etc.)."""
        _logger.warning(
            _fmt("ASSESSMENT_ABANDONED", assessment_id, student_name,
                 stage_name=last_stage,
                 extra=f'reason="{reason}"')
        )

    def stale(
        self,
        assessment_id: str,
        student_name: str,
        last_stage: str,
        minutes_since_heartbeat: float,
    ) -> None:
        """Log stale assessment (no heartbeat for extended period)."""
        _logger.warning(
            _fmt("ASSESSMENT_STALE", assessment_id, student_name,
                 stage_name=last_stage,
                 extra=f"no_heartbeat={minutes_since_heartbeat:.0f}min")
        )

    # ------------------------------------------------------------------
    # Stage events
    # ------------------------------------------------------------------
    def stage_entered(
        self,
        assessment_id: str,
        student_name: str,
        stage_name: str,
    ) -> None:
        """Log entry into a new assessment stage."""
        _logger.info(
            _fmt("STAGE_ENTERED", assessment_id, student_name,
                 stage_name=stage_name)
        )

    def stage_completed(
        self,
        assessment_id: str,
        student_name: str,
        stage_name: str,
        duration_sec: Optional[float] = None,
    ) -> None:
        """Log successful completion of a stage."""
        dur = f"duration={duration_sec:.0f}s" if duration_sec else ""
        _logger.info(
            _fmt("STAGE_COMPLETED", assessment_id, student_name,
                 stage_name=stage_name, extra=dur)
        )

    def stage_error(
        self,
        assessment_id: str,
        student_name: str,
        stage_name: str,
        error_type: str,
        error_detail: str,
    ) -> None:
        """Log an error during a specific stage."""
        _logger.error(
            _fmt("STAGE_ERROR", assessment_id, student_name,
                 stage_name=stage_name,
                 extra=f'error_type="{error_type}" | detail="{error_detail}"')
        )

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------
    def heartbeat(
        self,
        assessment_id: str,
        student_name: str,
        current_stage: str,
    ) -> None:
        """Log heartbeat received (DEBUG level to reduce noise)."""
        _logger.debug(
            _fmt("HEARTBEAT", assessment_id, student_name,
                 stage_name=current_stage)
        )

    # ------------------------------------------------------------------
    # Scoring / finalization
    # ------------------------------------------------------------------
    def scoring_started(
        self,
        assessment_id: str,
        student_name: str,
    ) -> None:
        """Log scoring process started."""
        _logger.info(
            _fmt("SCORING_STARTED", assessment_id, student_name)
        )

    def scoring_completed(
        self,
        assessment_id: str,
        student_name: str,
        total_score: float,
        grade: str,
    ) -> None:
        """Log scoring completion."""
        _logger.info(
            _fmt("SCORING_COMPLETED", assessment_id, student_name,
                 extra=f"score={total_score} | grade={grade}")
        )

    def scoring_failed(
        self,
        assessment_id: str,
        student_name: str,
        error: str,
    ) -> None:
        """Log scoring failure."""
        _logger.error(
            _fmt("SCORING_FAILED", assessment_id, student_name,
                 extra=f'error="{error}"')
        )


# Singleton instance
assessment_event_logger = AssessmentEventLogger()
