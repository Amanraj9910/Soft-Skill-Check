import { motion } from 'framer-motion';

const AimStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center items-center p-8 text-center"
        >
            <div className="inline-block px-4 py-2 bg-rose-50 text-rose-700 rounded-full text-sm font-semibold tracking-wide uppercase mb-6">
                Stage 6: Goals & Aspirations
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-4">Your Journey Ahead</h2>
            <p className="text-xl text-gray-600 max-w-2xl mb-12">
                Share your future goals. Why are you learning English, and what do you hope to achieve?
            </p>

            <div className="grid grid-cols-2 gap-4 max-w-lg w-full">
                {['Career Growth', 'Travel', 'Higher Education', 'Personal Development'].map((goal, i) => (
                    <div key={i} className="bg-white p-4 rounded-xl border border-gray-200 text-gray-700 font-medium shadow-sm flex items-center justify-center gap-2">
                        <span>🎯</span> {goal}
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

export default AimStage;
