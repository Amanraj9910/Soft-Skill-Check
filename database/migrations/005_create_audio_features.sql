-- ============================================
-- Migration: 005 - Create Audio Features Table
-- Description: Extracted audio features for analysis
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- Create audio_features table
CREATE TABLE IF NOT EXISTS public.audio_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL REFERENCES public.assessment_responses(id) ON DELETE CASCADE,
    
    -- Volume metrics
    average_volume DECIMAL(6,2), -- in dB
    max_volume DECIMAL(6,2),
    min_volume DECIMAL(6,2),
    volume_variance DECIMAL(8,4),
    
    -- Pitch metrics
    average_pitch DECIMAL(8,2), -- in Hz
    max_pitch DECIMAL(8,2),
    min_pitch DECIMAL(8,2),
    pitch_variance DECIMAL(10,4),
    pitch_stability_score DECIMAL(5,2), -- 0-100
    
    -- Silence and pacing
    silence_ratio DECIMAL(5,4), -- 0-1 (percentage of silence)
    total_silence_duration DECIMAL(8,2), -- in seconds
    average_pause_duration DECIMAL(8,2), -- in seconds
    longest_pause_duration DECIMAL(8,2), -- in seconds
    
    -- Speech rate
    pace_variance DECIMAL(8,4),
    speech_tempo DECIMAL(6,2), -- syllables per second
    
    -- Energy metrics
    energy_level DECIMAL(6,2),
    energy_variance DECIMAL(8,4),
    
    -- Spectral features (for advanced analysis)
    spectral_centroid DECIMAL(10,4),
    spectral_rolloff DECIMAL(10,4),
    zero_crossing_rate DECIMAL(8,6),
    
    -- Raw feature data (JSONB for flexibility)
    raw_features JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    CONSTRAINT unique_response_features UNIQUE(response_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audio_features_response_id ON public.audio_features(response_id);
CREATE INDEX IF NOT EXISTS idx_audio_features_pitch_stability ON public.audio_features(pitch_stability_score DESC);

-- Create GIN index for JSONB querying
CREATE INDEX IF NOT EXISTS idx_audio_features_raw_features ON public.audio_features USING GIN(raw_features);

-- Updated_at trigger
CREATE TRIGGER set_audio_features_updated_at
    BEFORE UPDATE ON public.audio_features
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Function to calculate derived metrics
CREATE OR REPLACE FUNCTION public.calculate_audio_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate pitch stability (inverse of variance, normalized)
    IF NEW.pitch_variance IS NOT NULL THEN
        NEW.pitch_stability_score = GREATEST(0, 100 - (NEW.pitch_variance / 10));
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for derived metrics
CREATE TRIGGER set_audio_derived_metrics
    BEFORE INSERT OR UPDATE ON public.audio_features
    FOR EACH ROW
    EXECUTE FUNCTION public.calculate_audio_metrics();

-- Add comments
COMMENT ON TABLE public.audio_features IS 'Extracted audio signal features for confidence and fluency analysis';
COMMENT ON COLUMN public.audio_features.pitch_stability_score IS 'Calculated stability score from pitch variance';
COMMENT ON COLUMN public.audio_features.silence_ratio IS 'Ratio of silence to total duration';
COMMENT ON COLUMN public.audio_features.raw_features IS 'Full feature vector for ML models';
