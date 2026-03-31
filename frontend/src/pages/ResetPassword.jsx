// Reset Password Page - Complete New Password
import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

const ResetPassword = () => {
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState(false);

    const { updateProfile, loading, error, clearError } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError('');
        clearError();

        if (!password || !confirmPassword) {
            setFormError('Please fill in all fields');
            return;
        }

        if (password.length < 6) {
            setFormError('Password must be at least 6 characters');
            return;
        }

        if (password !== confirmPassword) {
            setFormError('Passwords do not match');
            return;
        }

        // AuthContext.updateProfile uses supabase.auth.updateUser() under the hood
        // which handles committing the password update based on the token in the URL automatically parsed on load.
        const { error: updateErr } = await updateProfile({ password });

        if (updateErr) {
            setFormError(updateErr.message);
        } else {
            setSuccess(true);
            setTimeout(() => {
                navigate('/dashboard');
            }, 3000);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-gray-900">
            <div className="absolute inset-0 opacity-10" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                backgroundSize: '40px 40px'
            }} />

            <motion.div
                className="hidden md:block absolute -top-20 -right-20 w-[300px] h-[300px] lg:w-[400px] lg:h-[400px] bg-red-600/20 rounded-full blur-[100px]"
                animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.3, 0.2] }}
                transition={{ duration: 12, repeat: Infinity }}
            />
            <motion.div
                className="hidden md:block absolute bottom-0 -left-20 w-[400px] h-[400px] lg:w-[600px] lg:h-[600px] bg-red-900/15 rounded-full blur-[120px]"
                animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.2, 0.1] }}
                transition={{ duration: 15, repeat: Infinity }}
            />

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative w-full max-w-lg z-10"
            >
                <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8">
                    <div className="text-center mb-6 sm:mb-8">
                        <Link to="/" className="inline-block mb-4 sm:mb-6 hover:scale-105 transition-transform duration-300">
                            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center mx-auto shadow-xl shadow-red-600/20">
                                <img src="/img/favicon.ico.png" alt="" />
                            </div>
                        </Link>
                        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2 sm:mb-3 tracking-tight">Create New Password</h1>
                        <p className="text-base sm:text-lg text-gray-500">Secure your account with a strong password.</p>
                    </div>

                    {(error || formError) && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            className="mb-8 p-4 rounded-2xl bg-red-50 border border-red-100 text-red-600 text-sm font-medium flex items-center gap-3 relative"
                        >
                            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            {error || formError}
                        </motion.div>
                    )}

                    {success ? (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center py-6"
                        >
                            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold text-gray-900 mb-2">Password Updated!</h3>
                            <p className="text-gray-600 mb-6">
                                Your new password has been saved. We are redirecting you to your dashboard...
                            </p>
                        </motion.div>
                    ) : (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <Input
                                label="New Password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min 6 characters"
                                size="lg"
                            />
                            
                            <Input
                                label="Confirm New Password"
                                type={showPassword ? 'text' : 'password'}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Repeat new password"
                                size="lg"
                            />
                            
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
                                    <span className="text-gray-600 group-hover:text-gray-900 transition-colors select-none">Show passwords</span>
                                </label>
                            </div>

                            <Button type="submit" fullWidth loading={loading} size="lg" className="mt-6 text-lg py-4">
                                Update Password
                            </Button>
                        </form>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default ResetPassword;
