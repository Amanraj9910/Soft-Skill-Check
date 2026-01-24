// Login Page - Interview Assessment Theme
import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [formError, setFormError] = useState('');

    const { signIn, signInWithGoogle, loading, error, clearError } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const from = location.state?.from?.pathname || '/dashboard';

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError('');
        clearError();

        if (!email || !password) {
            setFormError('Please fill in all fields');
            return;
        }

        const { error } = await signIn(email, password);

        if (!error) {
            navigate(from, { replace: true });
        }
    };

    const handleGoogleSignIn = async () => {
        try {
            const { error } = await signInWithGoogle();
            if (error) setFormError(error.message);
        } catch (err) {
            setFormError('Failed to sign in with Google');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center py-20 px-4 relative overflow-hidden bg-gray-900">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                backgroundSize: '40px 40px'
            }} />

            {/* Accent Orbs */}
            <motion.div
                className="absolute -top-20 -right-20 w-[400px] h-[400px] bg-red-600/20 rounded-full blur-[100px]"
                animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.3, 0.2] }}
                transition={{ duration: 12, repeat: Infinity }}
            />
            <motion.div
                className="absolute bottom-0 -left-20 w-[600px] h-[600px] bg-red-900/15 rounded-full blur-[120px]"
                animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.2, 0.1] }}
                transition={{ duration: 15, repeat: Infinity }}
            />

            {/* Login Card */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative w-full max-w-sm z-10"
            >
                <div className="bg-white rounded-[2rem] shadow-2xl p-6 md:p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <Link to="/" className="inline-block mb-6 hover:scale-105 transition-transform duration-300">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center mx-auto shadow-xl shadow-red-600/20">
                                <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                </svg>
                            </div>
                        </Link>
                        <h1 className="text-4xl font-bold text-gray-900 mb-3 tracking-tight">Welcome Back</h1>
                        <p className="text-lg text-gray-500">Log in to your assessment dashboard</p>
                    </div>

                    {/* Error Message */}
                    {(error || formError) && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="mb-8 p-4 rounded-2xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium flex items-center gap-3"
                        >
                            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            {error || formError}
                        </motion.div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-8">
                        <Input
                            label="Email Address"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="name@example.com"
                            size="lg"
                            leftIcon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                                </svg>
                            }
                        />

                        <div>
                            <Input
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                size="lg"
                                leftIcon={
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                }
                                rightIcon={
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="hover:text-gray-700 transition-colors focus:outline-none"
                                    >
                                        {showPassword ? (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                            </svg>
                                        ) : (
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                            </svg>
                                        )}
                                    </button>
                                }
                            />
                            <div className="flex items-center justify-between mt-3 px-1">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <div className="relative flex items-center">
                                        <input
                                            type="checkbox"
                                            className="peer h-4 w-4 cursor-pointer appearance-none rounded border border-gray-300 transition-all checked:border-red-600 checked:bg-red-600 hover:border-red-400"
                                        />
                                        <svg className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white opacity-0 peer-checked:opacity-100" width="10" height="10" viewBox="0 0 12 12" fill="none">
                                            <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                    </div>
                                    <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors select-none">Remember me</span>
                                </label>
                                <Link to="/forgot-password" className="text-sm text-red-600 hover:text-red-700 font-medium transition-colors hover:underline">
                                    Forgot password?
                                </Link>
                            </div>
                        </div>

                        <Button type="submit" fullWidth loading={loading} size="lg" className="py-4 text-lg">
                            Sign In
                        </Button>
                    </form>

                    {/* Divider */}
                    <div className="relative my-8">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-200" />
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-6 bg-white text-gray-400 font-medium">or continue with</span>
                        </div>
                    </div>

                    {/* Social Login */}
                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={handleGoogleSignIn}
                            className="flex-1 flex items-center justify-center gap-3 px-6 py-3 border-2 border-gray-100 rounded-xl hover:border-red-100 hover:bg-red-50/50 transition-all duration-300 group"
                        >
                            <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-6 h-6 group-hover:scale-110 transition-transform" />
                            <span className="font-semibold text-gray-700 group-hover:text-red-700">Google</span>
                        </button>
                    </div>

                    {/* Sign Up Link */}
                    <div className="mt-8 text-center">
                        <p className="text-gray-600 text-lg">
                            Don't have an account?{' '}
                            <Link to="/signup" className="text-red-600 hover:text-red-700 font-bold hover:underline underline-offset-4 transition-all">
                                Sign up for free
                            </Link>
                        </p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
