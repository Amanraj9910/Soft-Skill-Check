-- ============================================================
-- Migration: Add assessment lifecycle tracking columns
-- Purpose:   Support heartbeat, abandonment, and stage tracking
-- Run this in: Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- Step 1: Add 'abandoned' to the status enum
-- (PostgreSQL enums cannot use IF NOT EXISTS, so we guard with a DO block)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_enum
    WHERE enumlabel = 'abandoned'
      AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assessment_status')
  ) THEN
    ALTER TYPE assessment_status ADD VALUE 'abandoned';
  END IF;
END
$$;

-- Step 2: Add heartbeat tracking (updated every 30s by the frontend)
ALTER TABLE assessments
  ADD COLUMN IF NOT EXISTS last_heartbeat_at TIMESTAMPTZ;

-- Step 3: Add abandonment reason (e.g., browser_closed, network_error, no_heartbeat)
ALTER TABLE assessments
  ADD COLUMN IF NOT EXISTS abandon_reason TEXT;

-- Step 4: Track the last stage the student completed before leaving
ALTER TABLE assessments
  ADD COLUMN IF NOT EXISTS last_completed_stage TEXT;

-- Step 5: Count of stages completed (0-6)
ALTER TABLE assessments
  ADD COLUMN IF NOT EXISTS stages_completed INTEGER DEFAULT 0;

-- Step 6: Index for the stale-checker query (find in_progress assessments with old heartbeats)
CREATE INDEX IF NOT EXISTS idx_assessments_stale_check
  ON assessments (status, last_heartbeat_at)
  WHERE status = 'in_progress';

-- Verify enum values
SELECT enumlabel FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'assessment_status')
ORDER BY enumsortorder;

-- Verify new columns
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'assessments'
  AND column_name IN ('last_heartbeat_at', 'abandon_reason', 'last_completed_stage', 'stages_completed');
