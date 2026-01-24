import { motion } from 'framer-motion';

const IntroductionStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center p-8 space-y-8"
        >
            <div className="text-center space-y-4">
                <div className="inline-block px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold tracking-wider uppercase border border-slate-200">
                    Stage 1: Professional Introduction
                </div>
                <h2 className="text-3xl font-bold text-slate-900">Professional Background</h2>
                <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
                    Please provide a brief professional introduction. Focus on your current role, key expertise, and significant career achievements.
                </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto w-full">
                {['Current Role', 'Key Expertise', 'Achievements'].map((hint, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + (i * 0.1) }}
                        className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm text-center hover:border-slate-300 transition-colors"
                    >
                        <div className="w-8 h-8 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-500 font-bold text-sm border border-slate-100">
                            {i + 1}
                        </div>
                        <span className="font-semibold text-slate-700">{hint}</span>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    );
};

export default IntroductionStage;
