import { motion } from 'framer-motion';

const OpinionStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center items-center p-8 text-center"
        >
            <div className="inline-block px-4 py-2 bg-teal-50 text-teal-700 rounded-full text-sm font-semibold tracking-wide uppercase mb-6">
                Stage 5: Opinion
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-6">What's Your Opinion?</h2>

            <div className="bg-teal-50 rounded-2xl p-8 max-w-2xl w-full border border-teal-100 mb-8">
                <p className="text-2xl font-serif text-teal-900 leading-relaxed italic">
                    "Technology in Education"
                </p>
            </div>

            <div className="max-w-xl mx-auto text-left space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Consider discussing:</h3>
                <ul className="space-y-2 text-gray-600">
                    <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                        Benefits for students and teachers
                    </li>
                    <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                        Potential drawbacks or challenges
                    </li>
                    <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                        Future trends you foresee
                    </li>
                </ul>
            </div>
        </motion.div>
    );
};

export default OpinionStage;
