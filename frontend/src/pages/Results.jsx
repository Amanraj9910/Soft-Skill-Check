// Results Page - Interview Assessment Theme
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { assessmentService } from '../services/assessmentService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';

const ScoreGauge = ({ label, score, max = 20 }) => {
    const circumference = 2 * Math.PI * 40;
    const percentage = Math.min(100, Math.max(0, ((score || 0) / max) * 100));
    const offset = circumference - (percentage / 100) * circumference;

    // Determine color based on percentage
    let strokeColor = '#dc2626'; // Red
    if (percentage >= 80) strokeColor = '#16a34a'; // Green
    else if (percentage >= 60) strokeColor = '#ca8a04'; // Yellow

    return (
        <div className="flex flex-col items-center">
            <div className="score-circle mb-3 relative w-24 h-24">
                <svg className="w-full h-full transform -rotate-90">
                    <circle cx="48" cy="48" r="40" stroke="#f3f4f6" strokeWidth="8" fill="none" />
                    <motion.circle
                        cx="48" cy="48" r="40"
                        stroke={strokeColor}
                        strokeWidth="8" fill="none"
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 1, ease: "easeOut" }}
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-xl font-bold text-gray-800">
                    {Math.round(score || 0)}<span className="text-sm text-gray-400">/{max}</span>
                </div>
            </div>
            <span className="text-sm font-semibold text-gray-700 text-center max-w-[100px] leading-tight">{label}</span>
        </div>
    );
};

const Results = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadResults();
    }, [id]);

    const loadResults = async () => {
        try {
            console.log("Fetching results for:", id);
            // 1. Try to fetch existing scores
            let data = await assessmentService.getAssessmentScore(id).catch(err => {
                console.warn("Scores not ready, attempting calculation...", err);
                return null;
            });

            // 2. If no scores, trigger calculation
            if (!data) {
                console.log("Triggering score calculation...");
                await assessmentService.calculateScore(id);
                // Wait a bit for DB update (simple poll or delay)
                await new Promise(r => setTimeout(r, 2000));
                data = await assessmentService.getAssessmentScore(id);
            }

            setResult(data);
        } catch (err) {
            console.error('Failed to load results:', err);
            setError("Could not load results. Please try refreshing.");
        } finally {
            setLoading(false);
        }
    };

    const getGradeColorClass = (grade) => {
        if (!grade) return 'bg-gray-100 text-gray-800';
        const g = grade.toLowerCase();
        if (g.includes('expert') || g.includes('advanced')) return 'bg-green-100 text-green-800 border-green-200';
        if (g.includes('intermediate')) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-red-100 text-red-800 border-red-200';
    };

    if (loading) {
        return (
            <div className="min-h-screen pt-24 pb-16 flex flex-col items-center justify-center bg-gray-50">
                <LoadingSpinner size="lg" />
                <p className="mt-4 text-gray-600 font-medium animate-pulse">Analyzing your performance...</p>
            </div>
        );
    }

    if (error || !result) {
        return (
            <div className="min-h-screen pt-24 pb-16 flex items-center justify-center bg-gray-50 p-4">
                <Card padding="lg" className="text-center max-w-md w-full">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Results Unavailable</h2>
                    <p className="text-gray-600 mb-6">{error || "We couldn't generate your report card just yet."}</p>
                    <div className="flex gap-4 justify-center">
                        <Button variant="secondary" onClick={() => window.location.reload()}>Retry</Button>
                        <Button onClick={() => navigate('/dashboard')}>Dashboard</Button>
                    </div>
                </Card>
            </div>
        );
    }

    // Prepare scores for display dynamically based on what was saved
    const getDetailScore = (key) => {
        if (result.details && result.details[key] && typeof result.details[key].score === 'number') {
            return result.details[key].score;
        }
        return undefined;
    };

    const scoreItems = [];
    
    if (result.fluency_score !== undefined && result.fluency_score !== null) scoreItems.push({ label: 'Fluency', score: result.fluency_score, max: 20 });
    if (result.pronunciation_score !== undefined && result.pronunciation_score !== null) scoreItems.push({ label: 'Pronunciation', score: result.pronunciation_score, max: 10 });
    if (result.grammar_score !== undefined && result.grammar_score !== null) scoreItems.push({ label: 'Grammar', score: result.grammar_score, max: 10 });
    
    // Confidence can be mapped directly or composed
    const confScore = result.confidence_score !== undefined ? result.confidence_score : ((result.vocal_confidence_score || 0) + (result.textual_confidence || 0));
    scoreItems.push({ label: 'Confidence', score: confScore, max: 20 });
    
    if (result.storytelling_score !== undefined && result.storytelling_score !== null) scoreItems.push({ label: 'Storytelling', score: result.storytelling_score, max: 20 });
    if (result.vision_clarity_score !== undefined && result.vision_clarity_score !== null) scoreItems.push({ label: 'Vision', score: result.vision_clarity_score, max: 10 });
    if (result.aim_clarity_score !== undefined && result.aim_clarity_score !== null) scoreItems.push({ label: 'Aim', score: result.aim_clarity_score, max: 10 });

    // Include Textual Confidence if it exists in details (audio_grader logic uses it for the total score)
    const textualConf = getDetailScore('textual_confidence');
    if (textualConf !== undefined && result.confidence_score !== undefined) {
        // If confidence_score was provided directly by audio_grader, it doesn't include textual_confidence, so it must be added separately to match the math
        scoreItems.push({ label: 'Textual Comm.', score: textualConf, max: 10 });
    }

    // Include Hesitation if it contributed to the score
    const hesitation = result.hesitation_score !== undefined ? result.hesitation_score : getDetailScore('hesitation');
    if (hesitation !== undefined && hesitation !== 0) {
        scoreItems.push({ label: 'Hesitation', score: hesitation, max: 10 });
    }


    return (
        <div className="min-h-screen pt-24 pb-16 bg-gray-50">
            <div className="container mx-auto px-6 max-w-5xl">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <div className={`inline-block px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wider mb-4 border ${getGradeColorClass(result.grade)}`}>
                        {result.grade || 'Completed'}
                    </div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-3">Assessment Report</h1>
                    <p className="text-xl text-gray-600">
                        Total Score: <span className="font-bold text-gray-900 text-3xl">{Math.round(result.total_score || 0)}</span><span className="text-gray-400">/100</span>
                    </p>
                    <div className="mt-8 p-6 bg-white rounded-2xl shadow-sm border border-gray-100 max-w-3xl mx-auto">
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Overall Review</h3>
                        <p className="text-gray-600 italic">
                            "{result.overall_feedback || "Assessment completed successfully."}"
                        </p>
                    </div>
                </motion.div>

                {/* Score Grid */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card padding="lg" className="mb-12">
                        <h2 className="text-xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4 text-center">
                            Performance Breakdown
                        </h2>
                        <div className="flex flex-wrap justify-center gap-8">
                            {scoreItems.map((item) => (
                                <ScoreGauge key={item.label} label={item.label} score={item.score} max={item.max} />
                            ))}
                        </div>
                    </Card>
                </motion.div>

                {/* Detailed Breakdown (Hidden from candidate) */}
                {/* 
                {result.details && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                        <Card padding="lg" className="mb-12">
                            <h2 className="text-xl font-bold text-gray-900 mb-6 border-b border-gray-100 pb-4">
                                Detailed Analysis & Reasoning
                            </h2>
                            <div className="space-y-6">
                                {[
                                    { key: 'fluency', label: 'Fluency', max: 20 },
                                    { key: 'pronunciation', label: 'Pronunciation', max: 10 },
                                    { key: 'grammar', label: 'Grammar', max: 10 },
                                    { key: 'vocal_confidence', label: 'Vocal Confidence', max: 10 },
                                    { key: 'textual_confidence', label: 'Textual Confidence', max: 10 },
                                    { key: 'storytelling', label: 'Storytelling', max: 20 },
                                    { key: 'vision_clarity', label: 'Vision', max: 10 },
                                    { key: 'aim_clarity', label: 'Aim', max: 10 },
                                    { key: 'hesitation', label: 'Hesitation Penalty', max: 0 },
                                ].map((cat) => {
                                    const categoryData = result.details[cat.key];
                                    if (!categoryData || !categoryData.reasoning) return null;
                                    return (
                                        <div key={cat.key} className="bg-white rounded-xl p-5 border border-gray-100 shadow-sm">
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="font-bold text-gray-900 text-lg">{cat.label}</h4>
                                                <span className={`font-bold px-3 py-1 rounded-full text-sm ${cat.key === 'hesitation' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>
                                                    {categoryData.score} {cat.max > 0 ? `/ ${cat.max}` : 'Marks'}
                                                </span>
                                            </div>
                                            <p className="text-gray-700 leading-relaxed text-sm whitespace-pre-line">{categoryData.reasoning}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        </Card>
                    </motion.div>
                )}
                */}

                {/* Thank You Message */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="text-center mb-10"
                >
                    <h2 className="text-2xl font-bold text-blue-600">Thank you for completing the assessment!</h2>
                    <p className="text-gray-500 mt-2">Your results have been recorded.</p>
                </motion.div>

                {/* Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="flex flex-col sm:flex-row gap-4 justify-center"
                >
                    <Button variant="secondary" size="lg" onClick={() => navigate('/dashboard')}>
                        Return to Dashboard
                    </Button>
                </motion.div>
            </div>
        </div>
    );
};

export default Results;
