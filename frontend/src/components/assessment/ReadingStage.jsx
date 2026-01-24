import { motion } from 'framer-motion';
import Card from '../common/Card';

const ReadingStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full p-8"
        >
            <div className="text-center mb-8">
                <div className="inline-block px-4 py-2 bg-purple-50 text-purple-700 rounded-full text-sm font-semibold tracking-wide uppercase mb-4">
                    Stage 2: Reading
                </div>
                <h2 className="text-3xl font-bold text-gray-900">Read the Passage Aloud</h2>
                <p className="text-gray-600 mt-2">Read the text clearly at your natural pace.</p>
            </div>

            <Card padding="xl" className="bg-gradient-to-br from-gray-50 to-white border-2 border-gray-100 shadow-lg max-w-3xl mx-auto w-full">
                <p className="text-xl md:text-2xl leading-loose font-serif text-gray-800">
                    "Artificial intelligence is transforming the way we learn and work.
                    It offers new opportunities for personalized education and efficient problem-solving.
                    However, as we embrace these technologies, it is important to consider the ethical implications
                    and ensure that they are used to benefit all of humanity."
                </p>
            </Card>
        </motion.div>
    );
};

export default ReadingStage;
