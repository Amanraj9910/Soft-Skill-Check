// Landing Page - Interview Assessment Platform
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Button from '../components/common/Button';
import { useAuth } from '../contexts/AuthContext';

const Landing = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    const features = [
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
            ),
            title: 'AI Speech Analysis',
            description: 'Advanced AI analyzes your pronunciation, fluency, and grammar in real-time.',
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
            ),
            title: 'Confidence Tracking',
            description: 'Video analysis tracks your eye contact, posture, and body language.',
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            ),
            title: 'Detailed Scoring',
            description: 'Get scores across 7 categories: fluency, grammar, confidence, vocabulary, and more.',
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
            ),
            title: 'AI Interviewer',
            description: 'Practice with an intelligent AI interviewer through realistic conversation scenarios.',
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
            ),
            title: 'Instant Results',
            description: 'Receive immediate feedback with actionable recommendations.',
        },
        {
            icon: (
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ),
            title: 'Progress Tracking',
            description: 'Monitor your improvement over time with detailed analytics and history.',
        },
    ];

    const assessmentStages = [
        { name: 'Introduction', description: 'Introduce yourself professionally' },
        { name: 'Reading', description: 'Read a passage aloud clearly' },
        { name: 'Listening', description: 'Listen and respond appropriately' },
        { name: 'Storytelling', description: 'Describe scenarios and situations' },
        { name: 'Opinion', description: 'Express your thoughts clearly' },
        { name: 'Goals', description: 'Discuss your career aspirations' },
    ];

    return (
        <div className="min-h-screen bg-white">
            {/* Hero Section */}
            <section className="relative min-h-screen flex items-center justify-center overflow-hidden py-32 md:py-48">
                {/* Background */}
                <div className="absolute inset-0 bg-gray-950" />

                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10" style={{
                    backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                    backgroundSize: '40px 40px'
                }} />

                {/* Animated accent elements - constrained */}
                <div className="absolute inset-0 overflow-hidden max-w-[1400px] mx-auto">
                    <motion.div
                        className="absolute top-20 right-0 w-[500px] h-[500px] bg-red-600/10 rounded-full blur-[100px]"
                        animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.2, 0.1] }}
                        transition={{ duration: 15, repeat: Infinity }}
                    />
                    <motion.div
                        className="absolute bottom-20 left-0 w-[600px] h-[600px] bg-indigo-900/20 rounded-full blur-[120px]"
                        animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.2, 0.1] }}
                        transition={{ duration: 18, repeat: Infinity, delay: 1 }}
                    />
                </div>

                {/* Content */}
                <div className="relative z-10 container mx-auto px-6 text-center max-w-5xl">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 backdrop-blur-md rounded-full border border-white/10 mb-8 hover:bg-white/10 transition-colors cursor-default">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                            </span>
                            <span className="text-sm font-medium text-gray-200">AI-Powered Assessment</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-white mb-8 tracking-tight leading-tight">
                            Ace Your <br className="hidden md:block" />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-500">
                                English Interview
                            </span>
                        </h1>

                        <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto mb-12 leading-relaxed font-light">
                            Practice with our intelligent AI interviewer and receive comprehensive, real-time feedback on your pronunciation, fluency, and confidence.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-20">
                            <Button
                                size="lg"
                                className="min-w-[200px] text-lg py-4 shadow-xl shadow-red-900/20"
                                onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
                                rightIcon={
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                }
                            >
                                {isAuthenticated ? 'Go to Dashboard' : 'Start Assessment'}
                            </Button>
                            <Button
                                variant="secondary"
                                size="lg"
                                className="min-w-[200px] text-lg py-4 bg-transparent border-white/20 text-white hover:bg-white/10 hover:border-white/40 hover:text-white"
                                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                            >
                                How It Works
                            </Button>
                        </div>
                    </motion.div>

                    {/* Stats */}
                    <div className="border-t border-white/10 pt-12">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.3 }}
                            className="grid grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12"
                        >
                            {[
                                { value: '7+', label: 'Assessment Stages' },
                                { value: 'AI', label: 'Real-time Analysis' },
                                { value: '98%', label: 'Score Accuracy' },
                                { value: '24/7', label: 'Instant Feedback' },
                            ].map((stat, i) => (
                                <div key={i} className="text-center group cursor-default">
                                    <div className="text-4xl md:text-5xl font-bold text-white mb-2 group-hover:text-red-400 transition-colors duration-300">{stat.value}</div>
                                    <div className="text-base text-gray-400 font-medium tracking-wide uppercase">{stat.label}</div>
                                </div>
                            ))}
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-24 md:py-32 bg-gray-50">
                <div className="container mx-auto px-6 max-w-7xl">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                        viewport={{ once: true }}
                        className="text-center mb-20"
                    >
                        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 tracking-tight">
                            Why Choose Our Platform?
                        </h2>
                        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
                            We combine advanced speech recognition with video analysis to provide the most comprehensive interview preparation available.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10">
                        {features.map((feature, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: i * 0.1 }}
                                viewport={{ once: true }}
                                className="p-8 lg:p-10 rounded-[2rem] bg-white border border-gray-100 hover:border-red-100 hover:shadow-xl hover:shadow-red-900/5 transition-all duration-300 group"
                            >
                                <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center text-red-600 mb-8 group-hover:scale-110 group-hover:bg-red-600 group-hover:text-white transition-all duration-300">
                                    {feature.icon}
                                </div>
                                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                                    {feature.title}
                                </h3>
                                <p className="text-gray-600 text-lg leading-relaxed">
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Assessment Process Section */}
            <section className="py-24 md:py-32 bg-white">
                <div className="container mx-auto px-6 max-w-6xl">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                            viewport={{ once: true }}
                        >
                            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8 tracking-tight">
                                How the Assessment Works
                            </h2>
                            <p className="text-xl text-gray-600 mb-12 leading-relaxed">
                                Our structured assessment guides you through 6 key stages designed to evaluate every aspect of your professional English communication skills.
                            </p>
                            <Button size="lg" className="text-lg px-8" onClick={() => navigate('/assessment')}>
                                Try It Yourself
                            </Button>
                        </motion.div>

                        <div className="relative">
                            <div className="absolute left-[27px] top-4 bottom-4 w-0.5 bg-gray-100" />
                            <div className="space-y-8">
                                {assessmentStages.map((stage, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: 20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        transition={{ duration: 0.5, delay: i * 0.1 }}
                                        viewport={{ once: true }}
                                        className="relative flex items-center gap-6 group cursor-default"
                                    >
                                        <div className="relative z-10 w-14 h-14 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center text-lg font-bold text-gray-400 group-hover:border-red-500 group-hover:text-red-600 transition-colors duration-300 shadow-sm">
                                            {i + 1}
                                        </div>
                                        <div className="flex-1 p-6 rounded-2xl bg-gray-50 border border-transparent group-hover:bg-white group-hover:border-gray-100 group-hover:shadow-lg transition-all duration-300">
                                            <h3 className="text-lg font-bold text-gray-900 mb-1">{stage.name}</h3>
                                            <p className="text-gray-600">{stage.description}</p>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-32 bg-gray-900 relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10" style={{
                    backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                    backgroundSize: '40px 40px'
                }} />

                <div className="container mx-auto px-6 text-center relative z-10 max-w-4xl">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 tracking-tight">
                            Ready to Ace Your Next Interview?
                        </h2>
                        <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
                            Join thousands of candidates who have improved their English speaking skills with our AI assessment.
                        </p>
                        <Button
                            size="lg"
                            className="text-xl py-5 px-12 shadow-xl shadow-red-900/30 hover:scale-105 transition-transform"
                            onClick={() => navigate(isAuthenticated ? '/assessment' : '/signup')}
                        >
                            Start Free Assessment Now
                        </Button>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 bg-gray-950 border-t border-gray-900">
                <div className="container mx-auto px-6">
                    <div className="flex flex-col md:flex-row justify-between items-center gap-8">
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center text-white">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                </svg>
                            </div>
                            <span className="font-bold text-xl text-white">SpeakAssess</span>
                        </div>
                        <p className="text-gray-500 text-sm">
                            © 2026 SpeakAssess. All rights reserved.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
