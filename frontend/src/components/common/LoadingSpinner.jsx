// Loading Spinner component with variants - Interview Theme
import { motion } from 'framer-motion';

const LoadingSpinner = ({
    size = 'md', // sm, md, lg, xl
    variant = 'primary', // primary, white, red
    text = '',
    fullScreen = false,
    className = '',
}) => {
    const sizes = {
        sm: { spinner: 'w-5 h-5', text: 'text-sm' },
        md: { spinner: 'w-8 h-8', text: 'text-base' },
        lg: { spinner: 'w-12 h-12', text: 'text-lg' },
        xl: { spinner: 'w-16 h-16', text: 'text-xl' },
    };

    const variants = {
        primary: 'border-red-600 border-t-transparent',
        white: 'border-white border-t-transparent',
        red: 'border-red-600 border-t-transparent',
    };

    const spinnerContent = (
        <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
            <motion.div
                className={`${sizes[size].spinner} border-4 rounded-full ${variants[variant]}`}
                animate={{ rotate: 360 }}
                transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
            />
            {text && (
                <p className={`${sizes[size].text} text-gray-500 animate-pulse font-medium`}>
                    {text}
                </p>
            )}
        </div>
    );

    if (fullScreen) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/90 backdrop-blur-sm">
                {spinnerContent}
            </div>
        );
    }

    return spinnerContent;
};

// Skeleton loading component
export const Skeleton = ({
    width = '100%',
    height = '1rem',
    rounded = 'md',
    className = '',
}) => {
    const roundedClasses = {
        none: 'rounded-none',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        xl: 'rounded-xl',
        full: 'rounded-full',
    };

    return (
        <div
            className={`bg-gray-100 animate-pulse ${roundedClasses[rounded]} ${className}`}
            style={{ width, height }}
        />
    );
};

// Skeleton group for cards
export const SkeletonCard = ({ lines = 3 }) => (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4 shadow-sm">
        <Skeleton height="1.5rem" width="60%" rounded="md" />
        {Array.from({ length: lines }).map((_, i) => (
            <Skeleton key={i} height="1rem" width={i === lines - 1 ? '80%' : '100%'} rounded="md" />
        ))}
    </div>
);

export default LoadingSpinner;
