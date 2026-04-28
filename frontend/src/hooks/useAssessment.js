// Assessment hook for managing assessment flow
import { useState, useCallback, useRef } from 'react';
import { assessmentService } from '../services/assessmentService';
import { conversationService } from '../services/conversationService';

// Assessment stages configuration
export const ASSESSMENT_STAGES = [
    {
        id: 'welcome',
        name: 'Welcome',
        description: 'Introduction to the assessment',
        duration: 30, // seconds
    },
    {
        id: 'introduction',
        name: 'Introduction',
        description: 'Tell us about yourself',
        duration: 120,
    },
    {
        id: 'reading',
        name: 'Reading',
        description: 'Read a passage aloud',
        duration: 180,
    },
    {
        id: 'listening',
        name: 'Listening',
        description: 'Listen and respond to questions',
        duration: 180,
    },
    {
        id: 'storytelling',
        name: 'Storytelling',
        description: 'Describe an image or tell a story',
        duration: 180,
    },
    {
        id: 'opinion',
        name: 'Opinion',
        description: 'Share your opinion on a topic',
        duration: 120,
    },
    {
        id: 'aim',
        name: 'Goals & Aspirations',
        description: 'Discuss your future goals',
        duration: 120,
    },
];

const useAssessment = () => {
    const [assessment, setAssessment] = useState(null);
    const [currentStageIndex, setCurrentStageIndex] = useState(0);
    const [stageResponses, setStageResponses] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isCompleted, setIsCompleted] = useState(false);
    const [score, setScore] = useState(null);

    const currentStage = ASSESSMENT_STAGES[currentStageIndex];
    const progress = ((currentStageIndex + 1) / ASSESSMENT_STAGES.length) * 100;
    const isFirstStage = currentStageIndex === 0;
    const isLastStage = currentStageIndex === ASSESSMENT_STAGES.length - 1;

    // Start a new assessment or resume existing one
    const startAssessment = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await assessmentService.startAssessment();

            setAssessment(data);

            // RESUME LOGIC: Check if there's a current_section in the backend response
            let initialStage = 0;
            if (data.current_section) {
                const stageIndex = ASSESSMENT_STAGES.findIndex(s => s.id === data.current_section);
                if (stageIndex !== -1) {
                    console.log(`[Assessment] Resuming from stage ${stageIndex + 1}/${ASSESSMENT_STAGES.length} (${data.current_section})`);
                    initialStage = stageIndex;
                }
            }

            setCurrentStageIndex(initialStage);
            setStageResponses({});
            setIsCompleted(false);
            setScore(null);
            return data;
        } catch (err) {
            console.error('[Assessment] Start error:', err.message || err);
            setError(err.message || 'Failed to start assessment');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    // Save response for current stage
    const saveStageResponse = useCallback(async (responseData) => {
        if (!assessment) {
            throw new Error('No active assessment');
        }

        // REMOVED setLoading(true) here to prevent full-screen loader during conversation.
        // The component handles local 'processing' state.
        setError(null);
        try {
            const response = await assessmentService.submitResponse(
                assessment.id,
                currentStage.id,
                responseData
            );

            setStageResponses(prev => ({
                ...prev,
                [currentStage.id]: response,
            }));

            return response;
        } catch (err) {
            setError(err.message || 'Failed to save response');
            throw err;
        }
        // finally block removed as we don't toggle loading
    }, [assessment, currentStage]);

    // Go to next stage
    const nextStage = useCallback(() => {
        if (!isLastStage) {
            setCurrentStageIndex(prev => prev + 1);
            setError(null);
        }
    }, [isLastStage]);

    // Go to previous stage
    const previousStage = useCallback(() => {
        if (!isFirstStage) {
            setCurrentStageIndex(prev => prev - 1);
            setError(null);
        }
    }, [isFirstStage]);

    // Go to specific stage
    const goToStage = useCallback((stageIndex) => {
        if (stageIndex >= 0 && stageIndex < ASSESSMENT_STAGES.length) {
            setCurrentStageIndex(stageIndex);
            setError(null);
        }
    }, []);

    // Complete the assessment
    const completeAssessment = useCallback(async () => {
        if (!assessment) {
            throw new Error('No active assessment');
        }

        setLoading(true);
        setError(null);
        try {
            const result = await assessmentService.completeAssessment(assessment.id);
            setIsCompleted(true);
            console.log(`[Assessment] Completed: ${assessment.id?.substring(0, 8)}`);

            // Try to get the score, but it may still be processing in the background
            try {
                const scoreData = await assessmentService.getAssessmentScore(assessment.id);
                setScore(scoreData);
                return { result, score: scoreData };
            } catch (scoreErr) {
                console.warn('[Assessment] Scores not ready yet (processing in background)');
                return { result, score: null };
            }
        } catch (err) {
            setError(err.message || 'Failed to complete assessment');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [assessment]);

    // Abandon the assessment (browser close, manual exit, etc.)
    const abandonAssessment = useCallback(async (reason = 'browser_closed') => {
        if (!assessment) return;
        const lastStage = currentStage?.id || 'unknown';
        console.warn(`[Assessment] Abandoning: ${assessment.id?.substring(0, 8)} at stage ${currentStageIndex + 1}/${ASSESSMENT_STAGES.length} (${lastStage}), reason=${reason}`);
        await assessmentService.abandonAssessment(assessment.id, reason, lastStage);
    }, [assessment, currentStage, currentStageIndex]);

    // Get AI response for current stage
    const getAIResponse = useCallback(async (userMessage, context = {}) => {
        if (!assessment) {
            throw new Error('No active assessment');
        }

        setLoading(true);
        setError(null);
        try {
            const response = await conversationService.generateResponse(
                assessment.id,
                currentStage.id,
                userMessage,
                context
            );
            return response;
        } catch (err) {
            setError(err.message || 'Failed to get AI response');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [assessment, currentStage]);

    // Reset assessment
    const resetAssessment = useCallback(() => {
        setAssessment(null);
        setCurrentStageIndex(0);
        setStageResponses({});
        setIsCompleted(false);
        setScore(null);
        setError(null);
    }, []);

    return {
        // State
        assessment,
        currentStage,
        currentStageIndex,
        stageResponses,
        loading,
        error,
        isCompleted,
        score,

        // Computed
        progress,
        isFirstStage,
        isLastStage,
        stages: ASSESSMENT_STAGES,
        totalStages: ASSESSMENT_STAGES.length,

        // Actions
        startAssessment,
        saveStageResponse,
        nextStage,
        previousStage,
        goToStage,
        completeAssessment,
        abandonAssessment,
        getAIResponse,
        resetAssessment,
        clearError: () => setError(null),
    };
};

export default useAssessment;
