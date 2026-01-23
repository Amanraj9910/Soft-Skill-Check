-- ============================================
-- Migration: 007 - Setup Row Level Security (RLS)
-- Description: Enable RLS and create security policies
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- ============================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audio_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vision_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================
-- PROFILES POLICIES
-- ============================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Profiles are created automatically via trigger (no INSERT policy needed for users)

-- ============================================
-- ASSESSMENTS POLICIES
-- ============================================

-- Users can view their own assessments
CREATE POLICY "Users can view own assessments"
    ON public.assessments
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own assessments
CREATE POLICY "Users can create own assessments"
    ON public.assessments
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own in-progress assessments
CREATE POLICY "Users can update own assessments"
    ON public.assessments
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users cannot delete assessments (for data integrity)
-- Only admins can delete via service role

-- ============================================
-- ASSESSMENT RESPONSES POLICIES
-- ============================================

-- Users can view responses for their own assessments
CREATE POLICY "Users can view own assessment responses"
    ON public.assessment_responses
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = auth.uid()
        )
    );

-- Users can create responses for their own assessments
CREATE POLICY "Users can create own responses"
    ON public.assessment_responses
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = auth.uid()
        )
    );

-- Users can update responses for their own in-progress assessments
CREATE POLICY "Users can update own responses"
    ON public.assessment_responses
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_responses.assessment_id
            AND assessments.user_id = auth.uid()
            AND assessments.status = 'in_progress'
        )
    );

-- ============================================
-- ASSESSMENT SCORES POLICIES
-- ============================================

-- Users can view scores for their own assessments
CREATE POLICY "Users can view own scores"
    ON public.assessment_scores
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessments
            WHERE assessments.id = assessment_scores.assessment_id
            AND assessments.user_id = auth.uid()
        )
    );

-- Scores are created by backend (service role only)
-- Users cannot directly insert or update scores

-- ============================================
-- AUDIO FEATURES POLICIES
-- ============================================

-- Users can view audio features for their own responses
CREATE POLICY "Users can view own audio features"
    ON public.audio_features
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessment_responses
            JOIN public.assessments ON assessments.id = assessment_responses.assessment_id
            WHERE assessment_responses.id = audio_features.response_id
            AND assessments.user_id = auth.uid()
        )
    );

-- Audio features are created by backend (service role only)

-- ============================================
-- VISION METRICS POLICIES
-- ============================================

-- Users can view vision metrics for their own responses
CREATE POLICY "Users can view own vision metrics"
    ON public.vision_metrics
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.assessment_responses
            JOIN public.assessments ON assessments.id = assessment_responses.assessment_id
            WHERE assessment_responses.id = vision_metrics.response_id
            AND assessments.user_id = auth.uid()
        )
    );

-- Vision metrics are created by backend (service role only)

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant select permissions to authenticated users (filtered by RLS)
GRANT SELECT ON public.profiles TO authenticated;
GRANT SELECT ON public.assessments TO authenticated;
GRANT SELECT ON public.assessment_responses TO authenticated;
GRANT SELECT ON public.assessment_scores TO authenticated;
GRANT SELECT ON public.audio_features TO authenticated;
GRANT SELECT ON public.vision_metrics TO authenticated;

-- Grant insert/update for user-writable tables
GRANT INSERT, UPDATE ON public.assessments TO authenticated;
GRANT INSERT, UPDATE ON public.assessment_responses TO authenticated;
GRANT UPDATE ON public.profiles TO authenticated;

-- Grant all to service role (backend)
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.assessments TO service_role;
GRANT ALL ON public.assessment_responses TO service_role;
GRANT ALL ON public.assessment_scores TO service_role;
GRANT ALL ON public.audio_features TO service_role;
GRANT ALL ON public.vision_metrics TO service_role;

-- ============================================
-- HELPER FUNCTIONS FOR POLICIES
-- ============================================

-- Function to check if user owns an assessment
CREATE OR REPLACE FUNCTION public.user_owns_assessment(assessment_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.assessments
        WHERE id = assessment_uuid
        AND user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comments
COMMENT ON POLICY "Users can view own profile" ON public.profiles IS 'Users can only view their own profile';
COMMENT ON POLICY "Users can view own assessments" ON public.assessments IS 'Users can only view their own assessments';
COMMENT ON FUNCTION public.user_owns_assessment IS 'Helper function to check assessment ownership';
