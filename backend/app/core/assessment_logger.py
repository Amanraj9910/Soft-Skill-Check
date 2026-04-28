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

from app.core.logging import get_logger, event_log

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
    """Return 'Stage N/6 (StageName)' or 'Stage ?/6 (name)' if not found."""
    try:
        idx = STAGE_ORDER.index(stage_name) + 1
        display = stage_name.replace("_", " ").title()
        return f"Stage {idx}/{TOTAL_STAGES} ({display})"
    except ValueError:
        return f"Stage ?/{TOTAL_STAGES} ({stage_name})"


class AssessmentEventLogger:
    """Structured assessment event logger — all events carry trace_id automatically."""

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def started(self, assessment_id: str, student_name: str, email: str = "") -> None:
        event_log(
            _logger, logging.INFO, "ASSESSMENT_STARTED",
            f"user={student_name!r}  id={assessment_id[:8]}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "email": email, "total_stages": TOTAL_STAGES},
        )

    def completed(
        self, assessment_id: str, student_name: str,
        stages_done: int, total_duration_sec: Optional[float] = None,
    ) -> None:
        dur = f"  duration={total_duration_sec:.0f}s" if total_duration_sec else ""
        event_log(
            _logger, logging.INFO, "ASSESSMENT_COMPLETED",
            f"user={student_name!r}  id={assessment_id[:8]}  stages={stages_done}/{TOTAL_STAGES}{dur}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "stages_done": stages_done, "duration_sec": total_duration_sec},
        )

    def abandoned(
        self, assessment_id: str, student_name: str,
        last_stage: str, reason: str,
    ) -> None:
        event_log(
            _logger, logging.WARNING, "ASSESSMENT_ABANDONED",
            f"user={student_name!r}  id={assessment_id[:8]}  {_stage_label(last_stage)}  reason={reason!r}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "last_stage": last_stage, "reason": reason},
        )

    def stale(
        self, assessment_id: str, student_name: str,
        last_stage: str, minutes_since_heartbeat: float,
    ) -> None:
        event_log(
            _logger, logging.WARNING, "ASSESSMENT_STALE",
            f"user={student_name!r}  id={assessment_id[:8]}  {_stage_label(last_stage)}"
            f"  no_heartbeat={minutes_since_heartbeat:.0f}min",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "last_stage": last_stage, "no_heartbeat_min": minutes_since_heartbeat},
        )

    # ── Stage events ─────────────────────────────────────────────────────────

    def stage_entered(self, assessment_id: str, student_name: str, stage_name: str) -> None:
        event_log(
            _logger, logging.INFO, "STAGE_ENTERED",
            f"user={student_name!r}  {_stage_label(stage_name)}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "stage": stage_name},
        )

    def stage_completed(
        self, assessment_id: str, student_name: str,
        stage_name: str, duration_sec: Optional[float] = None,
    ) -> None:
        dur = f"  duration={duration_sec:.0f}s" if duration_sec else ""
        event_log(
            _logger, logging.INFO, "STAGE_COMPLETED",
            f"user={student_name!r}  {_stage_label(stage_name)}{dur}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "stage": stage_name, "duration_sec": duration_sec},
        )

    def stage_error(
        self, assessment_id: str, student_name: str,
        stage_name: str, error_type: str, error_detail: str,
    ) -> None:
        event_log(
            _logger, logging.ERROR, "STAGE_ERROR",
            f"user={student_name!r}  {_stage_label(stage_name)}  {error_type}: {error_detail}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "stage": stage_name, "error_type": error_type, "detail": error_detail},
        )

    # ── User interaction events ───────────────────────────────────────────────

    def user_input_received(
        self, assessment_id: str, student_name: str,
        stage_name: str, transcript: str, word_count: int,
    ) -> None:
        preview = transcript[:60] + "..." if len(transcript) > 60 else transcript
        event_log(
            _logger, logging.INFO, "USER_INPUT_RECEIVED",
            f"user={student_name!r}  {_stage_label(stage_name)}  {word_count}w  \"{preview}\"",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "stage": stage_name, "word_count": word_count, "transcript_preview": preview},
        )

    def ai_response_generated(
        self, assessment_id: str, stage_name: str,
        completeness: int, transition: bool, next_section: Optional[str] = None,
    ) -> None:
        trans_str = f"→ {next_section}" if transition and next_section else "continuing"
        event_log(
            _logger, logging.INFO, "AI_RESPONSE_GENERATED",
            f"{_stage_label(stage_name)}  completeness={completeness}/10  {trans_str}",
            metadata={"assessment_id": assessment_id, "stage": stage_name,
                      "completeness": completeness, "transition": transition,
                      "next_section": next_section},
        )

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    def heartbeat(self, assessment_id: str, student_name: str, current_stage: str) -> None:
        """DEBUG level — completely silent in production INFO logging."""
        event_log(
            _logger, logging.DEBUG, "HEARTBEAT",
            f"user={student_name!r}  {_stage_label(current_stage)}",
            metadata={"assessment_id": assessment_id, "stage": current_stage},
        )

    # ── Scoring ───────────────────────────────────────────────────────────────

    def scoring_started(self, assessment_id: str, student_name: str) -> None:
        event_log(
            _logger, logging.INFO, "SCORING_STARTED",
            f"user={student_name!r}  id={assessment_id[:8]}",
            metadata={"assessment_id": assessment_id, "student_name": student_name},
        )

    def scoring_completed(
        self, assessment_id: str, student_name: str,
        total_score: float, grade: str,
    ) -> None:
        event_log(
            _logger, logging.INFO, "SCORING_COMPLETED",
            f"user={student_name!r}  id={assessment_id[:8]}  score={total_score}  grade={grade}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "total_score": total_score, "grade": grade},
        )

    def scoring_failed(self, assessment_id: str, student_name: str, error: str) -> None:
        event_log(
            _logger, logging.ERROR, "SCORING_FAILED",
            f"user={student_name!r}  id={assessment_id[:8]}  error={error!r}",
            metadata={"assessment_id": assessment_id, "student_name": student_name,
                      "error": error},
        )


# Singleton instance
assessment_event_logger = AssessmentEventLogger()

