import { motion } from 'framer-motion';

const ListeningStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center items-center p-8 text-center"
        >
            <div className="inline-block px-4 py-2 bg-indigo-50 text-indigo-700 rounded-full text-sm font-semibold tracking-wide uppercase mb-6">
                Stage 3: Listening
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-6">Listen Carefully</h2>

            <div className="relative w-32 h-32 mb-8">
                <span className="absolute inset-0 rounded-full bg-indigo-100 animate-ping opacity-75"></span>
                <span className="absolute inset-0 rounded-full bg-indigo-200 animate-pulse opacity-75 animation-delay-500"></span>
                <div className="relative bg-white w-full h-full rounded-full flex items-center justify-center shadow-xl border-4 border-indigo-50">
                    <svg className="w-12 h-12 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                </div>
            </div>

            <p className="text-xl text-gray-600 max-w-md leading-relaxed">
                The AI interviewer will ask you a question. Listen carefully and provide a thoughtful response.
            </p>
        </motion.div>
    );
};

export default ListeningStage;
