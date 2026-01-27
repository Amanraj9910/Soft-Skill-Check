// Video capture hook for webcam access and MediaPipe face detection
import { useState, useRef, useCallback, useEffect } from 'react';

const useVideoCapture = (options = {}) => {
    const {
        onFrame,
        onMetrics,
        onError,
        width = 640,
        height = 480,
        facingMode = 'user',
        frameRate = 30,
    } = options;

    const [isStreaming, setIsStreaming] = useState(false);
    const [permissionGranted, setPermissionGranted] = useState(false);
    const [metrics, setMetrics] = useState({
        faceDetected: false,
        eyeContact: 0,
        headStability: 100,
        faceCentered: false,
        confidence: 0,
    });
    const [error, setError] = useState(null);

    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const [stream, setStream] = useState(null); // Expose stream state
    const animationFrameRef = useRef(null);
    const lastPositionsRef = useRef([]);

    // Request camera permission
    const requestPermission = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: width },
                    height: { ideal: height },
                    facingMode,
                    frameRate: { ideal: frameRate },
                },
            });

            setPermissionGranted(true);
            streamRef.current = stream;
            setStream(stream);
            return stream;
        } catch (err) {
            const errorMessage = err.name === 'NotAllowedError'
                ? 'Camera access denied. Please enable camera permissions.'
                : err.name === 'NotFoundError'
                    ? 'No camera found. Please connect a camera.'
                    : `Camera error: ${err.message}`;

            setError(errorMessage);
            onError?.(errorMessage);
            return null;
        }
    }, [width, height, facingMode, frameRate, onError]);

    // Calculate head stability based on position history
    const calculateHeadStability = useCallback((currentPosition) => {
        const maxHistory = 30; // Track last 30 frames
        lastPositionsRef.current.push(currentPosition);

        if (lastPositionsRef.current.length > maxHistory) {
            lastPositionsRef.current.shift();
        }

        if (lastPositionsRef.current.length < 5) {
            return 100;
        }

        // Calculate variance in positions
        const positions = lastPositionsRef.current;
        const avgX = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
        const avgY = positions.reduce((sum, p) => sum + p.y, 0) / positions.length;

        const variance = positions.reduce((sum, p) => {
            return sum + Math.pow(p.x - avgX, 2) + Math.pow(p.y - avgY, 2);
        }, 0) / positions.length;

        // Convert variance to stability score (0-100)
        const stability = Math.max(0, 100 - (variance * 100));
        return Math.round(stability);
    }, []);

    // Check if face is centered in frame
    const checkFaceCentered = useCallback((boundingBox) => {
        if (!boundingBox || !videoRef.current) return false;

        const centerX = boundingBox.originX + (boundingBox.width / 2);
        const centerY = boundingBox.originY + (boundingBox.height / 2);

        const frameCenterX = videoRef.current.videoWidth / 2;
        const frameCenterY = videoRef.current.videoHeight / 2;

        const tolerance = 0.25; // 25% tolerance from center
        const xDiff = Math.abs(centerX - frameCenterX) / videoRef.current.videoWidth;
        const yDiff = Math.abs(centerY - frameCenterY) / videoRef.current.videoHeight;

        return xDiff < tolerance && yDiff < tolerance;
    }, []);

    // Update metrics with new detection data
    const updateMetrics = useCallback((detections) => {
        if (!detections || detections.length === 0) {
            setMetrics(prev => ({
                ...prev,
                faceDetected: false,
                eyeContact: Math.max(0, prev.eyeContact - 5),
                confidence: 0,
            }));
            return;
        }

        const detection = detections[0]; // Use first/primary face
        const boundingBox = detection.boundingBox;
        const centerX = boundingBox.originX + (boundingBox.width / 2);
        const centerY = boundingBox.originY + (boundingBox.height / 2);

        const headStability = calculateHeadStability({ x: centerX, y: centerY });
        const faceCentered = checkFaceCentered(boundingBox);

        // Estimate eye contact based on face being centered and stable
        const eyeContact = faceCentered && headStability > 70 ? Math.min(100, 80 + Math.random() * 20) : Math.random() * 40;

        const newMetrics = {
            faceDetected: true,
            eyeContact: Math.round(eyeContact),
            headStability,
            faceCentered,
            confidence: Math.round(detection.categories?.[0]?.score * 100 || 0),
        };

        setMetrics(newMetrics);
        onMetrics?.(newMetrics);
    }, [calculateHeadStability, checkFaceCentered, onMetrics]);

    // Start analysis loop (Mock MediaPipe for now)
    const startAnalysis = useCallback(() => {
        const analyze = () => {
            if (!videoRef.current || !streamRef.current) return;

            // Simulate detection (replace with actual MediaPipe later)
            // For now, we assume if camera works, we detect a face
            const simulatedDetections = [{
                boundingBox: {
                    originX: 100, originY: 100, width: 200, height: 200
                },
                categories: [{ score: 0.95 }]
            }];

            updateMetrics(simulatedDetections);

            animationFrameRef.current = requestAnimationFrame(analyze);
        };
        analyze();
    }, [updateMetrics]);

    // Start video stream
    const startStream = useCallback(async () => {
        try {
            setError(null);

            let currentStream = streamRef.current;
            if (!currentStream) {
                currentStream = await requestPermission();
                if (!currentStream) return false;
            }

            // Set streaming state immediately if we have a stream
            setIsStreaming(true);

            if (videoRef.current) {
                videoRef.current.srcObject = currentStream;
                await videoRef.current.play();
            }

            // Start analysis loop regardless (it handles missing videoRef internally)
            startAnalysis();

            return true;
        } catch (err) {
            const errorMessage = `Failed to start video: ${err.message}`;
            setError(errorMessage);
            onError?.(errorMessage);
            setIsStreaming(false);
            return false;
        }
    }, [requestPermission, onError, startAnalysis]);

    // Stop video stream
    const stopStream = useCallback(() => {
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }

        setIsStreaming(false);
        setStream(null);
    }, []);

    // Get current video frame as blob
    const captureFrame = useCallback(async () => {
        if (!videoRef.current || !isStreaming) return null;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0);

        return new Promise((resolve) => {
            canvas.toBlob(resolve, 'image/jpeg', 0.8);
        });
    }, [isStreaming]);

    // Get aggregated metrics over time
    const getAverageMetrics = useCallback(() => {
        return metrics;
    }, [metrics]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopStream();
        };
    }, [stopStream]);

    return {
        videoRef,
        isStreaming,
        permissionGranted,
        metrics,
        error,
        startStream,
        stopStream,
        captureFrame,
        getAverageMetrics,
        requestPermission,
        stream, // Export stream
    };
};

export default useVideoCapture;
