// Reusable Button component with variants and states - Interview Theme
import { motion } from 'framer-motion';

const Button = ({
    children,
    variant = 'primary', // primary, secondary, ghost, danger
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
    rounded-xl transition-all duration-200 cursor-pointer
    disabled:opacity-50 disabled:cursor-not-allowed
    focus:outline-none focus:ring-2 focus:ring-offset-2
  `;

    const variants = {
        primary: `
      bg-gradient-to-r from-red-600 to-red-700
      text-white shadow-lg shadow-red-600/25
      hover:shadow-xl hover:shadow-red-600/35 hover:-translate-y-0.5
      focus:ring-red-500
    `,
        secondary: `
      bg-white text-gray-900
      border-2 border-gray-200
      hover:border-red-500 hover:text-red-600 hover:bg-gray-50
      focus:ring-red-500
    `,
        ghost: `
      bg-transparent text-gray-600
      hover:bg-gray-100 hover:text-gray-900
      focus:ring-gray-500
    `,
        danger: `
      bg-gradient-to-r from-red-600 to-red-700
      text-white shadow-lg shadow-red-600/30
      hover:shadow-xl hover:shadow-red-600/40 hover:-translate-y-0.5
      focus:ring-red-500
    `,
        dark: `
      bg-gradient-to-r from-gray-800 to-gray-900
      text-white shadow-lg shadow-gray-900/30
      hover:shadow-xl hover:shadow-gray-900/40 hover:-translate-y-0.5
      focus:ring-gray-700
    `,
    };

    const sizes = {
        sm: 'px-5 py-2.5 text-sm',
        md: 'px-7 py-3.5 text-base',
        lg: 'px-9 py-4 text-lg',
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
                    className="animate-spin h-5 w-5"
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
