// Assessment Page - Professional Assessment Environment
import { useState, useEffect } from 'react';
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
        loading: assessmentLoading, isLastStage, startAssessment, saveStageResponse,
        nextStage, completeAssessment, resetAssessment
    } = useAssessment();

    const { isRecording, formattedDuration, audioBlob, startRecording, stopRecording, resetRecording } = useAudioRecorder();

    const { videoRef, isStreaming, startStream, stopStream, stream, getAverageMetrics } = useVideoCapture(); // Get stream & metrics

    // Ensure video stream is attached when element mounts
    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream, isStreaming]); // Re-run if stream changes or streaming state updates

    const [status, setStatus] = useState('idle'); // idle, ready, recording, processing
    const [permissionsGranted, setPermissionsGranted] = useState(false);

    // Initialize assessment sequence
    useEffect(() => {
        const init = async () => {
            try {
                await startAssessment();
            } catch (err) {
                console.error('Failed to start assessment:', err);
                // Error state is already set in hook, but we can also set local status if needed
            }
        };
        init();
        return () => {
            stopStream();
            resetAssessment();
        };
    }, []);

    const handleGrantPermissions = async () => {
        try {
            await startStream();
            setPermissionsGranted(true);
            setStatus('ready');
            nextStage(); // Move from Welcome to Introduction
        } catch (err) {
            console.error("Device access denied:", err);
            alert("Camera and Microphone access are required to proceed.");
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

        // Short buffer to ensure audio blob readiness
        setTimeout(async () => {
            try {
                if (audioBlob) {
                    const response = await saveStageResponse({
                        audio: audioBlob,
                        prompt: currentStage?.name || "Response",
                        metrics: getAverageMetrics() // Pass vision metrics
                    });

                    // Play AI Response if available
                    if (response?.ai_audio_url) {
                        setStatus('playing_response');
                        const audio = new Audio(response.ai_audio_url);
                        audio.onended = () => {
                            proceedToNext();
                        };
                        audio.play().catch(e => {
                            console.error("Audio play failed", e);
                            proceedToNext();
                        });
                    } else {
                        proceedToNext();
                    }
                } else {
                    proceedToNext();
                }
            } catch (err) {
                console.error('Error submitting response:', err);
                setStatus('ready');
            }
        }, 1000);
    };

    const proceedToNext = async () => {
        if (isLastStage) {
            await completeAssessment();
            navigate(`/results/${assessment?.id}`);
        } else {
            nextStage();
            setStatus('ready');
        }
    };

    const handleSkip = () => {
        if (isLastStage) {
            navigate(`/results/${assessment?.id}`);
        } else {
            nextStage();
            setStatus('ready');
        }
    };

    // Stage Renderer
    const renderStageContent = () => {
        switch (currentStage?.id) {
            case 'welcome': return <WelcomeStage onStart={handleGrantPermissions} />;
            case 'introduction': return <IntroductionStage />;
            case 'reading': return <ReadingStage />;
            case 'listening': return <ListeningStage />;
            case 'storytelling': return <StorytellingStage />;
            case 'opinion': return <OpinionStage />;
            case 'aim': return <AimStage />;
            default: return <div>Unknown Assessment Stage</div>;
        }
    };

    if (assessmentLoading) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
                <LoadingSpinner size="lg" />
                <p className="mt-4 text-slate-600 font-medium">Initializing Assessment Environment...</p>
            </div>
        );
    }

    if (!assessment && !assessmentLoading) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
                <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Check Connection</h2>
                    <p className="text-gray-600 mb-6">
                        We couldn't start the assessment. This might be due to a network issue or missing user profile.
                        Refresing the page usually fixes this.
                    </p>
                    <Button onClick={() => window.location.reload()} fullWidth>
                        Retry Connection
                    </Button>
                </div>
            </div>
        );
    }

    if (!currentStage) return null;

    const isWelcome = currentStage.id === 'welcome';



    return (
        <div className="min-h-screen bg-slate-50 flex flex-col pt-16">
            {/* Top Progress Bar - Minimal */}
            {!isWelcome && (
                <div className="bg-white border-b border-slate-200">
                    <div className="container mx-auto max-w-5xl px-6 h-14 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <span className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                                Section {currentStageIndex + 1}/{ASSESSMENT_STAGES.length}
                            </span>
                            <span className="h-4 w-px bg-slate-200"></span>
                            <span className="text-sm font-medium text-slate-600">
                                {currentStage.name}
                            </span>
                        </div>
                        <div className="w-32 text-right">
                            <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-slate-900"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Workspace */}
            <main className="flex-1 container mx-auto max-w-5xl px-6 py-8 flex flex-col">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-full">

                    {/* Left: Content Area */}
                    <div className={`lg:col-span-8 flex flex-col ${isWelcome ? 'lg:col-span-12' : ''}`}>
                        <Card className="flex-1 p-8 shadow-sm border-slate-200 flex flex-col min-h-[500px]">
                            <div className="flex-1">
                                {renderStageContent()}
                            </div>

                            {/* Controls - Only show if not welcome and media ready */}
                            {!isWelcome && permissionsGranted && (
                                <div className="mt-8 pt-8 border-t border-slate-100 flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-sm text-slate-500">
                                        {status === 'processing' ? (
                                            <span className="flex items-center gap-2 text-slate-900 font-medium">
                                                <LoadingSpinner size="sm" /> Saving Response...
                                            </span>
                                        ) : (
                                            <span>
                                                {status === 'recording' ? 'Microphone Active' : 'Ready to Record'}
                                            </span>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-4">
                                        {status === 'recording' ? (
                                            <Button
                                                onClick={handleStopRecording}
                                                className="bg-red-600 hover:bg-red-700 text-white min-w-[160px] animate-pulse"
                                            >
                                                Stop & Submit
                                            </Button>
                                        ) : (
                                            <div className="flex gap-3">
                                                <Button
                                                    variant="secondary"
                                                    onClick={handleSkip}
                                                    disabled={status === 'processing'}
                                                >
                                                    Skip
                                                </Button>
                                                <Button
                                                    onClick={handleStartRecording}
                                                    disabled={status === 'processing'}
                                                    className="bg-slate-900 hover:bg-black text-white min-w-[160px]"
                                                >
                                                    Start Recording
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </Card>
                    </div>

                    {/* Right: Camera Feed Monitor (Hidden on Welcome) */}
                    {!isWelcome && (
                        <div className="lg:col-span-4 flex flex-col gap-6">
                            {/* Video Monitor */}
                            <div className="bg-black rounded-lg overflow-hidden shadow-lg border border-slate-800 aspect-video relative group">
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    muted
                                    playsInline
                                    className="w-full h-full object-cover transform scale-x-[-1] opacity-90"
                                />
                                <div className="absolute top-3 right-3 flex flex-col gap-2">
                                    {status === 'recording' && (
                                        <div className="px-2 py-1 bg-red-600 text-white text-xs font-bold rounded flex items-center gap-1.5 shadow-sm">
                                            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                                            REC {formattedDuration}
                                        </div>
                                    )}
                                </div>
                                <div className="absolute bottom-3 left-3 text-xs font-mono text-white/50">
                                    MONITOR OUTPUT
                                </div>
                            </div>

                            {/* Audio Level / Status - Minimal */}
                            <div className="bg-white p-4 rounded-lg border border-slate-200">
                                <div className="text-xs font-bold text-slate-400 uppercase mb-2">System Status</div>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-slate-600">Video Feed</span>
                                        <span className="text-green-600 font-bold text-xs uppercase">Active</span>
                                    </div>
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-slate-600">Microphone</span>
                                        <span className="text-green-600 font-bold text-xs uppercase">Ready</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Assessment;
