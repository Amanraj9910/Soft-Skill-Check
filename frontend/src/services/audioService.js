// Audio service for audio-related operations
import { apiService } from './api';

export const audioService = {
    // Upload audio file to blob storage
    uploadAudio: async (audioBlob, assessmentId, stageId, audioType = 'response') => {
        const formData = new FormData();
        formData.append('file', audioBlob, `${audioType}_${stageId}.wav`);
        formData.append('assessment_id', assessmentId);
        formData.append('stage_id', stageId);
        formData.append('audio_type', audioType);

        return await apiService.post('/api/audio/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Get audio URL for playback
    getAudioUrl: async (assessmentId, stageId, audioType = 'response') => {
        return await apiService.get(`/api/audio/${assessmentId}/${stageId}`, {
            params: { audio_type: audioType },
        });
    },

    // Get TTS audio for text
    getTextToSpeech: async (text, voice = null) => {
        const response = await apiService.post('/api/audio/tts', {
            text,
            voice,
        }, {
            responseType: 'blob',
        });
        return response;
    },

    // Analyze audio features (loudness, pace, etc.)
    analyzeAudio: async (audioBlob) => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.wav');

        return await apiService.post('/api/audio/analyze', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // Convert audio format
    convertAudio: async (audioBlob, targetFormat = 'wav') => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio');
        formData.append('target_format', targetFormat);

        return await apiService.post('/api/audio/convert', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });
    },
};

export default audioService;
