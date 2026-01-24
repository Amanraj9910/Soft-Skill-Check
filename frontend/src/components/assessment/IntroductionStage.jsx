import { motion } from 'framer-motion';

const IntroductionStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center p-8 space-y-8"
        >
            <div className="text-center space-y-4">
                <div className="inline-block px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm font-semibold tracking-wide uppercase">
                    Stage 1: Introduction
                </div>
                <h2 className="text-3xl font-bold text-gray-900">Tell Us About Yourself</h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                    Please introduce yourself. You can mention your name, your background, what you do, and some of your hobbies or interests.
                </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto w-full">
                {['Name & Origin', 'Education/Work', 'Hobbies & Interests'].map((hint, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + (i * 0.1) }}
                        className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm text-center"
                    >
                        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3 text-gray-500 font-bold">
                            {i + 1}
                        </div>
                        <span className="font-semibold text-gray-800">{hint}</span>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    );
};

export default IntroductionStage;
