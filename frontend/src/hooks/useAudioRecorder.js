// Audio recorder hook for capturing user's voice
import { useState, useRef, useCallback, useEffect } from 'react';

const useAudioRecorder = (options = {}) => {
    const {
        onDataAvailable,
        onStop,
        onError,
        sampleRate = 16000,
        maxDuration = 300, // 5 minutes max
    } = options;

    const [isRecording, setIsRecording] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [duration, setDuration] = useState(0);
    const [audioBlob, setAudioBlob] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [error, setError] = useState(null);
    const [permissionGranted, setPermissionGranted] = useState(false);

    const mediaRecorderRef = useRef(null);
    const streamRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);
    const startTimeRef = useRef(null);

    // Check for microphone permission
    const checkPermission = useCallback(async () => {
        try {
            const result = await navigator.permissions.query({ name: 'microphone' });
            setPermissionGranted(result.state === 'granted');
            return result.state === 'granted';
        } catch {
            // Permissions API not supported, will check during recording
            return null;
        }
    }, []);

    // Request microphone access
    const requestPermission = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });
            setPermissionGranted(true);
            streamRef.current = stream;
            return true;
        } catch (err) {
            const errorMessage = err.name === 'NotAllowedError'
                ? 'Microphone access denied. Please enable microphone permissions.'
                : err.name === 'NotFoundError'
                    ? 'No microphone found. Please connect a microphone.'
                    : `Microphone error: ${err.message}`;

            setError(errorMessage);
            onError?.(errorMessage);
            return false;
        }
    }, [sampleRate, onError]);

    // Start recording
    const startRecording = useCallback(async () => {
        try {
            setError(null);
            chunksRef.current = [];

            // Get microphone stream if not already available
            if (!streamRef.current) {
                const granted = await requestPermission();
                if (!granted) return;
            }

            // Create MediaRecorder
            const mimeType = MediaRecorder.isTypeSupported('audio/webm')
                ? 'audio/webm'
                : 'audio/mp4';

            mediaRecorderRef.current = new MediaRecorder(streamRef.current, {
                mimeType,
                audioBitsPerSecond: 128000,
            });

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                    onDataAvailable?.(event.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: mimeType });
                setAudioBlob(blob);

                const url = URL.createObjectURL(blob);
                setAudioUrl(url);

                onStop?.(blob, url);

                // Clear timer
                if (timerRef.current) {
                    clearInterval(timerRef.current);
                    timerRef.current = null;
                }
            };

            mediaRecorderRef.current.onerror = (event) => {
                const errorMessage = `Recording error: ${event.error?.message || 'Unknown error'}`;
                setError(errorMessage);
                onError?.(errorMessage);
            };

            // Start recording
            mediaRecorderRef.current.start(1000); // Collect data every second
            setIsRecording(true);
            setIsPaused(false);
            startTimeRef.current = Date.now();

            // Start duration timer
            timerRef.current = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
                setDuration(elapsed);

                // Auto-stop if max duration reached
                if (elapsed >= maxDuration) {
                    stopRecording();
                }
            }, 1000);

        } catch (err) {
            const errorMessage = `Failed to start recording: ${err.message}`;
            setError(errorMessage);
            onError?.(errorMessage);
        }
    }, [requestPermission, maxDuration, onDataAvailable, onStop, onError]);

    // Stop recording
    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setIsPaused(false);

            // Stop all tracks
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
                streamRef.current = null;
            }
        }
    }, [isRecording]);

    // Pause recording
    const pauseRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording && !isPaused) {
            mediaRecorderRef.current.pause();
            setIsPaused(true);

            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        }
    }, [isRecording, isPaused]);

    // Resume recording
    const resumeRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording && isPaused) {
            mediaRecorderRef.current.resume();
            setIsPaused(false);

            // Resume timer
            const elapsed = duration;
            startTimeRef.current = Date.now() - (elapsed * 1000);
            timerRef.current = setInterval(() => {
                const newElapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
                setDuration(newElapsed);

                if (newElapsed >= maxDuration) {
                    stopRecording();
                }
            }, 1000);
        }
    }, [isRecording, isPaused, duration, maxDuration, stopRecording]);

    // Reset recorder
    const resetRecording = useCallback(() => {
        stopRecording();
        setDuration(0);
        setAudioBlob(null);
        if (audioUrl) {
            URL.revokeObjectURL(audioUrl);
        }
        setAudioUrl(null);
        setError(null);
        chunksRef.current = [];
    }, [stopRecording, audioUrl]);

    // Format duration as MM:SS
    const formattedDuration = `${Math.floor(duration / 60).toString().padStart(2, '0')}:${(duration % 60).toString().padStart(2, '0')}`;

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [audioUrl]);

    return {
        isRecording,
        isPaused,
        duration,
        formattedDuration,
        audioBlob,
        audioUrl,
        error,
        permissionGranted,
        checkPermission,
        requestPermission,
        startRecording,
        stopRecording,
        pauseRecording,
        resumeRecording,
        resetRecording,
    };
};

export default useAudioRecorder;
