import { motion } from 'framer-motion';
import Card from '../common/Card';

const StorytellingStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full p-8"
        >
            <div className="text-center mb-6">
                <div className="inline-block px-4 py-2 bg-orange-50 text-orange-700 rounded-full text-sm font-semibold tracking-wide uppercase mb-4">
                    Stage 4: Storytelling
                </div>
                <h2 className="text-3xl font-bold text-gray-900">Share a Personal Story</h2>
                <p className="text-gray-600">Think about a time you really enjoyed yourself.</p>
            </div>

            <Card padding="lg" className="shadow-lg max-w-2xl mx-auto w-full bg-white relative group">
                <div className="flex flex-col items-center justify-center p-8 space-y-6">
                    <div className="w-24 h-24 bg-orange-100 rounded-full flex items-center justify-center text-4xl mb-2">
                        🎉
                    </div>
                    <div className="text-center space-y-2">
                        <h3 className="text-xl font-bold text-gray-800">Your Prompt</h3>
                        <p className="text-lg text-gray-600 italic">
                            "Tell me about a personal experience where you enjoyed yourself a lot."
                        </p>
                    </div>
                    <div className="text-sm text-gray-400">
                        Describe what happened, who was there, and why it was special.
                    </div>
                </div>
            </Card>
        </motion.div>
    );
};

export default StorytellingStage;
