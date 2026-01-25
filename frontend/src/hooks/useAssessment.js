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

    // Start a new assessment
    const startAssessment = useCallback(async () => {
        console.log('🎯 [useAssessment] startAssessment called');
        console.log('🕐 [useAssessment] Timestamp:', new Date().toISOString());
        setLoading(true);
        setError(null);
        try {
            console.log('📞 [useAssessment] Calling assessmentService.startAssessment()...');
            const data = await assessmentService.startAssessment();
            console.log('✅ [useAssessment] Assessment data received:', data);
            setAssessment(data);
            setCurrentStageIndex(0);
            setStageResponses({});
            setIsCompleted(false);
            setScore(null);
            console.log('✅ [useAssessment] State updated, returning data');
            return data;
        } catch (err) {
            console.error('❌ [useAssessment] startAssessment error:', err);
            setError(err.message || 'Failed to start assessment');
            throw err;
        } finally {
            console.log('🏁 [useAssessment] startAssessment completed, setting loading=false');
            setLoading(false);
        }
    }, []);

    // Save response for current stage
    const saveStageResponse = useCallback(async (responseData) => {
        if (!assessment) {
            throw new Error('No active assessment');
        }

        setLoading(true);
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
        } finally {
            setLoading(false);
        }
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

            // Get the score
            const scoreData = await assessmentService.getAssessmentScore(assessment.id);
            setScore(scoreData);

            return { result, score: scoreData };
        } catch (err) {
            setError(err.message || 'Failed to complete assessment');
            throw err;
        } finally {
            setLoading(false);
        }
    }, [assessment]);

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
        getAIResponse,
        resetAssessment,
        clearError: () => setError(null),
    };
};

export default useAssessment;
