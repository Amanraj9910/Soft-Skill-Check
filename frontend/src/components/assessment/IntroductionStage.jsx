import { motion } from 'framer-motion';

const IntroductionStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center p-8 space-y-8"
        >
            <div className="text-center space-y-6">
                <div className="inline-block px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold tracking-wider uppercase border border-slate-200">
                    Stage 1: Introduction
                </div>
                <h2 className="text-3xl font-bold text-slate-900">AI Assessment Started</h2>
                <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
                    The AI will ask you a question. You can answer by clicking on the <strong>Start Recording</strong> button.
                </p>
            </div>
        </motion.div>
    );
};

export default IntroductionStage;
