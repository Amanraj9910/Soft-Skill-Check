-- ============================================
-- Migration: 008 - Security Fixes and RLS Optimization
-- Description: Fix mutable search_path in functions and optimize RLS policies
-- Author: AI English Assessment Platform
-- Date: 2026-01-25
-- ============================================

-- ============================================
-- PART 1: SECURITY FIXES - ADD SET search_path = ''
-- This prevents search path injection attacks
-- ============================================

-- Fix handle_updated_at function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix handle_new_user function
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- Fix calculate_assessment_duration function
CREATE OR REPLACE FUNCTION public.calculate_assessment_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.total_duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix update_user_stats_on_assessment function
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
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix calculate_wpm function
CREATE OR REPLACE FUNCTION public.calculate_wpm()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.word_count IS NOT NULL AND NEW.audio_duration IS NOT NULL AND NEW.audio_duration > 0 THEN
        NEW.words_per_minute = (NEW.word_count::DECIMAL / NEW.audio_duration::DECIMAL) * 60;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix calculate_word_count function
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
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix calculate_total_score function
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
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix sync_score_to_assessment function
CREATE OR REPLACE FUNCTION public.sync_score_to_assessment()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.assessments
    SET total_score = NEW.total_score
    WHERE id = NEW.assessment_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix calculate_audio_metrics function
CREATE OR REPLACE FUNCTION public.calculate_audio_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate pitch stability (inverse of variance, normalized)
    IF NEW.pitch_variance IS NOT NULL THEN
        NEW.pitch_stability_score = GREATEST(0, 100 - (NEW.pitch_variance / 10));
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix calculate_vision_ratios function
CREATE OR REPLACE FUNCTION public.calculate_vision_ratios()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate detection ratio
    IF NEW.frames_analyzed > 0 THEN
        NEW.detection_ratio = NEW.faces_detected::DECIMAL / NEW.frames_analyzed::DECIMAL;
    END IF;
    
    -- Calculate overall clarity score (weighted average)
    NEW.overall_clarity_score = (
        COALESCE(NEW.eye_contact_score, 0) * 0.3 +
        COALESCE(NEW.head_stability_score, 0) * 0.3 +
        COALESCE(NEW.facial_confidence_score, 0) * 0.2 +
        COALESCE(NEW.detection_ratio, 0) * 10 * 0.2
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix user_owns_assessment function
CREATE OR REPLACE FUNCTION public.user_owns_assessment(assessment_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.assessments
        WHERE id = assessment_uuid
        AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- ============================================
-- PART 2: RLS POLICY OPTIMIZATION
-- Wrap auth.uid() with (select ...) for better performance
-- ============================================

-- Drop and recreate PROFILES policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING ((select auth.uid()) = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING ((select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) = id);

-- Drop and recreate ASSESSMENTS policies
DROP POLICY IF EXISTS "Users can view own assessments" ON public.assessments;
CREATE POLICY "Users can view own assessments"
    ON public.assessments
    FOR SELECT
    USING ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can create own assessments" ON public.assessments;
CREATE POLICY "Users can create own assessments"
    ON public.assessments
    FOR INSERT
    WITH CHECK ((select auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own assessments" ON public.assessments;
CREATE POLICY "Users can update own assessments"
    ON public.assessments
    FOR UPDATE
    USING ((select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) = user_id);

-- Drop and recreate ASSESSMENT_RESPONSES policies
DROP POLICY IF EXISTS "Users can view own assessment responses" ON public.assessment_responses;
CREATE POLICY "Users can view own assessment responses"
    ON public.assessment_responses
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = (select auth.uid())
        )
    );

DROP POLICY IF EXISTS "Users can create own responses" ON public.assessment_responses;
CREATE POLICY "Users can create own responses"
    ON public.assessment_responses
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = (select auth.uid())
        )
    );

DROP POLICY IF EXISTS "Users can update own responses" ON public.assessment_responses;
CREATE POLICY "Users can update own responses"
    ON public.assessment_responses
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = (select auth.uid())
            AND assessments.status = 'in_progress'
        )
    );

-- Drop and recreate ASSESSMENT_SCORES policies
DROP POLICY IF EXISTS "Users can view own scores" ON public.assessment_scores;
CREATE POLICY "Users can view own scores"
    ON public.assessment_scores
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_scores.assessment_id
            AND assessments.user_id = (select auth.uid())
        )
    );

-- Drop and recreate AUDIO_FEATURES policies
DROP POLICY IF EXISTS "Users can view own audio features" ON public.audio_features;
CREATE POLICY "Users can view own audio features"
    ON public.audio_features
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessment_responses
            JOIN public.assessments ON assessments.id = assessment_responses.assessment_id
            WHERE assessment_responses.id = audio_features.response_id
            AND assessments.user_id = (select auth.uid())
        )
    );

-- Drop and recreate VISION_METRICS policies
DROP POLICY IF EXISTS "Users can view own vision metrics" ON public.vision_metrics;
CREATE POLICY "Users can view own vision metrics"
    ON public.vision_metrics
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessment_responses
            JOIN public.assessments ON assessments.id = assessment_responses.assessment_id
            WHERE assessment_responses.id = vision_metrics.response_id
            AND assessments.user_id = (select auth.uid())
        )
    );

-- ============================================
-- Add comments documenting the security fixes
-- ============================================

COMMENT ON FUNCTION public.handle_updated_at IS 'Trigger function to auto-update updated_at timestamp. Secured with SET search_path = empty.';
COMMENT ON FUNCTION public.handle_new_user IS 'Trigger function to auto-create profile on user signup. Secured with SECURITY DEFINER and SET search_path = empty.';
COMMENT ON FUNCTION public.user_owns_assessment IS 'Helper function to check assessment ownership. Secured with SECURITY DEFINER and SET search_path = empty.';
