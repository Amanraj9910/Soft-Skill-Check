// Input component with label and error states - Interview Theme
import { forwardRef } from 'react';

const Input = forwardRef(({
    label,
    error,
    helperText,
    leftIcon,
    rightIcon,
    fullWidth = true,
    size = 'md',
    className = '',
    ...props
}, ref) => {
    const sizes = {
        sm: 'px-4 py-3 text-sm',
        md: 'px-5 py-4 text-base',
        lg: 'px-6 py-5 text-lg',
    };

    const inputClass = `
    w-full bg-white border-2 rounded-xl
    text-gray-900 placeholder-gray-400
    transition-all duration-200
    focus:outline-none focus:ring-4 focus:ring-red-500/10
    ${error ? 'border-red-500 focus:border-red-500' : 'border-gray-200 focus:border-red-500'}
    ${leftIcon ? 'pl-12' : ''}
    ${rightIcon ? 'pr-12' : ''}
    ${sizes[size]}
    ${className}
  `.trim();

    return (
        <div className={fullWidth ? 'w-full' : ''}>
            {label && (
                <label className="block mb-3 text-sm font-semibold text-gray-700 ml-1">
                    {label}
                </label>
            )}
            <div className="relative">
                {leftIcon && (
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                        {leftIcon}
                    </div>
                )}
                <input
                    ref={ref}
                    className={inputClass}
                    {...props}
                />
                {rightIcon && (
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                        {rightIcon}
                    </div>
                )}
            </div>
            {(error || helperText) && (
                <p className={`mt-2 text-sm ml-1 ${error ? 'text-red-500' : 'text-gray-500'}`}>
                    {error || helperText}
                </p>
            )}
        </div>
    );
});

Input.displayName = 'Input';

export default Input;
