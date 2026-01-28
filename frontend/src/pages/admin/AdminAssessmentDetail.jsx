import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { motion, AnimatePresence } from 'framer-motion';

const ScoreBadge = ({ label, score, max = 10, color = 'blue' }) => {
    const percentage = (score / max) * 100;
    return (
        <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs font-medium text-gray-500">
                <span>{label}</span>
                <span>{score}/{max}</span>
            </div>
            <div className={`h-1.5 w-full bg-gray-100 rounded-full overflow-hidden`}>
                <div
                    className={`h-full bg-${color}-500 rounded-full`}
                    style={{ width: `${Math.min(100, percentage)}%` }}
                />
            </div>
        </div>
    );
};

const ResponseCard = ({ response, assessmentId }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [audioUrl, setAudioUrl] = useState(null);
    const [loadingAudio, setLoadingAudio] = useState(false);

    const toggleOpen = () => {
        setIsOpen(!isOpen);
        if (!isOpen && !audioUrl && !loadingAudio) {
            fetchAudio();
        }
    };

    const fetchAudio = async () => {
        try {
            setLoadingAudio(true);
            const data = await apiService.get(`/admin/assessments/${assessmentId}/audio/${response.section}`);
            setAudioUrl(data.url);
        } catch (err) {
            console.error("Failed to load audio", err);
        } finally {
            setLoadingAudio(false);
        }
    };

    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden bg-white mb-4">
            <button
                onClick={toggleOpen}
                className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
            >
                <div className="flex items-center gap-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${isOpen ? 'bg-red-100 text-red-700' : 'bg-gray-200 text-gray-600'
                        }`}>
                        {response.section.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 capitalize">{response.section.replace(/_/g, ' ')}</h4>
                        <p className="text-xs text-gray-500">{new Date(response.created_at).toLocaleTimeString()}</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {response.pronunciation_score && (
                        <div className="text-sm">
                            <span className="text-gray-500">Score: </span>
                            <span className="font-bold text-gray-900">{response.pronunciation_score.toFixed(1)}</span>
                        </div>
                    )}
                    <svg
                        className={`w-5 h-5 text-gray-400 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="p-6 border-t border-gray-100 space-y-6">
                            {/* Audio Player */}
                            <div className="bg-gray-50 p-4 rounded-lg">
                                <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Audio Recording</h5>
                                {loadingAudio ? (
                                    <div className="flex items-center gap-2 text-sm text-gray-500">
                                        <LoadingSpinner size="sm" /> Loading audio...
                                    </div>
                                ) : audioUrl ? (
                                    <audio controls className="w-full h-10">
                                        <source src={audioUrl} type="audio/wav" />
                                        Your browser does not support the audio element.
                                    </audio>
                                ) : (
                                    <p className="text-sm text-red-500">Audio unavailable</p>
                                )}
                            </div>

                            {/* Transcript */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Question / Prompt</h5>
                                    <div className="p-3 bg-blue-50 text-blue-900 rounded-lg text-sm">
                                        {response.question_text || "No question text available."}
                                    </div>
                                </div>
                                <div>
                                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">User Response</h5>
                                    <div className="p-3 bg-white border border-gray-200 rounded-lg text-sm text-gray-800">
                                        {response.user_transcript || <span className="text-gray-400 italic">No transcript available</span>}
                                    </div>
                                </div>
                            </div>

                            {/* AI Analysis (Mocked if not in response) */}
                            <div>
                                <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">AI Analysis</h5>
                                <div className="p-3 bg-yellow-50 border border-yellow-100 rounded-lg text-sm text-yellow-800">
                                    <p>{response.feedback || "Automated analysis not available for this section."}</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const AdminAssessmentDetail = () => {
    const { id } = useParams();
    const [details, setDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDetails();
    }, [id]);

    const fetchDetails = async () => {
        try {
            setLoading(true);
            const data = await apiService.get(`/admin/assessments/${id}`);
            setDetails(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch assessment details');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner fullScreen={false} text="Loading details..." />;
    if (error) return (
        <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-100">
            Error: {error}
        </div>
    );
    if (!details) return null;

    const { assessment, user, scores, responses } = details;

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            {/* Header */}
            <div>
                <Link to="/admin/assessments" className="text-sm text-gray-500 hover:text-red-600 mb-4 inline-block">
                    ← Back to Assessments
                </Link>
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">Assessment Details</h1>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                                {new Date(assessment.created_at).toLocaleString()}
                            </span>
                            <span className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                                ID: {assessment.id.slice(0, 8)}...
                            </span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${assessment.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                            }`}>
                            {assessment.status.replace('_', ' ').toUpperCase()}
                        </div>
                    </div>
                </div>
            </div>

            {/* Candidate Info */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-6">
                <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-2xl font-bold text-gray-500">
                    {(user.full_name || user.email || '?').charAt(0).toUpperCase()}
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-900">{user.full_name || 'Unknown Candidate'}</h2>
                    <p className="text-gray-500">{user.email}</p>
                    <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-gray-400">User since {new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            </div>

            {/* Scores Overview */}
            {scores && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className=" bg-gradient-to-br from-gray-900 to-gray-800 text-white p-6 rounded-2xl shadow-lg">
                        <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-1">Overall Score</h3>
                        <div className="flex items-baseline gap-2">
                            <span className="text-5xl font-bold">{scores.total_score?.toFixed(1) || 'N/A'}</span>
                            <span className="text-gray-400">/ 100</span>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-700">
                            <div className="flex justify-between items-center">
                                <span className="text-gray-300">Grade</span>
                                <span className="px-3 py-1 bg-white/10 rounded-full text-sm font-medium">
                                    {scores.grade?.replace('_', ' ').toUpperCase() || 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="md:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="font-bold text-gray-900 mb-4">Detailed Breakdown</h3>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-6">
                            <ScoreBadge label="Fluency" score={scores.fluency_score} max={20} color="blue" />
                            <ScoreBadge label="Pronunciation" score={scores.pronunciation_score} max={10} color="green" />
                            <ScoreBadge label="Grammar" score={scores.grammar_score} max={10} color="purple" />
                            <ScoreBadge label="Confidence" score={scores.confidence_score} max={20} color="orange" />
                            <ScoreBadge label="Storytelling" score={scores.storytelling_score} max={20} color="indigo" />
                            <ScoreBadge label="Vision" score={scores.vision_clarity_score} max={10} color="teal" />
                        </div>
                    </div>
                </div>
            )}

            {/* AI Feedback */}
            {scores && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="font-bold text-green-700 mb-4 flex items-center gap-2">
                            <span>💪</span> Strengths
                        </h3>
                        <ul className="space-y-2">
                            {scores.strengths?.length > 0 ? (
                                scores.strengths.map((s, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                        <span className="text-green-500 mt-1">•</span>
                                        {s}
                                    </li>
                                ))
                            ) : (
                                <li className="text-gray-400 italic">No feedback available</li>
                            )}
                        </ul>
                    </div>
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="font-bold text-red-700 mb-4 flex items-center gap-2">
                            <span>🎯</span> Areas for Improvement
                        </h3>
                        <ul className="space-y-2">
                            {scores.weaknesses?.length > 0 ? (
                                scores.weaknesses.map((w, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                        <span className="text-red-500 mt-1">•</span>
                                        {w}
                                    </li>
                                ))
                            ) : (
                                <li className="text-gray-400 italic">No feedback available</li>
                            )}
                        </ul>
                    </div>
                </div>
            )}

            {/* Stage Responses */}
            <div>
                <h3 className="text-xl font-bold text-gray-900 mb-6">Response Timeline</h3>
                <div className="space-y-0">
                    {responses.length > 0 ? (
                        responses.map((resp) => (
                            <ResponseCard key={resp.id} response={resp} assessmentId={id} />
                        ))
                    ) : (
                        <div className="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-8 text-center text-gray-500">
                            No responses recorded for this assessment.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminAssessmentDetail;
