// Assessment service for managing assessments
import { apiService } from './api';

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
        console.log('🚀 [AssessmentService] Starting assessment request...');
        console.log('🕐 [AssessmentService] Timestamp:', new Date().toISOString());
        try {
            console.log('📤 [AssessmentService] Calling POST /api/v1/assessments/');
            const response = await apiService.post('/api/v1/assessments/', {
                // Optional: user_agent, ip_address
            });
            console.log('✅ [AssessmentService] Assessment created:', response);
            return response;
        } catch (error) {
            console.error('❌ [AssessmentService] Assessment creation failed:', error);
            console.error('❌ [AssessmentService] Error details:', JSON.stringify(error, null, 2));
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
        console.log('📤 [AssessmentService] submitResponse called:', { assessmentId, stageId });

        // Skip calling backend for 'welcome' stage as it's not a recorded section
        if (stageId === 'welcome') {
            console.log('⏭️ [AssessmentService] Skipping welcome stage');
            return { success: true, message: 'Welcome stage skipped' };
        }

        const stageConfig = STAGE_CONFIG[stageId];
        if (!stageConfig) {
            console.warn(`⚠️ [AssessmentService] Unknown stage: ${stageId}, skipping submission.`);
            return null;
        }

        try {
            // 1. Create response record
            console.log('📝 [AssessmentService] Creating response record...');
            const createPayload = {
                assessment_id: assessmentId,
                section: stageConfig.section,
                section_order: stageConfig.order,
                question_text: responseData.prompt || "Assessment Section",
            };

            const responseRecord = await apiService.post('/api/v1/responses/', createPayload);
            const responseId = responseRecord.id;
            console.log('✅ [AssessmentService] Response record created:', responseId);

            // 2. Upload Audio if exists
            if (responseData.audio) {
                const audioSize = responseData.audio.size || 0;
                console.log(`🎤 [AssessmentService] Uploading audio: ${(audioSize / 1024).toFixed(2)}KB`);

                if (audioSize === 0) {
                    console.warn('⚠️ [AssessmentService] Audio blob is empty, skipping audio upload');
                } else {
                    const formData = new FormData();
                    formData.append('audio_file', responseData.audio, 'recording.wav');

                    try {
                        const aiResponse = await apiService.post(`/api/v1/responses/${responseId}/audio`, formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });
                        console.log('✅ [AssessmentService] Audio processed successfully:', {
                            transcript: aiResponse.transcript?.substring(0, 50) + '...',
                            ai_audio_url: aiResponse.ai_audio_url,
                            hasScores: !!aiResponse.scores
                        });

                        // Return the enriched response with AI data
                        return { ...responseRecord, ...aiResponse };
                    } catch (audioErr) {
                        console.error('❌ [AssessmentService] Audio processing failed:', audioErr);
                        // Don't fail the whole response, just log and continue
                    }
                }
            } else {
                console.log('ℹ️ [AssessmentService] No audio to upload');
            }

            // 3. Save Vision Metrics if exists
            if (responseData.metrics) {
                console.log('👁️ [AssessmentService] Saving vision metrics...');
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
                    console.log('✅ [AssessmentService] Vision metrics saved');
                } catch (visionErr) {
                    console.warn('⚠️ [AssessmentService] Vision metrics save failed:', visionErr);
                }
            }

            return responseRecord;
        } catch (error) {
            console.error("❌ [AssessmentService] Error submitting response:", error);
            throw error;
        }
    },

    // Complete the assessment
    completeAssessment: async (assessmentId) => {
        return await apiService.post(`/api/v1/assessments/${assessmentId}/complete`);
    },

    // Get full scoring results (including breakdown)
    getAssessmentScore: async (assessmentId) => {
        // Try/catch wrapper to handle missing scores (404) gracefully if needed
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
