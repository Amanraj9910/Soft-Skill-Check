// Landing Page - B2B Interview Assessment Platform
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Button from '../components/common/Button';
import { useAuth } from '../contexts/AuthContext';

const Landing = () => {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();

    const valueProps = [
        {
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            ),
            title: 'Objective Benchmarking',
            description: 'Standardized scoring on fluency, grammar, and vocabulary eliminates subconscious hiring bias.',
        },
        {
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ),
            title: 'Automated Screening',
            description: 'Save 90% of HR time by automating initial communication screenings before human interviews.',
        },
        {
            icon: (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            ),
            title: 'Detailed Candidate Reports',
            description: 'Get deep insights into non-verbal cues, confidence levels, and speech clarity.',
        },
    ];

    const stats = [
        { value: '40%', label: 'Reduction in Hiring Time' },
        { value: '98%', label: 'Assessment Accuracy' },
        { value: '24/7', label: 'Candidate Availability' },
        { value: '10k+', label: 'Interviews Analyzed' },
    ];

    return (
        <div className="min-h-screen bg-white">
            {/* Header / Nav */}
            <nav className="fixed w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
                <div className="container mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center text-white font-bold">
                            <img src="../img/favicon.ico.png" alt="" />
                        </div>
                        <span className="text-xl font-bold text-slate-900 tracking-tight">Hosho Digital</span>
                    </div>
                    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
                        <a href="#solutions" className="hover:text-slate-900 transition-colors">Solutions</a>
                        <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How it Works</a>
                        {/* <a href="#pricing" className="hover:text-slate-900 transition-colors">Pricing</a> */}
                    </div>
                    <div className="flex items-center gap-4">
                        {isAuthenticated ? (
                            <Button size="sm" onClick={() => navigate('/dashboard')} className="bg-slate-900 text-white hover:bg-slate-800">
                                Dashboard
                            </Button>
                        ) : (
                            <>
                                <Button variant="ghost" className="text-slate-600 hover:text-slate-900 font-medium" onClick={() => navigate('/login')}>
                                    Login
                                </Button>
                                <Button size="sm" onClick={() => navigate('/signup')} className="bg-slate-900 text-white hover:bg-slate-800">
                                    Get Started
                                </Button>
                            </>
                        )}
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-slate-50">
                <div className="container mx-auto px-6 text-center max-w-5xl relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-200 text-slate-700 text-sm font-medium mb-8">
                            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
                            Enterprise-Grade Assessment Platform
                        </div>

                        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 mb-6 tracking-tight leading-tight">
                            The Standard for <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-red-800">
                                Interview Communication
                            </span>
                        </h1>

                        <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
                            Evaluate candidate speaking skills objectively. Reduce hiring bias.
                            Save 90% of screening time with automated AI benchmarking.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                            <Button
                                size="lg"
                                className="min-w-[200px] h-14 text-lg bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/20"
                                onClick={() => navigate(isAuthenticated ? '/dashboard' : '/signup')}
                            >
                                Start Free Screening
                            </Button>
                            <Button
                                variant="secondary"
                                size="lg"
                                className="min-w-[200px] h-14 text-lg bg-white border border-slate-200 text-slate-800 hover:bg-slate-50"
                                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                            >
                                Book a Demo
                            </Button>
                        </div>
                    </motion.div>
                </div>

                {/* Abstract decorative elements */}
                <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                    <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] bg-slate-200/50 rounded-full blur-3xl opacity-50" />
                    <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-red-100/50 rounded-full blur-3xl opacity-50" />
                </div>
            </section>

            {/* Stats Band */}
            <div className="bg-white border-y border-slate-100 py-12">
                <div className="container mx-auto px-6">
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
                        {stats.map((stat, i) => (
                            <div key={i} className="text-center">
                                <div className="text-3xl lg:text-4xl font-bold text-slate-900 mb-1">{stat.value}</div>
                                <div className="text-sm text-slate-500 font-medium uppercase tracking-wide">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <section id="features" className="py-24 bg-white">
                <div className="container mx-auto px-6 max-w-7xl">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
                            Data-Driven Hiring Decisions
                        </h2>
                        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                            Stop relying on gut feeling. Use precise metrics to validate candidate communication capabilities.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {valueProps.map((prop, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-300 hover:shadow-lg transition-all duration-300"
                            >
                                <div className="w-12 h-12 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-red-600 mb-6 shadow-sm">
                                    {prop.icon}
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 mb-3">{prop.title}</h3>
                                <p className="text-slate-600 leading-relaxed">{prop.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How it Works / Workflow */}
            <section className="py-24 bg-slate-900 text-white">
                <div className="container mx-auto px-6">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <div>
                            <h2 className="text-3xl md:text-4xl font-bold mb-6">
                                Integrated Assessment Workflow
                            </h2>
                            <p className="text-slate-400 text-lg mb-8 leading-relaxed">
                                Seamlessly integrate SpeakAssess into your existing recruitment pipeline.
                                From invitation to final report, every step is automated.
                            </p>

                            <div className="space-y-6">
                                {[
                                    { step: '01', title: 'Invite Candidates', desc: 'Send bulk invitations via email or ATS integration.' },
                                    { step: '02', title: 'AI Assessment', desc: 'Candidates complete a standardized 15-min interview session.' },
                                    { step: '03', title: 'Review Reports', desc: 'Receive instant scorecards with hiring recommendations.' }
                                ].map((item, i) => (
                                    <div key={i} className="flex gap-6 items-start">
                                        <div className="text-2xl font-bold text-red-500 opacity-60">{item.step}</div>
                                        <div>
                                            <h4 className="text-xl font-bold mb-1">{item.title}</h4>
                                            <p className="text-slate-400">{item.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="relative">
                            <div className="aspect-[4/3] rounded-2xl bg-slate-800 border border-slate-700 p-2 shadow-2xl skew-y-1 transform hover:skew-y-0 transition-transform duration-700">
                                <div className="h-full w-full bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center">
                                    {/* Abstract Dashboard UI */}
                                    <div className="w-3/4 space-y-4 opacity-50">
                                        <div className="h-32 bg-slate-800 rounded-lg w-full animate-pulse"></div>
                                        <div className="flex gap-4">
                                            <div className="h-32 bg-slate-800 rounded-lg w-1/2 animate-pulse"></div>
                                            <div className="h-32 bg-slate-800 rounded-lg w-1/2 animate-pulse"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-white border-t border-slate-100 py-12">
                <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="text-slate-900 font-bold text-xl flex items-center gap-2">
                        <img className="w-6 h-6" src="../img/favicon.ico.png" alt="" />
                        Hosho Digital
                    </div>
                    <div className="text-slate-500 text-sm">
                        &copy; 2026 Hosho DIgital Inc. Enterprise Edition.
                    </div>
                    <div className="flex gap-6 text-sm font-medium text-slate-600">
                        <a href="#" className="hover:text-slate-900">Privacy</a>
                        <a href="#" className="hover:text-slate-900">Security</a>
                        <a href="#" className="hover:text-slate-900">Terms</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Landing;
