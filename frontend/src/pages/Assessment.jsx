// Assessment Page - Professional Assessment Environment
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import useAssessment, { ASSESSMENT_STAGES } from '../hooks/useAssessment';
import useAudioRecorder from '../hooks/useAudioRecorder';
import useVideoCapture from '../hooks/useVideoCapture';
import { conversationService } from '../services/conversationService';
import { API_TIMEOUTS } from '../services/api';
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
    }, [stream, isStreaming, currentStage]); // Re-run when stage changes (video element might mount)

    const [status, setStatus] = useState('idle'); // idle, ready, recording, processing, playing_greeting, playing_response, thinking
    const [permissionsGranted, setPermissionsGranted] = useState(false);
    const [lastAudioUrl, setLastAudioUrl] = useState(null);
    const isSubmittingRef = useRef(false); // Prevent duplicate submissions

    // AI Greeting Effect - FIXED: Only play if we are starting freshly or it's the very first interaction of a stage that NEEDS it.
    // The previous logic played it on every mount, causing duplicates if the transition audio also played.
    // We'll rely on the previous stage's transition response to play the "moving on" audio.
    // This effect is now strictly for initial load or manual recover.
    useEffect(() => {
        if (!currentStage || currentStage.id === 'welcome' || !permissionsGranted) return;

        // If we just transitioned and have AI audio playing from the transition, don't fetch greeting.
        if (status === 'playing_response') return;

        const playGreeting = async (retryCount = 0) => {
            try {
                if (retryCount === 0) setLastAudioUrl(null);
                console.log(`🗣️ [Assessment Page] Fetching greeting for ${currentStage.id}... (attempt ${retryCount + 1})`);
                setStatus('playing_greeting');
                const response = await conversationService.getGreeting(currentStage.id);

                if (response.audio_url) {
                    setLastAudioUrl(response.audio_url);
                    console.log('🔊 [Assessment Page] Playing greeting audio...');
                    const audio = new Audio(response.audio_url);
                    audio.onended = () => {
                        console.log('✅ [Assessment Page] Greeting finished');
                        setStatus('ready');
                    };
                    audio.onerror = (e) => {
                        console.error('❌ [Assessment Page] Audio playback error', e);
                        setStatus('ready');
                    };
                    await audio.play();
                } else {
                    setStatus('ready');
                }
            } catch (err) {
                console.error(`❌ [Assessment Page] Greeting attempt ${retryCount + 1} failed:`, err);
                // Retry once after 2s delay (handles TTS cold-start timeouts)
                if (retryCount < 1) {
                    console.log('🔄 [Assessment Page] Retrying greeting in 2s...');
                    await new Promise(r => setTimeout(r, 2000));
                    return playGreeting(retryCount + 1);
                }
                console.warn('⚠️ [Assessment Page] Greeting failed after retry — continuing without audio');
                setStatus('ready');
            }
        };

        playGreeting();
    }, [currentStage?.id, permissionsGranted]); // carefully scoped

    const [initError, setInitError] = useState(null);
    const initStartedRef = useRef(false);

    // Initialize assessment sequence
    useEffect(() => {
        console.log('📍 [Assessment Page] useEffect triggered - initializing assessment');

        // Prevent double initialization in React Strict Mode
        if (initStartedRef.current) {
            console.log('📍 [Assessment Page] Already initializing, skipping...');
            return;
        }
        initStartedRef.current = true;

        let mounted = true;
        const abortController = new AbortController();

        const init = async () => {
            try {
                console.log('📍 [Assessment Page] Calling startAssessment()...');
                // Add timeout to prevent infinite loading - using extended timeout for AI operations
                const timeoutPromise = new Promise((_, reject) => {
                    const id = setTimeout(() => reject(new Error('Request timed out. Please check your connection.')), API_TIMEOUTS.audio);
                    abortController.signal.addEventListener('abort', () => clearTimeout(id));
                });

                await Promise.race([startAssessment(), timeoutPromise]);

                if (mounted) {
                    console.log('📍 [Assessment Page] startAssessment() completed');
                    setInitError(null);
                }
            } catch (err) {
                if (abortController.signal.aborted) {
                    console.log('📍 [Assessment Page] Request aborted');
                    return;
                }
                console.error('❌ [Assessment Page] Failed to start assessment:', err);
                if (mounted) {
                    setInitError(err.message || 'Failed to start assessment. Please try again.');
                }
            }
        };
        init();
        return () => {
            mounted = false;
            abortController.abort();
            // NOTE: Do NOT reset initStartedRef here — it causes StrictMode
            // to call startAssessment() twice, creating duplicate DB records.
            console.log('📍 [Assessment Page] Cleanup - stopping stream');
            stopStream();
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
        // Prevent duplicate submissions
        if (isSubmittingRef.current) {
            console.warn('⚠️ [Assessment Page] Submission already in progress, ignoring duplicate request');
            return;
        }

        isSubmittingRef.current = true;
        setStatus('processing');

        try {
            // stopRecording now returns a Promise with the blob
            const recordedBlob = await stopRecording();

            // Validate the blob
            if (!recordedBlob) {
                console.warn('⚠️ [Assessment Page] No audio blob returned from recording');
                setInitError('No audio was recorded. Please try again.');
                setStatus('ready');
                return;
            }

            if (recordedBlob.size === 0) {
                console.warn('⚠️ [Assessment Page] Audio blob is empty');
                setInitError('Audio recording failed. Please check microphone permissions.');
                setStatus('ready');
                return;
            }

            console.log(`📤 [Assessment Page] Submitting audio: ${(recordedBlob.size / 1024).toFixed(2)}KB`);

            const response = await saveStageResponse({
                audio: recordedBlob,
                prompt: currentStage?.name || "Response",
                metrics: getAverageMetrics()
            });

            console.log('✅ [Assessment Page] Stage response saved:', response);

            // Play AI Response if available
            if (response?.ai_audio_url) {
                setLastAudioUrl(response.ai_audio_url);
                console.log('🔊 [Assessment Page] Playing AI audio response...');
                setStatus('playing_response');
                const audio = new Audio(response.ai_audio_url);

                const onAudioComplete = () => {
                    console.log('✅ [Assessment Page] AI audio finished');

                    if (response.should_transition) {
                        console.log('🏁 [Assessment Page] AI signaled transition');
                        proceedToNext(response);
                    } else {
                        console.log('🔄 [Assessment Page] Continuing conversation');
                        setStatus('ready');
                    }
                };

                audio.onended = onAudioComplete;
                audio.onerror = (e) => {
                    console.error('❌ [Assessment Page] AI audio playback error:', e);
                    onAudioComplete(); // Fallback to logic even if audio fails
                };

                audio.play().catch(e => {
                    console.error("Audio play failed", e);
                    onAudioComplete();
                });
            } else {
                console.log('ℹ️ [Assessment Page] No AI audio, checking for transition...');
                if (response.should_transition) {
                    proceedToNext(response);
                } else {
                    // If no audio and no transition, we must reset status to ready
                    // Otherwise the "Thinking..." overlay will persist forever
                    console.log('⚠️ [Assessment Page] No AI audio and no transition - resetting state');
                    setStatus('ready');
                }
            }
        } catch (err) {
            console.error('❌ [Assessment Page] Error submitting response:', err);
            setInitError(`Failed to process response: ${err.message || 'Please try again.'}`);
            setStatus('ready');
        } finally {
            isSubmittingRef.current = false;
        }
    };

    const handleSpeakAgain = () => {
        if (!lastAudioUrl || status === 'playing_greeting' || status === 'playing_response') return;
        
        setStatus('playing_response');
        const audio = new Audio(lastAudioUrl);
        
        const onAudioComplete = () => setStatus('ready');
        
        audio.onended = onAudioComplete;
        audio.onerror = (e) => {
            console.error('❌ [Assessment Page] Replay audio playback error:', e);
            onAudioComplete();
        };
        
        audio.play().catch(e => {
            console.error("Audio replay play failed", e);
            onAudioComplete();
        });
    };

    // New "Thinking" State Helper
    const ThinkingOverlay = () => (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center rounded-xl">
            <div className="flex space-x-2 mb-4">
                <div className="w-3 h-3 bg-red-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-3 h-3 bg-red-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-3 h-3 bg-red-600 rounded-full animate-bounce"></div>
            </div>
            <p className="text-slate-600 font-medium animate-pulse">AI is thinking...</p>
        </div>
    );

    const proceedToNext = async (response = {}) => {
        console.log('🔄 [Assessment Page] proceedToNext called:', {
            next_section: response.next_section,
            isLastStage,
            currentStageIndex
        });

        if (response.next_section) {
            // AI wants to jump to specific section (not implemented in hook yet, but good to have)
            // For now standard nextStage
            console.log('➡️ [Assessment Page] Moving to next section:', response.next_section);
            nextStage();
            setStatus('ready');
            return;
        }

        if (isLastStage) {
            console.log('🏁 [Assessment Page] Last stage completed! Navigating to completion page...');

            // Try to complete assessment, but navigate regardless of outcome
            // The scoring engine runs asynchronously in the background
            try {
                await completeAssessment();
                console.log('✅ [Assessment Page] Assessment completed successfully');
            } catch (err) {
                // Don't block navigation - scoring may still be processing in background
                console.warn('⚠️ [Assessment Page] completeAssessment had an error (scoring may still be processing):', err.message);
            }

            // ALWAYS navigate to completion page, even if there was an error
            // The user can view results once scoring finishes
            navigate('/assessment-complete');
        } else {
            nextStage();
            setStatus('ready');
        }
    };



    // Stage Renderer with Props
    const renderStageContent = () => {
        // Shared props for stages that need to interact with the parent state
        const stageProps = {
            status,             // To show 'recording', 'processing', etc. inside the stage
            isStreaming,        // To know if camera is on
            onRepeat: async () => { /* Logic to repeat last AI audio? Needs backend support or cached URL */ }
        };

        switch (currentStage?.id) {
            case 'welcome': return <WelcomeStage onStart={handleGrantPermissions} />;
            case 'introduction': return <IntroductionStage {...stageProps} />;
            case 'reading': return <ReadingStage {...stageProps} />;
            case 'listening': return <ListeningStage {...stageProps} />; // This is the Shadowing stage
            case 'storytelling': return <StorytellingStage {...stageProps} />;
            case 'opinion': return <OpinionStage {...stageProps} />;
            case 'aim': return <AimStage {...stageProps} />;
            default: return <div>Unknown Assessment Stage</div>;
        }
    };

    if (assessmentLoading) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
                <LoadingSpinner size="lg" />
                <p className="mt-4 text-slate-600 font-medium">Initializing Assessment Environment...</p>
                <p className="mt-2 text-slate-400 text-sm">This may take a few seconds</p>
            </div>
        );
    }

    // Show error state if initialization failed
    if (initError || (!assessment && !assessmentLoading)) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
                <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">
                        {initError ? 'Connection Error' : 'Check Connection'}
                    </h2>
                    <p className="text-gray-600 mb-6">
                        {initError || "We couldn't start the assessment. This might be due to a network issue or missing user profile. Refreshing the page usually fixes this."}
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
                            <div className="flex-1 relative">
                                {status === 'processing' && <ThinkingOverlay />}
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
                                        ) : status === 'playing_greeting' || status === 'playing_response' ? (
                                            <span className="flex items-center gap-2 text-blue-600 font-medium animate-pulse">
                                                🔊 AI Speaking...
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
                                                {lastAudioUrl && (
                                                    <Button
                                                        onClick={handleSpeakAgain}
                                                        disabled={status === 'processing' || status === 'playing_greeting' || status === 'playing_response'}
                                                        className="bg-indigo-600 hover:bg-indigo-700 text-white min-w-[140px]"
                                                    >
                                                        🔊 Speak Again
                                                    </Button>
                                                )}
                                                <Button
                                                    onClick={handleStartRecording}
                                                    disabled={status === 'processing' || status === 'playing_greeting' || status === 'playing_response'}
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
                                {(!isStreaming) && (
                                    <div className="absolute inset-0 flex items-center justify-center bg-zinc-900 text-white/30 text-xs">
                                        NO SIGNAL
                                    </div>
                                )}
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
