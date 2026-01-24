import { motion } from 'framer-motion';
import Button from '../common/Button';
import Card from '../common/Card';

const WelcomeStage = ({ onStart }) => {
    return (
        <div className="h-full flex flex-col justify-center p-6 bg-slate-50">
            <div className="max-w-3xl w-full mx-auto">
                <Card className="border border-slate-200 shadow-sm bg-white p-8 md:p-12">
                    <div className="mb-8 border-b border-slate-100 pb-6">
                        <h1 className="text-3xl font-bold text-slate-900 mb-2">
                            Assessment Instructions
                        </h1>
                        <p className="text-slate-600">
                            Please read the following guidelines carefully before initializing the session.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 mb-10">
                        <div>
                            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest mb-4">
                                Test Components
                            </h3>
                            <ul className="space-y-3">
                                {[
                                    "Introduction & Background",
                                    "Reading Comprehension",
                                    "Listening Analysis",
                                    "Visual Storytelling",
                                    "Opinion Statement",
                                    "Career Aspirations"
                                ].map((item, i) => (
                                    <li key={i} className="flex items-center text-sm text-slate-700 border-b border-slate-50 pb-2">
                                        <span className="w-6 text-slate-400 font-mono text-xs">0{i + 1}</span>
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest mb-4">
                                Requirements
                            </h3>
                            <div className="space-y-4">
                                <div className="p-4 bg-slate-50 border border-slate-100 rounded">
                                    <div className="font-semibold text-slate-900 text-sm mb-1">Audio & Video</div>
                                    <p className="text-xs text-slate-600">A functioning microphone and camera are required. The session will be recorded for review.</p>
                                </div>
                                <div className="p-4 bg-slate-50 border border-slate-100 rounded">
                                    <div className="font-semibold text-slate-900 text-sm mb-1">Environment</div>
                                    <p className="text-xs text-slate-600">Ensure you are in a quiet, well-lit room. Minimized background noise is essential for AI analysis.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col items-center">
                        <Button
                            size="lg"
                            onClick={onStart}
                            className="bg-red-600 hover:bg-red-700 text-white w-full md:w-auto px-12 py-3 text-base font-semibold shadow-sm"
                        >
                            I Understand - Begin Assessment
                        </Button>
                        <p className="mt-4 text-xs text-slate-400">
                            By clicking "Begin", you consent to audio and video recording for assessment purposes.
                        </p>
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default WelcomeStage;
