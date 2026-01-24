// Dashboard Page - Interview Assessment Theme
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { assessmentService } from '../services/assessmentService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner, { SkeletonCard } from '../components/common/LoadingSpinner';

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [assessments, setAssessments] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            const [historyData, statsData] = await Promise.all([
                assessmentService.getAssessmentHistory(5).catch(() => []),
                assessmentService.getUserStats().catch(() => null),
            ]);
            setAssessments(historyData?.assessments || []);
            setStats(statsData);
        } catch (err) {
            console.error('Failed to load dashboard:', err);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score) => {
        if (score >= 80) return 'text-green-600';
        if (score >= 60) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getGrade = (score) => {
        if (score >= 90) return 'A+';
        if (score >= 80) return 'A';
        if (score >= 70) return 'B';
        if (score >= 60) return 'C';
        return 'D';
    };

    const getGradeBg = (score) => {
        if (score >= 80) return 'bg-green-100 text-green-700';
        if (score >= 60) return 'bg-yellow-100 text-yellow-700';
        return 'bg-red-100 text-red-700';
    };

    return (
        <div className="min-h-screen pt-24 pb-16 bg-gray-50">
            <div className="container mx-auto px-6">
                {/* Welcome Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-10"
                >
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Welcome back, {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'}! 👋
                    </h1>
                    <p className="text-gray-600 text-lg">
                        Track your interview preparation progress and start new assessments
                    </p>
                </motion.div>

                {/* Stats Cards */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-10"
                >
                    {[
                        { label: 'Total Assessments', value: stats?.total_assessments || assessments.length || 0, icon: '📊', color: 'bg-red-50 border-red-100' },
                        { label: 'Average Score', value: stats?.average_score ? `${Math.round(stats.average_score)}%` : 'N/A', icon: '⭐', color: 'bg-gray-50 border-gray-100' },
                        { label: 'Best Score', value: stats?.best_score ? `${stats.best_score}%` : 'N/A', icon: '🏆', color: 'bg-gray-50 border-gray-100' },
                        { label: 'Streak', value: stats?.streak ? `${stats.streak} days` : '0 days', icon: '🔥', color: 'bg-red-50 border-red-100' },
                    ].map((stat, i) => (
                        <Card key={i} padding="md" className={`text-center border-2 ${stat.color}`}>
                            <div className="text-3xl mb-3">{stat.icon}</div>
                            <div className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</div>
                            <div className="text-sm text-gray-500 font-medium">{stat.label}</div>
                        </Card>
                    ))}
                </motion.div>

                {/* Quick Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mb-10"
                >
                    <Card variant="gradient" padding="lg">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                            <div className="text-center md:text-left">
                                <h2 className="text-2xl font-bold text-white mb-3">Ready for a Practice Interview?</h2>
                                <p className="text-gray-300">Start a new assessment and improve your speaking skills</p>
                            </div>
                            <Button
                                size="lg"
                                onClick={() => navigate('/assessment')}
                                className="bg-white text-gray-900 hover:bg-gray-100 shadow-lg whitespace-nowrap"
                                rightIcon={
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                }
                            >
                                Start Assessment
                            </Button>
                        </div>
                    </Card>
                </motion.div>

                {/* Recent Assessments */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-gray-900">Recent Assessments</h2>
                    </div>

                    {loading ? (
                        <div className="grid gap-4">
                            {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
                        </div>
                    ) : assessments.length > 0 ? (
                        <div className="grid gap-4">
                            {assessments.map((assessment, i) => (
                                <motion.div
                                    key={assessment.id || i}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 * i }}
                                >
                                    <Card hover padding="md" onClick={() => navigate(`/results/${assessment.id}`)}>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-5">
                                                <div className={`w-16 h-16 rounded-xl flex items-center justify-center text-xl font-bold ${getGradeBg(assessment.total_score)}`}>
                                                    {getGrade(assessment.total_score)}
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-gray-900 text-lg mb-1">
                                                        Assessment #{assessment.id?.slice(-6) || i + 1}
                                                    </h3>
                                                    <p className="text-sm text-gray-500">
                                                        {new Date(assessment.created_at).toLocaleDateString('en-US', {
                                                            month: 'short', day: 'numeric', year: 'numeric'
                                                        })}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className={`text-2xl font-bold ${getScoreColor(assessment.total_score)}`}>
                                                    {assessment.total_score || 0}%
                                                </div>
                                                <div className="text-sm text-gray-500 font-medium">
                                                    {assessment.status || 'Completed'}
                                                </div>
                                            </div>
                                        </div>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <Card padding="lg" className="text-center">
                            <div className="text-6xl mb-6">🎯</div>
                            <h3 className="text-xl font-bold text-gray-900 mb-3">No Assessments Yet</h3>
                            <p className="text-gray-600 mb-6 max-w-md mx-auto">
                                Complete your first interview assessment to see your progress and get personalized feedback
                            </p>
                            <Button onClick={() => navigate('/assessment')}>Start Your First Assessment</Button>
                        </Card>
                    )}
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
