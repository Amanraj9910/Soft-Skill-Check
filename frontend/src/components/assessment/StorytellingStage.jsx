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
                <h2 className="text-3xl font-bold text-gray-900">Tell a Story</h2>
                <p className="text-gray-600">Describe what you see in the image and weave a short story around it.</p>
            </div>

            <Card padding="none" className="overflow-hidden shadow-lg max-w-2xl mx-auto w-full aspect-video bg-gray-100 relative group">
                <img
                    src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80"
                    alt="Story Prompt"
                    className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-6">
                    <p className="text-white text-lg font-medium">Scenario: A team collaborating on a project.</p>
                </div>
            </Card>
        </motion.div>
    );
};

export default StorytellingStage;
