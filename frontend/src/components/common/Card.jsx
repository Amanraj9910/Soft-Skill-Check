// Reusable Card component with variants - Interview Theme
import { motion } from 'framer-motion';

const Card = ({
    children,
    variant = 'default', // default, glass, gradient, bordered
    hover = false,
    padding = 'md', // none, sm, md, lg
    className = '',
    onClick,
    ...props
}) => {
    const baseStyles = `
    rounded-2xl transition-all duration-300
  `;

    const variants = {
        default: `
      bg-white border border-gray-200
      shadow-md
    `,
        glass: `
      bg-white/95 backdrop-blur-xl
      border border-gray-200
      shadow-xl
    `,
        gradient: `
      bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900
      border border-gray-700
      shadow-xl
    `,
        bordered: `
      bg-white border-2 border-gray-200
      shadow-sm
    `,
        red: `
      bg-gradient-to-br from-red-600 to-red-700
      border border-red-500/20
      shadow-xl shadow-red-600/10
    `,
    };

    const paddings = {
        none: '',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
    };

    const hoverStyles = hover
        ? 'hover:-translate-y-1 hover:shadow-xl hover:border-red-500/50 cursor-pointer'
        : '';

    const combinedClassName = `
    ${baseStyles}
    ${variants[variant]}
    ${paddings[padding]}
    ${hoverStyles}
    ${className}
  `.trim();

    const MotionComponent = onClick ? motion.button : motion.div;

    return (
        <MotionComponent
            className={combinedClassName}
            onClick={onClick}
            whileHover={hover ? { scale: 1.01 } : undefined}
            whileTap={onClick ? { scale: 0.99 } : undefined}
            {...props}
        >
            {children}
        </MotionComponent>
    );
};

// Card Header component
Card.Header = ({ children, className = '' }) => (
    <div className={`border-b border-gray-200 pb-4 mb-4 ${className}`}>
        {children}
    </div>
);

// Card Body component
Card.Body = ({ children, className = '' }) => (
    <div className={className}>{children}</div>
);

// Card Footer component
Card.Footer = ({ children, className = '' }) => (
    <div className={`border-t border-gray-200 pt-4 mt-4 ${className}`}>
        {children}
    </div>
);

export default Card;
