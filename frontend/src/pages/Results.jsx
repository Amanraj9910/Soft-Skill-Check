// Results Page - Interview Assessment Theme
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { assessmentService } from '../services/assessmentService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';

const ScoreGauge = ({ label, score }) => {
    const circumference = 2 * Math.PI * 40;
    const offset = circumference - ((score || 0) / 100) * circumference;

    // Determine color based on score
    let strokeColor = '#dc2626'; // Red (default/low)
    if (score >= 80) strokeColor = '#16a34a'; // Green
    else if (score >= 60) strokeColor = '#ca8a04'; // Yellow

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
                    {Math.round(score || 0)}
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

    // Prepare scores for display
    const scoreItems = [
        { label: 'Fluency', score: result.fluency_score },
        { label: 'Pronunciation', score: result.pronunciation_score },
        { label: 'Grammar', score: result.grammar_score },
        { label: 'Confidence', score: result.confidence_score },
        { label: 'Storytelling', score: result.storytelling_score },
        { label: 'Vision', score: result.vision_clarity_score },
    ];

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
                    <p className="mt-4 max-w-2xl mx-auto text-gray-600 italic">
                        "{result.overall_feedback}"
                    </p>
                </motion.div>

                {/* Score Grid */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card padding="lg" className="mb-8">
                        <h2 className="text-xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4">
                            Performance Breakdown
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 justify-items-center">
                            {scoreItems.map((item) => (
                                <ScoreGauge key={item.label} label={item.label} score={item.score} />
                            ))}
                        </div>
                    </Card>
                </motion.div>

                {/* Strengths & Weaknesses */}
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                        <Card padding="lg" className="h-full border-t-4 border-t-green-500 shadow-sm hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <span className="bg-green-100 text-green-700 p-2 rounded-lg">💪</span> Strengths
                            </h3>
                            {result.strengths && result.strengths.length > 0 ? (
                                <ul className="space-y-3">
                                    {result.strengths.map((item, i) => (
                                        <li key={i} className="flex items-start gap-3 text-gray-700">
                                            <span className="text-green-500 mt-1">✓</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-gray-400 italic">No specific strengths highlighted.</p>
                            )}
                        </Card>
                    </motion.div>

                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                        <Card padding="lg" className="h-full border-t-4 border-t-orange-500 shadow-sm hover:shadow-md transition-shadow">
                            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <span className="bg-orange-100 text-orange-700 p-2 rounded-lg">📈</span> Areas to Improve
                            </h3>
                            {result.weaknesses && result.weaknesses.length > 0 ? (
                                <ul className="space-y-3">
                                    {result.weaknesses.map((item, i) => (
                                        <li key={i} className="flex items-start gap-3 text-gray-700">
                                            <span className="text-orange-500 mt-1">!</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="text-gray-400 italic">No major weaknesses detected.</p>
                            )}
                        </Card>
                    </motion.div>
                </div>

                {/* Recommendations */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <Card padding="lg" className="mb-10 bg-gradient-to-r from-slate-900 to-slate-800 text-white border-none shadow-xl">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                            <span className="bg-white/10 p-2 rounded-lg">💡</span> Action Plan
                        </h3>
                        {result.recommendations && result.recommendations.length > 0 ? (
                            <ul className="space-y-4">
                                {result.recommendations.map((item, i) => (
                                    <li key={i} className="flex items-start gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold text-white">
                                            {i + 1}
                                        </span>
                                        <span className="text-gray-100">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-white/60 italic">Keep practicing to improve further!</p>
                        )}
                    </Card>
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
                    <Button size="lg" onClick={() => navigate('/assessment')}>
                        Take New Assessment
                    </Button>
                </motion.div>
            </div>
        </div>
    );
};

export default Results;
