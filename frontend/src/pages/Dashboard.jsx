// Dashboard Page - B2B Candidate Overview
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { assessmentService } from '../services/assessmentService';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Dashboard = () => {
    const { user, userProfile } = useAuth();
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
                assessmentService.getAssessmentHistory(10).catch(() => []),
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

    // Determine if candidate is at their assessment limit
    const isCandidate = userProfile?.role === 'candidate';
    const attemptCount = (stats?.completed_assessments || 0) + (stats?.in_progress_assessments || 0) + (stats?.abandoned_assessments || 0);
    const isAtLimit = isCandidate && attemptCount >= 2;
    const attemptsRemaining = isCandidate ? Math.max(0, 2 - attemptCount) : null;

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'bg-green-100 text-green-700 border-green-200';
            case 'in_progress': return 'bg-blue-100 text-blue-700 border-blue-200';
            case 'abandoned': return 'bg-orange-100 text-orange-700 border-orange-200';
            default: return 'bg-slate-100 text-slate-700 border-slate-200';
        }
    };

    const getStatusLabel = (status) => {
        switch (status) {
            case 'completed': return 'Finalized';
            case 'in_progress': return 'Running';
            case 'abandoned': return 'Abandoned';
            case 'cancelled': return 'Cancelled';
            default: return status;
        }
    };

    return (
        <div className="min-h-screen pt-24 pb-16 bg-white">
            <div className="container mx-auto px-6 max-w-6xl">
                {/* Header Section */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row justify-between items-end mb-12 border-b border-slate-100 pb-8"
                >
                    <div className="space-y-1">
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
                            Assessment Portal
                        </h1>
                        <p className="text-slate-500 font-medium">
                            Candidate ID: <span className="text-slate-900 font-mono text-sm bg-slate-100 px-2 py-0.5 rounded">{user?.email}</span>
                        </p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                        <Button
                            size="lg"
                            onClick={() => navigate('/assessment')}
                            disabled={isAtLimit}
                            className={`rounded-md font-semibold px-8 shadow-sm ${isAtLimit
                                    ? 'bg-slate-300 text-slate-500 cursor-not-allowed hover:bg-slate-300'
                                    : 'bg-red-600 hover:bg-red-700 text-white'
                                }`}
                        >
                            {isAtLimit ? '✕ Limit Reached' : '+ Initialize Assessment'}
                        </Button>
                        {isCandidate && (
                            <span className={`text-xs font-medium ${isAtLimit ? 'text-red-600' : 'text-slate-500'
                                }`}>
                                {isAtLimit
                                    ? 'Maximum 2 attempts used'
                                    : `${attemptsRemaining} attempt${attemptsRemaining !== 1 ? 's' : ''} remaining`
                                }
                            </span>
                        )}
                    </div>
                </motion.div>

                {/* KPI Section - Strictly Professional */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16"
                >
                    <div className="p-6 border-l-4 border-slate-900 bg-slate-50 rounded-r-lg">
                        <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Completed</div>
                        <div className="text-4xl font-bold text-slate-900">{stats?.completed_assessments || 0}</div>
                    </div>
                    <div className="p-6 border-l-4 border-red-600 bg-red-50/10 rounded-r-lg">
                        <div className="text-xs font-bold text-red-700 uppercase tracking-widest mb-2">Pending / In Progress</div>
                        <div className="text-4xl font-bold text-red-700">{stats?.in_progress_assessments || 0}</div>
                    </div>
                    <div className="p-6 border-l-4 border-orange-500 bg-orange-50/10 rounded-r-lg">
                        <div className="text-xs font-bold text-orange-700 uppercase tracking-widest mb-2">Abandoned</div>
                        <div className="text-4xl font-bold text-orange-700">{stats?.abandoned_assessments || 0}</div>
                    </div>
                </motion.div>

                {/* Recent Activity Table */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                >
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-bold text-slate-900 text-lg">History Log</h3>
                    </div>

                    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                        {loading ? (
                            <div className="p-12 flex justify-center">
                                <LoadingSpinner size="md" />
                            </div>
                        ) : assessments.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                                            <th className="px-6 py-4">Reference ID</th>
                                            <th className="px-6 py-4">Date Logged</th>
                                            <th className="px-6 py-4">Status</th>
                                            <th className="px-6 py-4">Score</th>
                                            <th className="px-6 py-4 text-right">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {assessments.map((assessment) => (
                                            <tr key={assessment.id} className="hover:bg-slate-50 transition-colors group">
                                                <td className="px-6 py-4 text-slate-600 font-mono text-xs">
                                                    {assessment.id.slice(0, 8).toUpperCase()}
                                                </td>
                                                <td className="px-6 py-4 text-slate-900 text-sm font-medium">
                                                    {(() => {
                                                        try {
                                                            const date = new Date(assessment.created_at);
                                                            return isNaN(date.getTime())
                                                                ? 'Just now'
                                                                : date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                                                        } catch (e) {
                                                            return 'Just now';
                                                        }
                                                    })()}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold uppercase tracking-wide border ${getStatusColor(assessment.status)}`}>
                                                        {getStatusLabel(assessment.status)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-slate-900 font-bold">
                                                    {assessment.total_score ? `${Math.round(assessment.total_score)}%` : '—'}
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    {assessment.status === 'completed' && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => navigate(`/results/${assessment.id}`)}
                                                            className="text-slate-500 hover:text-red-600 font-medium text-sm"
                                                        >
                                                            View Report →
                                                        </Button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="p-16 text-center border-t border-slate-100">
                                <h3 className="text-slate-900 font-semibold mb-2">No Records Found</h3>
                                <p className="text-slate-500 text-sm mb-6">Initialize a new candidate assessment to generate data.</p>
                                {isAtLimit ? (
                                    <p className="text-red-600 text-sm font-medium">
                                        You have reached the maximum of 2 assessment attempts.
                                    </p>
                                ) : (
                                    <Button onClick={() => navigate('/assessment')} className="bg-slate-900 text-white hover:bg-black">
                                        Start Session
                                    </Button>
                                )}
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
