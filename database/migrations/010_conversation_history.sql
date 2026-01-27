-- Migration: 010 - Add Conversation History
-- Description: Adds JSONB column to store full conversation history for a section response

ALTER TABLE public.assessment_responses 
ADD COLUMN IF NOT EXISTS conversation_history JSONB DEFAULT '[]';

COMMENT ON COLUMN public.assessment_responses.conversation_history IS 'Full conversation turns (user + agent) for this section';
