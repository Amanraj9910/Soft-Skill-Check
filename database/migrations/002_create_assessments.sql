-- ============================================
-- Migration: 002 - Create Assessments Table
-- Description: Main assessment tracking and results
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- Create assessment status enum
CREATE TYPE assessment_status AS ENUM ('in_progress', 'completed', 'cancelled');

-- Create grade enum
CREATE TYPE assessment_grade AS ENUM ('beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced', 'expert');

-- Create assessments table
CREATE TABLE IF NOT EXISTS public.assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    
    -- Status tracking
    status assessment_status DEFAULT 'in_progress' NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    
    -- Scores
    total_score DECIMAL(5,2) CHECK (total_score >= 0 AND total_score <= 100),
    grade assessment_grade,
    
    -- Audio storage
    full_audio_url TEXT,
    full_audio_duration INTEGER, -- in seconds
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    -- Assessment context
    user_agent TEXT,
    ip_address INET,
    
    -- Timing metrics
    total_duration_seconds INTEGER,
    
    CONSTRAINT valid_completion CHECK (
        (status = 'completed' AND completed_at IS NOT NULL AND total_score IS NOT NULL)
        OR (status != 'completed')
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON public.assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON public.assessments(status);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON public.assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_user_status ON public.assessments(user_id, status);

-- Create composite index for user's assessment history
CREATE INDEX IF NOT EXISTS idx_assessments_user_completed 
    ON public.assessments(user_id, completed_at DESC) 
    WHERE status = 'completed';

-- Create updated_at trigger
CREATE TRIGGER set_assessments_updated_at
    BEFORE UPDATE ON public.assessments
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Function to calculate total duration
CREATE OR REPLACE FUNCTION public.calculate_assessment_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.total_duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate duration
CREATE TRIGGER set_assessment_duration
    BEFORE INSERT OR UPDATE ON public.assessments
    FOR EACH ROW
    EXECUTE FUNCTION public.calculate_assessment_duration();

-- Function to update user stats when assessment completes
CREATE OR REPLACE FUNCTION public.update_user_stats_on_assessment()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status != 'completed') THEN
        UPDATE public.profiles
        SET 
            total_assessments = total_assessments + 1,
            average_score = (
                SELECT AVG(total_score)
                FROM public.assessments
                WHERE user_id = NEW.user_id AND status = 'completed'
            ),
            last_assessment_at = NEW.completed_at
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update user stats
CREATE TRIGGER update_user_stats_trigger
    AFTER INSERT OR UPDATE ON public.assessments
    FOR EACH ROW
    EXECUTE FUNCTION public.update_user_stats_on_assessment();

-- Add comments
COMMENT ON TABLE public.assessments IS 'Main assessment records with scores and metadata';
COMMENT ON COLUMN public.assessments.full_audio_url IS 'Azure Blob Storage URL for complete conversation';
COMMENT ON COLUMN public.assessments.total_score IS 'Final score out of 100';
