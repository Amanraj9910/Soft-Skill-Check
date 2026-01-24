import { motion } from 'framer-motion';
import Button from '../common/Button';
import Card from '../common/Card';

const WelcomeStage = ({ onStart }) => {
    return (
        <div className="h-full flex flex-col items-center justify-center p-6 text-center">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="max-w-2xl w-full"
            >
                <Card padding="xl" className="border-none shadow-2xl bg-white/80 backdrop-blur-sm">
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                    >
                        <div className="w-20 h-20 bg-red-100 rounded-3xl flex items-center justify-center mx-auto mb-8 text-4xl shadow-lg shadow-red-100">
                            👋
                        </div>
                        <h1 className="text-4xl font-bold text-gray-900 mb-6 bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
                            Welcome to Your Assessment
                        </h1>
                        <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                            I'm your AI Interviewer. We'll go through a few simple stages to assess your English speaking skills.
                            Relax, speak naturally, and try your best!
                        </p>

                        <div className="grid grid-cols-2 gap-4 mb-10 text-left max-w-lg mx-auto">
                            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="block text-2xl mb-2">⏱️</span>
                                <span className="font-semibold text-gray-900">10-15 Minutes</span>
                                <span className="block text-sm text-gray-500">Total duration</span>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                                <span className="block text-2xl mb-2">🤖</span>
                                <span className="font-semibold text-gray-900">AI Analysis</span>
                                <span className="block text-sm text-gray-500">Real-time feedback</span>
                            </div>
                        </div>

                        <Button
                            size="lg"
                            onClick={onStart}
                            className="bg-gray-900 hover:bg-black text-white px-12 py-4 text-lg shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
                        >
                            Start Assessment
                        </Button>
                    </motion.div>
                </Card>
            </motion.div>
        </div>
    );
};

export default WelcomeStage;
