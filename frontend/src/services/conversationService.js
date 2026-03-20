// Conversation service for real-time conversation with AI
import { apiService } from './api';

export const conversationService = {
    // Process user's speech and get AI response (Speech-to-Text)
    processSpeech: async (audioBlob, assessmentId, stageId) => {
        const formData = new FormData();
        // Backend expects 'audio_file'
        formData.append('audio_file', audioBlob, 'recording.wav');
        // valid reference_text can be passed if we had the prompt text

        return await apiService.post('/api/v1/conversation/speech-to-text', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Generate AI response for a given context
    generateResponse: async (assessmentId, stageId, userMessage, context = {}) => {
        return await apiService.post('/api/v1/conversation/generate-response', {
            assessment_id: assessmentId,
            section: stageId, // Mapped to AssessmentSection enum
            user_message: userMessage,
            conversation_history: context.history || [], // Ensure history is passed if available
        });
    },

    // Get initial AI greeting for a stage
    getGreeting: async (stageId) => {
        return await apiService.get('/api/v1/conversation/greeting', {
            params: { section: stageId },
            timeout: 15000 // 15 seconds timeout — Azure TTS cold-start can take 8-10s
        });
    },

    // Get conversation history for an assessment
    // Backend endpoint not implemented yet
    getConversationHistory: async (assessmentId) => {
        // return await apiService.get(`/api/v1/conversation/${assessmentId}/history`);
        return { data: [] };
    },

    // Get stage prompt/question
    // Backend endpoint not implemented yet
    getStagePrompt: async (stageId) => {
        // return await apiService.get(`/api/v1/conversation/stages/${stageId}/prompt`);
        return { prompt: "Default prompt" };
    },

    // Get all stages configuration
    // Backend endpoint not implemented yet
    getStages: async () => {
        // return await apiService.get('/api/v1/conversation/stages');
        return [];
    },

    // Submit text response (for testing without audio)
    submitTextResponse: async (assessmentId, stageId, text) => {
        console.warn("submitTextResponse not implemented in backend");
        return { success: false };
    },
};

export default conversationService;
