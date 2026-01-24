// Assessment Page - Interview Assessment Theme
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import useAssessment, { ASSESSMENT_STAGES } from '../hooks/useAssessment';
import useAudioRecorder from '../hooks/useAudioRecorder';
import useVideoCapture from '../hooks/useVideoCapture';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';

// Stage Components
import WelcomeStage from '../components/assessment/WelcomeStage';
import IntroductionStage from '../components/assessment/IntroductionStage';
import ReadingStage from '../components/assessment/ReadingStage';
import ListeningStage from '../components/assessment/ListeningStage';
import StorytellingStage from '../components/assessment/StorytellingStage';
import OpinionStage from '../components/assessment/OpinionStage';
import AimStage from '../components/assessment/AimStage';

const Assessment = () => {
    const navigate = useNavigate();
    const {
        assessment, currentStage, currentStageIndex, progress,
        loading, error, isLastStage, startAssessment, saveStageResponse,
        nextStage, completeAssessment, resetAssessment
    } = useAssessment();

    const { isRecording, formattedDuration, audioBlob, startRecording, stopRecording, resetRecording } = useAudioRecorder();
    const { videoRef, isStreaming, metrics, startStream, stopStream } = useVideoCapture();

    const [status, setStatus] = useState('idle'); // idle, ready, recording, processing, completed
    const [messages, setMessages] = useState([]); // Keep for specific feedback if needed, mostly unused now
    const [showPermissionDialog, setShowPermissionDialog] = useState(false);

    // Initialize assessment
    useEffect(() => {
        const init = async () => {
            try {
                await startAssessment();
                // Don't show permission dialog immediately, wait for user to click Start in WelcomeStage
            } catch (err) {
                console.error('Failed to start assessment:', err);
            }
        };
        init();
        return () => resetAssessment();
    }, []);

    const handleWelcomeStart = () => {
        setShowPermissionDialog(true);
    };

    // Request permissions
    const handleGrantPermissions = async () => {
        try {
            await startStream();
            setShowPermissionDialog(false);
            setStatus('ready');
            // Move from Welcome to Introduction
            nextStage();
        } catch (err) {
            console.error("Error accessing media devices:", err);
            // Handle error state appropriately
        }
    };

    const handleStartRecording = async () => {
        resetRecording();
        await startRecording();
        setStatus('recording');
    };

    const handleStopRecording = async () => {
        stopRecording();
        setStatus('processing');

        // Simulate processing
        setTimeout(async () => {
            try {
                if (audioBlob) {
                    await saveStageResponse({ audio: audioBlob, metrics });
                }

                if (isLastStage) {
                    const result = await completeAssessment();
                    navigate(`/results/${assessment?.id || 'demo'}`);
                } else {
                    nextStage();
                    setStatus('ready');
                }
            } catch (err) {
                console.error('Error processing response:', err);
                setStatus('ready');
            }
        }, 1500);
    };

    const handleSkipStage = () => {
        if (isLastStage) {
            navigate(`/results/${assessment?.id || 'demo'}`);
        } else {
            nextStage();
            setStatus('ready');
        }
    };

    const renderStageContent = () => {
        if (!currentStage) return null;

        switch (currentStage.id) {
            case 'welcome':
                return <WelcomeStage onStart={handleWelcomeStart} />;
            case 'introduction':
                return <IntroductionStage />;
            case 'reading':
                return <ReadingStage />;
            case 'listening':
                return <ListeningStage />;
            case 'storytelling':
                return <StorytellingStage />;
            case 'opinion':
                return <OpinionStage />;
            case 'aim':
                return <AimStage />;
            default:
                return (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        Unknown Stage: {currentStage.name}
                    </div>
                );
        }
    };

    const isWelcomeStage = currentStage?.id === 'welcome';
    const showControls = !isWelcomeStage && !loading;

    if (loading && !assessment) {
        return <LoadingSpinner fullScreen text="Preparing your assessment..." />;
    }

    return (
        <div className="min-h-screen bg-gray-50 pt-20 pb-12">
            {/* Permission Dialog */}
            <AnimatePresence>
                {showPermissionDialog && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl"
                        >
                            <div className="text-center">
                                <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <h2 className="text-xl font-bold text-gray-900 mb-2">Enable Camera & Mic</h2>
                                <p className="text-gray-600 mb-8 text-sm">
                                    We need access to your camera and microphone to assess your speaking and confidence.
                                </p>
                                <div className="flex flex-col gap-3">
                                    <Button fullWidth onClick={handleGrantPermissions} size="lg">Allow Access</Button>
                                    <Button variant="secondary" fullWidth onClick={() => { setShowPermissionDialog(false); }} size="md">Cancel</Button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="container mx-auto px-4 max-w-7xl h-full">
                <div className="grid lg:grid-cols-12 gap-6 h-[calc(100vh-140px)] min-h-[600px]">

                    {/* Left Panel - Video Feed & Metrics (Only show if not welcome stage) */}
                    <div className={`lg:col-span-4 flex flex-col gap-6 transition-all duration-500 ${isWelcomeStage ? 'hidden lg:hidden' : 'block'}`}>
                        <Card padding="none" className="overflow-hidden bg-black rounded-2xl shadow-xl flex-shrink-0">
                            <div className="relative aspect-[4/3] bg-gray-900">
                                <video ref={videoRef} autoPlay muted playsInline className="w-full h-full object-cover transform scale-x-[-1]" />
                                {!isStreaming && (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 gap-2">
                                        <svg className="w-12 h-12 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3l18 18" />
                                        </svg>
                                        <span className="text-sm">Camera Off</span>
                                    </div>
                                )}
                                {isRecording && (
                                    <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-red-600/90 backdrop-blur-sm rounded-full shadow-lg border border-white/10 animate-pulse">
                                        <div className="w-2 h-2 bg-white rounded-full" />
                                        <span className="text-white text-xs font-bold tracking-wide uppercase">REC</span>
                                        <span className="text-white text-xs font-mono ml-1">{formattedDuration}</span>
                                    </div>
                                )}
                            </div>

                            {/* Live Metrics overlay */}
                            <div className="p-5 bg-white border-t border-gray-100">
                                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                                    Live Analysis
                                </h3>
                                <div className="space-y-4">
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-medium text-gray-500">Eye Contact</span>
                                            <span className="text-xs font-bold text-gray-900">{metrics.eyeContact}%</span>
                                        </div>
                                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                            <motion.div
                                                className="h-full bg-green-500 rounded-full"
                                                animate={{ width: `${metrics.eyeContact}%` }}
                                                transition={{ type: "spring", stiffness: 50 }}
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs font-medium text-gray-500">Head Stability</span>
                                            <span className="text-xs font-bold text-gray-900">{metrics.headStability}%</span>
                                        </div>
                                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                            <motion.div
                                                className="h-full bg-blue-500 rounded-full"
                                                animate={{ width: `${metrics.headStability}%` }}
                                                transition={{ type: "spring", stiffness: 50 }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Card>

                        {/* Status Card or Helpful Tips could go here */}
                        <Card padding="md" className="bg-blue-50 border-blue-100 hidden lg:block">
                            <div className="flex gap-3">
                                <span className="text-2xl">💡</span>
                                <div>
                                    <h4 className="font-bold text-blue-900 text-sm">Pro Tip</h4>
                                    <p className="text-blue-700 text-xs mt-1">Speak clearly and maintain eye contact with the camera for the best score.</p>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Right Panel - Stage Content (Full width on Welcome, 8 cols otherwise) */}
                    <div className={`${isWelcomeStage ? 'col-span-12' : 'lg:col-span-8'} flex flex-col h-full transition-all duration-500`}>
                        {/* Header Area (Hide on Welcome) */}
                        {!isWelcomeStage && (
                            <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-gray-200 mb-6 flex items-center justify-between flex-shrink-0">
                                <div>
                                    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-1">{currentStage?.name}</h2>
                                    <p className="text-gray-500 text-xs sm:text-sm">Stage {currentStageIndex + 1} of {ASSESSMENT_STAGES.length}</p>
                                </div>
                                <div className="w-1/3 max-w-[200px]">
                                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                                        <span>Progress</span>
                                        <span>{Math.round(progress)}%</span>
                                    </div>
                                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <motion.div
                                            className="h-full bg-red-600 rounded-full"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${progress}%` }}
                                            transition={{ duration: 0.5 }}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Main Stage Content */}
                        <Card padding="none" className="flex-1 flex flex-col bg-white border border-gray-200 shadow-sm overflow-hidden relative">
                            <div className="flex-1 overflow-y-auto relative">
                                {renderStageContent()}

                                {/* Processing Overlay */}
                                {status === 'processing' && (
                                    <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-10">
                                        <div className="flex flex-col items-center gap-4">
                                            <LoadingSpinner size="lg" />
                                            <span className="text-gray-600 font-medium animate-pulse">Analyzing your response...</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Controls Footer */}
                            {showControls && (
                                <div className="p-4 sm:p-6 bg-white border-t border-gray-100 flex-shrink-0">
                                    <div className="flex items-center justify-center gap-4 sm:gap-6 max-w-2xl mx-auto">
                                        {status === 'recording' ? (
                                            <Button
                                                size="lg"
                                                onClick={handleStopRecording}
                                                className="w-full sm:w-auto min-w-[200px] py-4 shadow-lg shadow-red-500/20 bg-red-600 hover:bg-red-700 text-white border-none transition-all hover:scale-105"
                                            >
                                                <span className="flex items-center justify-center gap-2">
                                                    <span className="w-3 h-3 rounded-sm bg-white animate-pulse" />
                                                    Stop Recording
                                                </span>
                                            </Button>
                                        ) : (
                                            <>
                                                <Button
                                                    size="lg"
                                                    onClick={handleStartRecording}
                                                    disabled={status === 'processing'}
                                                    className="flex-1 py-4 shadow-lg shadow-red-600/10 text-lg group transition-all"
                                                >
                                                    <span className="flex items-center gap-2">
                                                        <span className="w-6 h-6 rounded-full bg-red-100 text-red-600 flex items-center justify-center group-hover:bg-red-500 group-hover:text-white transition-colors">
                                                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                                            </svg>
                                                        </span>
                                                        Start Speaking
                                                    </span>
                                                </Button>
                                                <Button
                                                    variant="secondary"
                                                    onClick={handleSkipStage}
                                                    disabled={status === 'processing'}
                                                    className="px-6 hover:bg-gray-100"
                                                >
                                                    Skip
                                                </Button>
                                            </>
                                        )}
                                    </div>
                                </div>
                            )}
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Assessment;
