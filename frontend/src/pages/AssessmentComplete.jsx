import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Button from '../components/common/Button';
import Card from '../components/common/Card';

const AssessmentComplete = () => {
    const navigate = useNavigate();

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
                        Thank you for completing the assessment. Our AI is now analyzing your responses to provide a detailed evaluation of your speaking skills.
                    </p>

                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-8 text-left">
                        <h3 className="text-sm font-bold text-blue-900 mb-2">What happens next?</h3>
                        <ul className="text-sm text-blue-800 space-y-2 list-disc list-inside">
                            <li>We are grading your fluency, pronunciation, and confidence.</li>
                            <li>Your detailed report will be available shortly.</li>
                            <li>You can check your status in the dashboard.</li>
                        </ul>
                    </div>

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
