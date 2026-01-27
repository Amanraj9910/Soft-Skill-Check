// Signup Page - Interview Assessment Theme
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

const Signup = () => {
    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        password: '',
        confirmPassword: '',
    });
    const [showPassword, setShowPassword] = useState(false);
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState(false);

    const { signUp, signInWithGoogle, loading, error, clearError } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const validateForm = () => {
        if (!formData.fullName || !formData.email || !formData.password || !formData.confirmPassword) {
            setFormError('Please fill in all fields');
            return false;
        }
        if (formData.password.length < 6) {
            setFormError('Password must be at least 6 characters');
            return false;
        }
        if (formData.password !== formData.confirmPassword) {
            setFormError('Passwords do not match');
            return false;
        }
        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError('');
        clearError();
        if (!validateForm()) return;

        // Update: wrapper expects metadata as 3rd arg, but we need to pass options for emailRedirectTo.
        // We need to bypass wrapper or update wrapper. Let's update wrapper first or pass it correctly.
        // Actually, the wrapper puts the 3rd arg into 'options.data'. This is wrong for emailRedirectTo.
        // I will fix the wrapper in the previous step or here usage?
        // Let's fix the usage to bypass if needed, OR update the wrapper to accept options.
        // Decision: I already updated wrapper to put 3rd arg into `options.data`. This breaks `emailRedirectTo`.
        // I will fix `frontend/src/services/supabase.js` to handle options better in the next step.
        // For now, let's just make the UI smaller.
        // Wait, I strictly must fix the functionality.
        // Re-reading `supabase.js`:
        // signUp: async (email, password, metadata = {}) => { ... options: { data: metadata } }
        // This effectively hides `emailRedirectTo`. I must fix `supabase.js` signUp method too.

        const { error } = await signUp(
            formData.email,
            formData.password,
            { full_name: formData.fullName },
            { emailRedirectTo: `${window.location.origin}/login` }
        );
        if (error) {
            if (error.message.includes('rate limit')) {
                setFormError('Too many signup attempts. Please wait a few minutes or check if you already received an email.');
            } else {
                setFormError(error.message);
            }
        } else {
            setSuccess(true);
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

    // Success Modal Logic handled in render below via AnimatePresence
    // removing early return to allow modal overlay


    return (
        <div className="min-h-screen flex items-center justify-center py-20 px-4 relative overflow-hidden bg-gray-900">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                backgroundSize: '40px 40px'
            }} />

            {/* Accent Orbs */}
            <motion.div
                className="absolute top-20 right-20 w-96 h-96 bg-red-600/20 rounded-full blur-[100px]"
                animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.3, 0.2] }}
                transition={{ duration: 10, repeat: Infinity }}
            />
            <motion.div
                className="absolute bottom-20 left-20 w-[500px] h-[500px] bg-red-900/20 rounded-full blur-[120px]"
                animate={{ scale: [1, 1.1, 1], opacity: [0.2, 0.3, 0.2] }}
                transition={{ duration: 15, repeat: Infinity }}
            />

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative w-full max-w-2xl z-10"
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
                        <h1 className="text-4xl font-bold text-gray-900 mb-3 tracking-tight">Create Account</h1>
                        <p className="text-lg text-gray-500">Join thousands of others improving their English</p>
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

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <Input
                            label="Full Name"
                            name="fullName"
                            value={formData.fullName}
                            onChange={handleChange}
                            placeholder="e.g., John Doe"
                            size="lg"
                        />
                        <Input
                            label="Email Address"
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="name@example.com"
                            size="lg"
                        />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <Input
                                label="Password"
                                type={showPassword ? 'text' : 'password'}
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="Min 6 chars"
                                size="lg"
                            />
                            <Input
                                label="Confirm"
                                type={showPassword ? 'text' : 'password'}
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                placeholder="Repeat password"
                                size="lg"
                            />
                        </div>

                        <div className="pt-2">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <div className="relative flex items-center">
                                    <input
                                        type="checkbox"
                                        onChange={() => setShowPassword(!showPassword)}
                                        className="peer h-5 w-5 cursor-pointer appearance-none rounded-md border-2 border-gray-300 transition-all checked:border-red-600 checked:bg-red-600 hover:border-red-400"
                                    />
                                    <svg className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white opacity-0 peer-checked:opacity-100" width="12" height="12" viewBox="0 0 12 12" fill="none">
                                        <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                <span className="text-gray-600 group-hover:text-gray-900 transition-colors select-none">Show password</span>
                            </label>
                        </div>

                        <Button type="submit" fullWidth loading={loading} size="lg" className="mt-6 text-lg py-4">
                            Create Free Account
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

                    <div className="mt-8 text-center">
                        <p className="text-gray-600 text-lg">
                            Already have an account?{' '}
                            <Link to="/login" className="text-red-600 hover:text-red-700 font-bold hover:underline underline-offset-4 transition-all">
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Success Modal */}
            {success && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm"
                    />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        className="relative bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center z-10"
                    >
                        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">Registration Successful!</h3>
                        <p className="text-gray-600 mb-8">
                            We've sent a confirmation email to <span className="font-semibold text-gray-900">{formData.email}</span>.
                            <br /><br />
                            Please verify your email address to activate your account, then log in.
                        </p>
                        <Button
                            onClick={() => navigate('/login')}
                            fullWidth
                            size="lg"
                            className="bg-red-600 hover:bg-red-700 text-white"
                        >
                            OK, Login Now
                        </Button>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default Signup;
