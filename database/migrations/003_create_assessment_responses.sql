-- ============================================
-- Migration: 003 - Create Assessment Responses Table
-- Description: Stores individual section responses and transcripts
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- Create section type enum
CREATE TYPE assessment_section AS ENUM (
    'introduction',
    'reading',
    'listening',
    'storytelling',
    'opinion',
    'aim'
);

-- Create assessment_responses table
CREATE TABLE IF NOT EXISTS public.assessment_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES public.assessments(id) ON DELETE CASCADE,
    
    -- Section information
    section assessment_section NOT NULL,
    section_order INTEGER NOT NULL,
    
    -- Question and response
    question_text TEXT NOT NULL,
    user_transcript TEXT,
    agent_transcript TEXT, -- What the AI agent said
    
    -- Audio storage
    audio_url TEXT,
    audio_duration INTEGER, -- in seconds
    
    -- Response metrics
    response_time_seconds INTEGER, -- Time taken to respond
    word_count INTEGER,
    words_per_minute DECIMAL(6,2),
    
    -- Speech analysis
    pause_count INTEGER DEFAULT 0,
    filler_word_count INTEGER DEFAULT 0,
    sentence_count INTEGER DEFAULT 0,
    
    -- Pronunciation data (from Azure)
    pronunciation_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    fluency_score DECIMAL(5,2),
    completeness_score DECIMAL(5,2),
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    CONSTRAINT unique_section_per_assessment UNIQUE(assessment_id, section)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_responses_assessment_id ON public.assessment_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_responses_section ON public.assessment_responses(section);
CREATE INDEX IF NOT EXISTS idx_responses_assessment_section ON public.assessment_responses(assessment_id, section_order);

-- Function to calculate words per minute
CREATE OR REPLACE FUNCTION public.calculate_wpm()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.word_count IS NOT NULL AND NEW.audio_duration IS NOT NULL AND NEW.audio_duration > 0 THEN
        NEW.words_per_minute = (NEW.word_count::DECIMAL / NEW.audio_duration::DECIMAL) * 60;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate WPM
CREATE TRIGGER set_wpm
    BEFORE INSERT OR UPDATE ON public.assessment_responses
    FOR EACH ROW
    EXECUTE FUNCTION public.calculate_wpm();

-- Function to calculate word count from transcript
CREATE OR REPLACE FUNCTION public.calculate_word_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_transcript IS NOT NULL THEN
        NEW.word_count = array_length(
            regexp_split_to_array(trim(NEW.user_transcript), '\s+'),
            1
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate word count
CREATE TRIGGER set_word_count
    BEFORE INSERT OR UPDATE ON public.assessment_responses
    FOR EACH ROW
    WHEN (NEW.user_transcript IS NOT NULL)
    EXECUTE FUNCTION public.calculate_word_count();

-- Add comments
COMMENT ON TABLE public.assessment_responses IS 'Individual section responses within an assessment';
COMMENT ON COLUMN public.assessment_responses.section IS 'Which stage of the conversation';
COMMENT ON COLUMN public.assessment_responses.words_per_minute IS 'Speaking pace calculated from word count and duration';
COMMENT ON COLUMN public.assessment_responses.pronunciation_score IS 'Azure Speech pronunciation assessment score';
