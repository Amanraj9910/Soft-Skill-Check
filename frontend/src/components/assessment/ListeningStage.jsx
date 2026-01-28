import { motion } from 'framer-motion';
import Card from '../common/Card';

const ListeningStage = ({ status }) => {
    // We infer the current activity from the parent status
    const isListening = status === 'playing_response' || status === 'playing_greeting';
    const isRecording = status === 'recording';
    const isProcessing = status === 'processing';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full items-center justify-center p-6 space-y-8"
        >
            <div className="text-center space-y-3">
                <div className="inline-block px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-bold tracking-wider uppercase border border-blue-100">
                    Stage 3: Listening & Shadowing
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Shadowing Exercise</h2>
                <p className="text-slate-500 max-w-lg mx-auto text-sm">
                    Listen to the sentence, then repeat it exactly. You have <strong>one chance</strong> per sentence.
                </p>
            </div>

            <div className="w-full max-w-md">
                <Card className={`border-2 transition-all duration-300 p-8 flex flex-col items-center justify-center space-y-6 ${isListening ? 'border-blue-400 bg-blue-50/50 scale-105' :
                    isRecording ? 'border-red-400 bg-red-50/50 scale-105' :
                        'border-slate-200 bg-white'
                    }`}>

                    {/* Visual Indicator */}
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 ${isListening ? 'bg-blue-100 text-blue-600 ring-4 ring-blue-100' :
                        isRecording ? 'bg-red-100 text-red-600 ring-4 ring-red-100' :
                            'bg-slate-100 text-slate-400'
                        }`}>
                        {isListening ? (
                            <svg className="w-10 h-10 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>
                        ) : isRecording ? (
                            <svg className="w-10 h-10 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                        ) : (
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full"></div>
                            </div>
                        )}
                    </div>

                    {/* Status Text */}
                    <div className="text-center">
                        <h3 className={`text-xl font-bold transition-colors ${isListening ? 'text-blue-700' :
                            isRecording ? 'text-red-700' :
                                'text-slate-700'
                            }`}>
                            {isListening ? "Listening..." :
                                isRecording ? "Your Turn - Speak!" :
                                    isProcessing ? "Analyzing..." :
                                        "Get Ready"}
                        </h3>
                        <p className="text-slate-500 mt-2 text-sm">
                            {isListening ? "Pay attention to the AI's pronunciation." :
                                isRecording ? "Repeat the sentence clearly." :
                                    "Click 'Start Recording' to repeat."}
                        </p>
                    </div>

                </Card>
            </div>
        </motion.div>
    );
};

export default ListeningStage;
