// Reusable Button component - Professional Theme
import { motion } from 'framer-motion';

const Button = ({
    children,
    variant = 'primary', // primary, secondary, ghost, danger, dark
    size = 'md', // sm, md, lg
    disabled = false,
    loading = false,
    leftIcon,
    rightIcon,
    fullWidth = false,
    type = 'button',
    onClick,
    className = '',
    ...props
}) => {
    const baseStyles = `
    inline-flex items-center justify-center gap-2 font-semibold
    rounded transition-all duration-200 cursor-pointer
    disabled:opacity-50 disabled:pointer-events-none
    focus:outline-none focus:ring-2 focus:ring-offset-2
  `;

    const variants = {
        primary: `
      bg-red-600 text-white
      hover:bg-red-700
      active:bg-red-800
      focus:ring-red-500
      shadow-sm
    `,
        secondary: `
      bg-white text-slate-700
      border border-slate-300
      hover:bg-slate-50 hover:text-slate-900 hover:border-slate-400
      focus:ring-slate-500
      shadow-sm
    `,
        ghost: `
      bg-transparent text-slate-600
      hover:bg-slate-100 hover:text-slate-900
      focus:ring-slate-500
    `,
        danger: `
      bg-red-600 text-white
      hover:bg-red-700
      focus:ring-red-500
      shadow-sm
    `,
        dark: `
      bg-slate-900 text-white
      hover:bg-black
      focus:ring-slate-700
      shadow-sm
    `,
    };

    const sizes = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-2.5 text-sm',
        lg: 'px-8 py-3 text-base',
    };

    const combinedClassName = `
    ${baseStyles}
    ${variants[variant]}
    ${sizes[size]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim();

    return (
        <motion.button
            type={type}
            disabled={disabled || loading}
            onClick={onClick}
            className={combinedClassName}
            whileTap={{ scale: disabled ? 1 : 0.98 }}
            {...props}
        >
            {loading ? (
                <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                >
                    <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                    />
                    <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                </svg>
            ) : (
                leftIcon
            )}
            {children}
            {!loading && rightIcon}
        </motion.button>
    );
};

export default Button;
