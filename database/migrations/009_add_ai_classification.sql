-- ============================================
-- Migration: 009 - Add AI Classification Column
-- Description: Adds missing ai_classification column to assessment_responses
-- Author: AI English Assessment Platform
-- Date: 2026-01-26
-- ============================================

ALTER TABLE public.assessment_responses 
ADD COLUMN IF NOT EXISTS ai_classification JSONB;

COMMENT ON COLUMN public.assessment_responses.ai_classification IS 'Full breakdown of AI scoring and analysis';
