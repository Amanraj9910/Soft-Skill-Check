import { motion } from 'framer-motion';
import Card from '../common/Card';

const ReadingStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center p-6 md:p-12 space-y-8"
        >
            <div className="text-center space-y-4">
                <div className="inline-block px-3 py-1 bg-slate-100 text-slate-600 rounded text-xs font-bold tracking-wider uppercase border border-slate-200">
                    Stage 2: Technical Reading
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Passage Recitation</h2>
                <p className="text-slate-500 max-w-lg mx-auto">
                    Read the following text aloud. Focus on clear pronunciation and natural pacing.
                </p>
            </div>

            <Card className="bg-white border text-left border-slate-200 shadow-sm max-w-3xl mx-auto w-full p-8 md:p-12">
                <p className="text-xl md:text-2xl leading-relaxed text-slate-800 font-medium">
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
