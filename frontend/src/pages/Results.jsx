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
    const offset = circumference - (score / 100) * circumference;

    // Determine color based on score
    let strokeColor = '#dc2626'; // Red (default/low)
    if (score >= 80) strokeColor = '#16a34a'; // Green
    else if (score >= 60) strokeColor = '#ca8a04'; // Yellow

    return (
        <div className="flex flex-col items-center">
            <div className="score-circle mb-3">
                <svg className="w-full h-full">
                    <circle cx="48" cy="48" r="40" strokeWidth="8" fill="none" className="score-circle-bg" />
                    <motion.circle
                        cx="48" cy="48" r="40"
                        stroke={strokeColor}
                        strokeWidth="8" fill="none"
                        className="score-circle-fill"
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 1, ease: "easeOut" }}
                    />
                </svg>
                <div className="score-circle-text">
                    {score}%
                </div>
            </div>
            <span className="text-sm font-semibold text-gray-700 text-center">{label}</span>
        </div>
    );
};

const Results = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadResults();
    }, [id]);

    const loadResults = async () => {
        try {
            // Try to fetch from API, fallback to demo data
            const data = await assessmentService.getAssessmentScore(id).catch(() => null);

            if (data) {
                setResult(data);
            } else {
                // Demo data
                setResult({
                    total_score: 78,
                    grade: 'B+',
                    scores: {
                        fluency: 82, pronunciation: 75, grammar: 80,
                        confidence: 72, vocabulary: 85, storytelling: 70, clarity: 82
                    },
                    strengths: ['Good vocabulary usage', 'Clear pronunciation', 'Confident delivery'],
                    improvements: ['Work on complex grammar', 'Reduce filler words', 'Improve storytelling flow'],
                    recommendations: [
                        'Practice speaking for 15 minutes daily',
                        'Record yourself and listen back',
                        'Focus on reducing pauses and hesitations'
                    ]
                });
            }
        } catch (err) {
            console.error('Failed to load results:', err);
        } finally {
            setLoading(false);
        }
    };

    const getGradeColorClass = (grade) => {
        if (grade?.startsWith('A')) return 'grade-badge-a';
        if (grade?.startsWith('B')) return 'grade-badge-b';
        if (grade?.startsWith('C')) return 'grade-badge-c';
        return 'grade-badge-d';
    };

    if (loading) {
        return <LoadingSpinner fullScreen text="Calculating your scores..." />;
    }

    if (!result) {
        return (
            <div className="min-h-screen pt-24 pb-16 flex items-center justify-center bg-gray-50">
                <Card padding="lg" className="text-center max-w-md">
                    <h2 className="text-2xl font-bold text-gray-900 mb-3">Results Not Found</h2>
                    <p className="text-gray-600 mb-6">Unable to load assessment results.</p>
                    <Button onClick={() => navigate('/dashboard')}>Go to Dashboard</Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen pt-24 pb-16 bg-gray-50">
            <div className="container mx-auto px-6 max-w-5xl">
                {/* Header with Total Score */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-12"
                >
                    <div className={`grade-badge ${getGradeColorClass(result.grade)} mx-auto mb-6`}>
                        {result.grade}
                    </div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-3">Assessment Complete!</h1>
                    <p className="text-xl text-gray-600">
                        Your overall score: <span className="font-bold text-gray-900">{result.total_score}%</span>
                    </p>
                </motion.div>

                {/* Score Breakdown */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                    <Card padding="lg" className="mb-8">
                        <h2 className="text-xl font-bold text-gray-900 mb-8 border-b border-gray-100 pb-4">
                            Detailed Score Breakdown
                        </h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-8">
                            {Object.entries(result.scores || {}).map(([key, value]) => (
                                <ScoreGauge key={key} label={key.charAt(0).toUpperCase() + key.slice(1)} score={value} />
                            ))}
                        </div>
                    </Card>
                </motion.div>

                {/* Strengths & Improvements */}
                <div className="grid md:grid-cols-2 gap-8 mb-8">
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                        <Card padding="lg" className="h-full border-l-4 border-l-green-500">
                            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <span className="text-2xl">💪</span> Strengths
                            </h3>
                            <ul className="space-y-4">
                                {result.strengths?.map((item, i) => (
                                    <li key={i} className="flex items-start gap-3">
                                        <div className="mt-1 w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0">
                                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                            </svg>
                                        </div>
                                        <span className="text-gray-700 font-medium">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </Card>
                    </motion.div>

                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
                        <Card padding="lg" className="h-full border-l-4 border-l-yellow-500">
                            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <span className="text-2xl">📈</span> Areas for Improvement
                            </h3>
                            <ul className="space-y-4">
                                {result.improvements?.map((item, i) => (
                                    <li key={i} className="flex items-start gap-3">
                                        <div className="mt-1 w-5 h-5 rounded-full bg-yellow-100 text-yellow-600 flex items-center justify-center flex-shrink-0">
                                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                            </svg>
                                        </div>
                                        <span className="text-gray-700 font-medium">{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </Card>
                    </motion.div>
                </div>

                {/* Recommendations */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                    <Card padding="lg" className="mb-10 bg-gradient-to-br from-gray-900 to-gray-800 text-white border-none shadow-xl">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                            <span className="text-2xl">💡</span> Personalized Recommendations
                        </h3>
                        <ul className="space-y-4">
                            {result.recommendations?.map((item, i) => (
                                <li key={i} className="flex items-start gap-4 p-4 bg-white/10 rounded-xl border border-white/10 backdrop-blur-sm">
                                    <span className="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0 shadow-lg shadow-red-600/30">
                                        {i + 1}
                                    </span>
                                    <span className="text-gray-100 text-lg">{item}</span>
                                </li>
                            ))}
                        </ul>
                    </Card>
                </motion.div>

                {/* Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="flex flex-col sm:flex-row gap-6 justify-center"
                >
                    <Button variant="secondary" size="lg" onClick={() => navigate('/dashboard')}>
                        Back to Dashboard
                    </Button>
                    <Button size="lg" onClick={() => navigate('/assessment')}>
                        Take Another Assessment
                    </Button>
                </motion.div>
            </div>
        </div>
    );
};

export default Results;
