// Assessment service for managing assessments
import { apiService, API_TIMEOUTS } from './api';

const STAGE_CONFIG = {
    introduction: { section: 'introduction', order: 1 },
    reading: { section: 'reading', order: 2 },
    listening: { section: 'listening', order: 3 },
    storytelling: { section: 'storytelling', order: 4 },
    opinion: { section: 'opinion', order: 5 },
    aim: { section: 'aim', order: 6 },
};

export const assessmentService = {
    // Start a new assessment
    startAssessment: async () => {
        try {
            const response = await apiService.post('/api/v1/assessments/', {});
            console.log('[Assessment] Started:', response.id?.substring(0, 8));
            return response;
        } catch (error) {
            console.error('[Assessment] Start failed:', error.message || error);
            throw error;
        }
    },

    // Get assessment by ID
    getAssessment: async (assessmentId) => {
        return await apiService.get(`/api/v1/assessments/${assessmentId}`);
    },

    // Get user's assessment history
    getAssessmentHistory: async (limit = 10, offset = 0) => {
        return await apiService.get('/api/v1/assessments/', {
            params: { limit, offset },
        });
    },

    // Submit a response for a specific stage
    submitResponse: async (assessmentId, stageId, responseData) => {
        // Skip calling backend for 'welcome' stage as it's not a recorded section
        if (stageId === 'welcome') {
            return { success: true, message: 'Welcome stage skipped' };
        }

        const stageConfig = STAGE_CONFIG[stageId];
        if (!stageConfig) {
            console.warn(`[Assessment] Unknown stage: ${stageId}, skipping.`);
            return null;
        }

        try {
            // 1. Create response record
            const createPayload = {
                assessment_id: assessmentId,
                section: stageConfig.section,
                section_order: stageConfig.order,
                question_text: responseData.prompt || "Assessment Section",
            };

            const responseRecord = await apiService.post('/api/v1/responses/', createPayload);
            const responseId = responseRecord.id;
            console.log(`[Assessment] Stage ${stageConfig.order}/6 (${stageId}) response created: ${responseId?.substring(0, 8)}`);

            // 2. Upload Audio if exists
            if (responseData.audio) {
                const audioSize = responseData.audio.size || 0;

                if (audioSize === 0) {
                    console.warn(`[Assessment] Stage ${stageConfig.order}/6 (${stageId}): Empty audio, skipping upload`);
                } else {
                    const formData = new FormData();
                    formData.append('audio_file', responseData.audio, 'recording.wav');

                    try {
                        const aiResponse = await apiService.post(`/api/v1/responses/${responseId}/audio`, formData, {
                            headers: { 'Content-Type': 'multipart/form-data' },
                            timeout: API_TIMEOUTS.audio
                        });
                        console.log(`[Assessment] Stage ${stageConfig.order}/6 (${stageId}) audio processed`);
                        return { ...responseRecord, ...aiResponse };
                    } catch (audioErr) {
                        console.error(`[Assessment] Stage ${stageConfig.order}/6 (${stageId}) audio FAILED:`, audioErr.message || audioErr);
                    }
                }
            }

            // 3. Save Vision Metrics if exists
            if (responseData.metrics) {
                const metricsPayload = {
                    eye_contact_score: responseData.metrics.eyeContact || 0,
                    head_stability_score: responseData.metrics.headStability || 0,
                    facial_confidence_score: 0,
                    overall_clarity_score: 0,
                    frames_analyzed: 0,
                    faces_detected: 0
                };
                try {
                    await apiService.post(`/api/v1/responses/${responseId}/vision`, metricsPayload);
                } catch (visionErr) {
                    console.warn(`[Assessment] Vision metrics save failed for stage ${stageConfig.order}:`, visionErr.message);
                }
            }

            return responseRecord;
        } catch (error) {
            console.error(`[Assessment] Stage ${stageConfig?.order || '?'}/6 (${stageId}) submit FAILED:`, error.message || error);
            throw error;
        }
    },

    // Complete the assessment
    completeAssessment: async (assessmentId) => {
        return await apiService.post(`/api/v1/assessments/${assessmentId}/complete`);
    },

    // Abandon the assessment (called on browser close / network failure)
    abandonAssessment: async (assessmentId, reason, lastStage) => {
        try {
            return await apiService.post(`/api/v1/assessments/${assessmentId}/abandon`, {
                reason,
                last_stage: lastStage,
            });
        } catch (err) {
            // Best-effort — don't crash if this fails (browser may be closing)
            console.error('[Assessment] Abandon notification failed:', err.message);
        }
    },

    // Send heartbeat to keep assessment alive
    sendHeartbeat: async (assessmentId, currentStage) => {
        try {
            return await apiService.post(`/api/v1/assessments/${assessmentId}/heartbeat`, {
                current_stage: currentStage,
            });
        } catch (err) {
            // Best-effort — don't crash for heartbeat failures
            console.warn('[Assessment] Heartbeat failed:', err.message);
        }
    },

    // Get full scoring results (including breakdown)
    getAssessmentScore: async (assessmentId) => {
        return await apiService.get(`/api/v1/scoring/${assessmentId}`);
    },

    // Trigger score calculation
    calculateScore: async (assessmentId) => {
        return await apiService.post(`/api/v1/scoring/${assessmentId}/calculate`);
    },

    // Get assessment statistics for the user
    getUserStats: async () => {
        return await apiService.get('/api/v1/users/stats');
    },

    // Delete an assessment
    deleteAssessment: async (assessmentId) => {
        return await apiService.delete(`/api/v1/assessments/${assessmentId}`);
    },
};

export default assessmentService;
