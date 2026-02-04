import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { apiService } from '../../services/api';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const StatCard = ({ title, value, subtext, icon, color = 'blue' }) => {
    // Safely handle if value is an object (common Supabase count pattern issue)
    const displayValue = typeof value === 'object' && value !== null
        ? (value.count ?? value.value ?? JSON.stringify(value))
        : value;

    // Extra safety: check for specific object structure reported {name, count}
    // and extract the count if present.
    const finalValue = typeof value === 'object' && value !== null && 'count' in value
        ? value.count
        : displayValue;

    return (
        <div className={`bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden group`}>
            <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity text-${color}-600`}>
                <span className="text-6xl">{icon}</span>
            </div>
            <div className="relative z-10">
                <h3 className="text-gray-500 font-medium text-sm uppercase tracking-wider mb-2">{title}</h3>
                <p className="text-4xl font-bold text-gray-900 mb-2">{typeof finalValue === 'object' ? JSON.stringify(finalValue) : finalValue}</p>
                {subtext && <p className="text-sm text-gray-400">{subtext}</p>}
            </div>
        </div>
    );
};

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await apiService.get('/admin/stats');
            setStats(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch admin stats');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner fullScreen={false} text="Loading dashboard..." />;
    if (error) return (
        <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-100">
            Error: {error}
        </div>
    );

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-gray-500 mt-1">Overview of platform performance</p>
                </div>
                <button
                    onClick={fetchStats}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                >
                    🔄
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Assessments"
                    value={stats?.total_assessments}
                    icon="📝"
                    color="blue"
                />
                <StatCard
                    title="Total Candidates"
                    value={stats?.total_users}
                    icon="👥"
                    color="indigo"
                />
                <StatCard
                    title="Completed Today"
                    value={stats?.assessments_today}
                    subtext="Assessments in last 24h"
                    icon="📅"
                    color="green"
                />
                <StatCard
                    title="Average Score"
                    value={stats?.average_score}
                    subtext="Across all completed"
                    icon="⭐"
                    color="yellow"
                />
            </div>

            {/* Charts/Distribution (Placeholder for now) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">Score Distribution</h3>
                    <div className="space-y-4">
                        {stats?.score_distribution && Object.entries(stats.score_distribution).map(([key, value]) => {
                            const total = Object.values(stats.score_distribution).reduce((a, b) => a + b, 0) || 1;
                            const percentage = Math.round((value / total) * 100);
                            const colors = { low: 'bg-red-500', medium: 'bg-yellow-500', high: 'bg-green-500' };

                            return (
                                <div key={key} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="capitalize font-medium text-gray-700">{key} Scores</span>
                                        <span className="text-gray-500">{value} ({percentage}%)</span>
                                    </div>
                                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${percentage}%` }}
                                            className={`h-full ${colors[key] || 'bg-blue-500'}`}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-900 mb-6">Recent Activity</h3>
                    <div className="flex items-center justify-center h-48 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                        Activity Feed Coming Soon
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
