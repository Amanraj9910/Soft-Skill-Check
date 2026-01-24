import { motion } from 'framer-motion';

const AimStage = () => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full justify-center items-center p-8 text-center"
        >
            <div className="inline-block px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold tracking-wider uppercase border border-slate-200 mb-6">
                Stage 6: Career Vision
            </div>

            <h2 className="text-3xl font-bold text-slate-900 mb-4">Professional Goals</h2>
            <p className="text-lg text-slate-600 max-w-2xl mb-12">
                Discuss your professional objectives for the next 3-5 years. Focus on leadership aspirations, skill acquisition, and your planned career trajectory.
            </p>

            <div className="grid grid-cols-2 gap-4 max-w-lg w-full">
                {['Leadership', 'Skill Acquisition', 'Industry Impact', 'Innovation'].map((goal, i) => (
                    <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 text-slate-700 font-medium shadow-sm flex items-center justify-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-slate-400"></span> {goal}
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

export default AimStage;
