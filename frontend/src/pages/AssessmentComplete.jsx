import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { assessmentService } from '../services/assessmentService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';

const AssessmentComplete = () => {
    const navigate = useNavigate();
    const location = useLocation();
    
    // Extract assessment ID from the path or state if available
    const assessmentId = location.state?.assessmentId || localStorage.getItem('currentAssessmentId');

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [score, setScore] = useState(null);

    useEffect(() => {
        const fetchScore = async () => {
            if (!assessmentId) {
                setLoading(false);
                return;
            }
            
            try {
                const scoreData = await assessmentService.getAssessmentScore(assessmentId);
                if (scoreData) {
                    setScore(scoreData);
                    setError(null);
                }
            } catch (err) {
                console.error('Error fetching score:', err);
                setError('Unable to load assessment results. Results may still be processing.');
            } finally {
                setLoading(false);
            }
        };

        fetchScore();
        
        // Also update the assessment status to completed to ensure it's properly marked
        const updateAssessmentStatus = async () => {
            if (!assessmentId) return;
            
            try {
                // Attempt to complete the assessment if not already completed
                await assessmentService.completeAssessment(assessmentId);
            } catch (err) {
                // If it's already completed, that's fine - just log the error
                console.warn('Warning completing assessment (may already be completed):', err);
            }
        };
        
        updateAssessmentStatus();
    }, [assessmentId]);

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
            <Card className="max-w-md w-full p-8 text-center shadow-lg border-slate-200">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                >
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <span className="text-4xl">🎉</span>
                    </div>

                    <h1 className="text-2xl font-bold text-slate-900 mb-4">
                        Assessment Completed!
                    </h1>

                    <p className="text-slate-600 mb-8 leading-relaxed">
                        Thank you for completing the assessment. Your performance has been recorded and you will not be able to retake this assessment.
                    </p>

                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-8 text-left">
                        <h3 className="text-sm font-bold text-blue-900 mb-2">Important Notice:</h3>
                        <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
                            <li>Your assessment has been permanently recorded in our system.</li>
                            <li>No additional attempts will be allowed for this assessment.</li>
                            <li>If you experienced technical issues, please contact support immediately.</li>
                        </ul>
                    </div>

                    {loading && (
                        <div className="py-4">
                            <p className="text-slate-600">Processing your results...</p>
                        </div>
                    )}

                    {error && (
                        <div className="py-4">
                            <p className="text-red-600 text-sm">{error}</p>
                        </div>
                    )}

                    <div className="space-y-3">
                        <Button
                            onClick={() => navigate('/dashboard')}
                            className="bg-slate-900 hover:bg-black text-white w-full"
                        >
                            Return to Dashboard
                        </Button>
                    </div>
                </motion.div>
            </Card>
        </div>
    );
};

export default AssessmentComplete;