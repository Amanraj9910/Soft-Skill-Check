-- ============================================
-- Migration: 006 - Create Vision Metrics Table
-- Description: MediaPipe-derived vision analysis metrics
-- Author: AI English Assessment Platform
-- Date: 2026-01-23
-- ============================================

-- Create vision_metrics table
CREATE TABLE IF NOT EXISTS public.vision_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL REFERENCES public.assessment_responses(id) ON DELETE CASCADE,
    
    -- Face detection consistency
    frames_analyzed INTEGER DEFAULT 0,
    faces_detected INTEGER DEFAULT 0,
    detection_ratio DECIMAL(5,4), -- faces_detected / frames_analyzed
    
    -- Eye contact metrics
    eye_contact_score DECIMAL(5,2), -- 0-10
    average_gaze_direction DECIMAL(8,4), -- angle in degrees
    gaze_stability DECIMAL(5,2), -- 0-10
    
    -- Head position and movement
    head_stability_score DECIMAL(5,2), -- 0-10
    average_head_tilt DECIMAL(8,4), -- degrees
    average_head_pan DECIMAL(8,4), -- degrees
    excessive_movement_count INTEGER DEFAULT 0,
    
    -- Facial confidence indicators
    facial_confidence_score DECIMAL(5,2), -- 0-10
    smile_frequency DECIMAL(5,4), -- ratio of frames with smile
    
    -- Distance and framing
    average_face_size DECIMAL(8,4), -- normalized 0-1
    face_size_variance DECIMAL(8,4),
    proper_framing_ratio DECIMAL(5,4), -- ratio of well-framed shots
    
    -- Overall clarity score (combination of metrics)
    overall_clarity_score DECIMAL(5,2) CHECK (overall_clarity_score >= 0 AND overall_clarity_score <= 10),
    
    -- Raw detection data (for debugging/reprocessing)
    raw_detections JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    CONSTRAINT unique_response_metrics UNIQUE(response_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_vision_metrics_response_id ON public.vision_metrics(response_id);
CREATE INDEX IF NOT EXISTS idx_vision_metrics_clarity_score ON public.vision_metrics(overall_clarity_score DESC);

-- Create GIN index for JSONB
CREATE INDEX IF NOT EXISTS idx_vision_metrics_raw_detections ON public.vision_metrics USING GIN(raw_detections);

-- Updated_at trigger
CREATE TRIGGER set_vision_metrics_updated_at
    BEFORE UPDATE ON public.vision_metrics
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Function to calculate detection ratio
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
$$ LANGUAGE plpgsql;

-- Trigger for ratio calculations
CREATE TRIGGER set_vision_ratios
    BEFORE INSERT OR UPDATE ON public.vision_metrics
    FOR EACH ROW
    EXECUTE FUNCTION public.calculate_vision_ratios();

-- Add comments
COMMENT ON TABLE public.vision_metrics IS 'MediaPipe-derived vision analysis for body language scoring';
COMMENT ON COLUMN public.vision_metrics.detection_ratio IS 'Ratio of frames where face was detected';
COMMENT ON COLUMN public.vision_metrics.eye_contact_score IS 'Estimated eye contact quality (0-10)';
COMMENT ON COLUMN public.vision_metrics.overall_clarity_score IS 'Weighted combination of all vision metrics';
COMMENT ON COLUMN public.vision_metrics.raw_detections IS 'Full MediaPipe detection data for reprocessing';
