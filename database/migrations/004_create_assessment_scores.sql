-- ============================================
-- Migration: 004 - Create Assessment Scores Table
-- Description: Detailed category-wise scoring and feedback
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- Create assessment_scores table
CREATE TABLE IF NOT EXISTS public.assessment_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL UNIQUE REFERENCES public.assessments(id) ON DELETE CASCADE,
    
    -- Category scores (out of their max points)
    fluency_score DECIMAL(5,2) CHECK (fluency_score >= 0 AND fluency_score <= 20),
    pronunciation_score DECIMAL(5,2) CHECK (pronunciation_score >= 0 AND pronunciation_score <= 10),
    grammar_score DECIMAL(5,2) CHECK (grammar_score >= 0 AND grammar_score <= 10),
    confidence_score DECIMAL(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 20),
    hesitation_penalty DECIMAL(5,2) CHECK (hesitation_penalty >= -10 AND hesitation_penalty <= 0),
    storytelling_score DECIMAL(5,2) CHECK (storytelling_score >= 0 AND storytelling_score <= 20),
    vision_clarity_score DECIMAL(5,2) CHECK (vision_clarity_score >= 0 AND vision_clarity_score <= 10),
    
    -- Calculated total (should match assessments.total_score)
    total_score DECIMAL(5,2) CHECK (total_score >= 0 AND total_score <= 100),
    
    -- Grade (beginner, intermediate, advanced, etc)
    grade TEXT,
    
    -- Detailed feedback
    strengths TEXT[], -- Array of strength points
    weaknesses TEXT[], -- Array of weakness points
    recommendations TEXT[], -- Array of improvement suggestions
    
    -- AI-generated summary
    overall_feedback TEXT,
    
    -- Raw AI response (for debugging/reprocessing)
    details JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scores_assessment_id ON public.assessment_scores(assessment_id);
CREATE INDEX IF NOT EXISTS idx_scores_total_score ON public.assessment_scores(total_score DESC);

-- Function to calculate total score
CREATE OR REPLACE FUNCTION public.calculate_total_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_score = COALESCE(NEW.fluency_score, 0)
                    + COALESCE(NEW.pronunciation_score, 0)
                    + COALESCE(NEW.grammar_score, 0)
                    + COALESCE(NEW.confidence_score, 0)
                    + COALESCE(NEW.hesitation_penalty, 0)
                    + COALESCE(NEW.storytelling_score, 0)
                    + COALESCE(NEW.vision_clarity_score, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate total
CREATE TRIGGER set_total_score
    BEFORE INSERT OR UPDATE ON public.assessment_scores
    FOR EACH ROW
    EXECUTE FUNCTION public.calculate_total_score();

-- Updated_at trigger
CREATE TRIGGER set_scores_updated_at
    BEFORE UPDATE ON public.assessment_scores
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Function to sync score to assessments table
CREATE OR REPLACE FUNCTION public.sync_score_to_assessment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.assessments
    SET total_score = NEW.total_score
    WHERE id = NEW.assessment_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to sync scores
CREATE TRIGGER sync_assessment_score
    AFTER INSERT OR UPDATE ON public.assessment_scores
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_score_to_assessment();

-- Add comments
COMMENT ON TABLE public.assessment_scores IS 'Detailed scoring breakdown for each assessment';
COMMENT ON COLUMN public.assessment_scores.fluency_score IS 'Score out of 20 for speaking fluency';
COMMENT ON COLUMN public.assessment_scores.hesitation_penalty IS 'Negative score (0 to -10) for hesitation';
COMMENT ON COLUMN public.assessment_scores.strengths IS 'Array of identified strengths';
COMMENT ON COLUMN public.assessment_scores.raw_ai_response IS 'Full GPT response for debugging';
