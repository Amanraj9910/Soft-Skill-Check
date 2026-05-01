"""
Stale assessment checker — background task.

Runs every 5 minutes to find assessments stuck in 'in_progress' with no
heartbeat for over 5 minutes, and marks them as 'abandoned'.

This is the safety net that catches "ghost" assessments when the frontend's
beforeunload/sendBeacon fail (e.g., browser crash, network drop).
"""
import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.logging import get_logger
from app.core.assessment_logger import assessment_event_logger

logger = get_logger("stale_checker")

# Configuration
CHECK_INTERVAL_SECONDS = 300       # Run every 5 minutes
STALE_THRESHOLD_MINUTES = 30       # Mark stale after 30 min without heartbeat (increased from 5)
FALLBACK_STALE_HOURS = 2           # If no heartbeat column, use created_at > 2 hours


class StaleAssessmentChecker:
    """Background task that detects and marks stale assessments."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        # Default to True so it runs. If users want to disable it on certain workers, they can use an env var.
        # Idempotent DB operations make it safe for multiple workers to run it concurrently.
        self._is_master_process = os.environ.get('DISABLE_STALE_CHECKER') != 'true'

    async def start(self):
        """Start the periodic checker."""
        if self._running:
            return
            
        if not self._is_master_process:
            logger.info("Stale assessment checker explicitly disabled via env var")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Stale assessment checker started in master process (interval=%ds, threshold=%dmin)",
                     CHECK_INTERVAL_SECONDS, STALE_THRESHOLD_MINUTES)

    async def stop(self):
        """Stop the periodic checker gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stale assessment checker stopped")

    async def _run_loop(self):
        """Main loop — runs check, then sleeps."""
        while self._running:
            try:
                await self._check_stale_assessments()
            except Exception as e:
                logger.error("Stale checker iteration failed: %s", str(e))
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def _check_stale_assessments(self):
        """
        Query for in_progress assessments with stale heartbeats and mark them abandoned.
        
        Two strategies:
        1. If last_heartbeat_at exists and is older than threshold → stale
        2. If last_heartbeat_at is NULL and created_at is older than fallback → stale
           (handles assessments created before the heartbeat feature was deployed)
        """
        from app.services.supabase_client import get_supabase_service
        
        supabase = get_supabase_service()
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        fallback_cutoff = now - timedelta(hours=FALLBACK_STALE_HOURS)

        # Strategy 1: Has heartbeat but it's old
        try:
            heartbeat_stale = await asyncio.to_thread(
                lambda: supabase.admin_client.table("assessments")
                    .select("id, user_id, last_heartbeat_at, last_completed_stage, current_section")
                    .eq("status", "in_progress")
                    .lt("last_heartbeat_at", stale_cutoff.isoformat())
                    .execute()
            )
            stale_rows = heartbeat_stale.data or []
        except Exception as e:
            logger.warning("Heartbeat stale query failed (column may not exist yet): %s", str(e))
            stale_rows = []

        # Strategy 2: No heartbeat at all, but created long ago
        try:
            no_heartbeat = await asyncio.to_thread(
                lambda: supabase.admin_client.table("assessments")
                    .select("id, user_id, created_at, current_section")
                    .eq("status", "in_progress")
                    .is_("last_heartbeat_at", "null")
                    .lt("created_at", fallback_cutoff.isoformat())
                    .execute()
            )
            fallback_rows = no_heartbeat.data or []
        except Exception as e:
            logger.warning("Fallback stale query failed: %s", str(e))
            fallback_rows = []

        total_stale = len(stale_rows) + len(fallback_rows)
        if total_stale == 0:
            return  # Nothing to do — stay silent

        logger.info("Found %d stale assessments (%d heartbeat-expired, %d no-heartbeat)",
                     total_stale, len(stale_rows), len(fallback_rows))

        # Mark each as abandoned
        for row in stale_rows:
            await self._mark_abandoned(supabase, row, reason="no_heartbeat")

        for row in fallback_rows:
            await self._mark_abandoned(supabase, row, reason="no_heartbeat_legacy")

    async def _mark_abandoned(self, supabase, row: dict, reason: str):
        """Update a single assessment to abandoned status and log it."""
        assessment_id = row["id"]
        user_id = row.get("user_id", "unknown")
        last_stage = row.get("last_completed_stage") or row.get("current_section") or "unknown"

        try:
            # Resolve student name for logging
            identity = await supabase.get_student_identity(user_id)
            student_name = identity.get("full_name", "Unknown")

            # Calculate minutes since last heartbeat
            heartbeat_str = row.get("last_heartbeat_at")
            if heartbeat_str:
                try:
                    last_hb = datetime.fromisoformat(heartbeat_str.replace("Z", "+00:00"))
                    minutes_stale = (datetime.now(timezone.utc) - last_hb).total_seconds() / 60
                except (ValueError, TypeError):
                    minutes_stale = STALE_THRESHOLD_MINUTES
            else:
                minutes_stale = FALLBACK_STALE_HOURS * 60

            # Log it
            assessment_event_logger.stale(
                assessment_id=assessment_id,
                student_name=student_name,
                last_stage=last_stage,
                minutes_since_heartbeat=minutes_stale,
            )

            # Update DB
            await asyncio.to_thread(
                lambda: supabase.admin_client.table("assessments")
                    .update({
                        "status": "abandoned",
                        "abandon_reason": reason,
                        "last_completed_stage": last_stage,
                    })
                    .eq("id", assessment_id)
                    .eq("status", "in_progress")  # Guard: only update if still in_progress
                    .execute()
            )

            assessment_event_logger.abandoned(
                assessment_id=assessment_id,
                student_name=student_name,
                last_stage=last_stage,
                reason=reason,
            )

        except Exception as e:
            logger.error("Failed to mark assessment %s as abandoned: %s",
                         assessment_id[:8], str(e))


# Singleton
stale_checker = StaleAssessmentChecker()