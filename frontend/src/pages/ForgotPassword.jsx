// Forgot Password Page - Request Email
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [formError, setFormError] = useState('');
    const [success, setSuccess] = useState(false);

    const { resetPassword, loading, error, clearError } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log('Sending reset password link for email:', email);
        setFormError('');
        clearError();

        if (!email) {
            setFormError('Please enter your email address');
            return;
        }

        console.log('Calling resetPassword context method...');
        const { error: resetErr } = await resetPassword(email);
        console.log('resetPassword result error:', resetErr);

        if (resetErr) {
            setFormError(resetErr.message);
        } else {
            console.log('Successfully requested reset link, setting success to true');
            setSuccess(true);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-gray-900">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                backgroundSize: '40px 40px'
            }} />

            {/* Accent Orbs */}
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

            {/* Form Card */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative w-full max-w-lg z-10"
            >
                <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8">
                    {/* Header */}
                    <div className="text-center mb-6 sm:mb-8">
                        <Link to="/" className="inline-block mb-4 sm:mb-6 hover:scale-105 transition-transform duration-300">
                            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center mx-auto shadow-xl shadow-red-600/20">
                                <img src="/img/favicon.ico.png" alt="" />
                            </div>
                        </Link>
                        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2 sm:mb-3 tracking-tight">Reset Password</h1>
                        <p className="text-base sm:text-lg text-gray-500">Enter your email to receive a secure link.</p>
                    </div>

                    {/* Error Message */}
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

                    <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6">
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

                        <Button type="submit" fullWidth loading={loading} size="lg" className="py-3 sm:py-4 text-base sm:text-lg">
                            Send Reset Link
                        </Button>
                    </form>

                    {/* Footer Nav */}
                    <div className="mt-8 text-center border-t border-gray-100 pt-6">
                        <p className="text-gray-600 text-lg flex items-center justify-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                            <Link to="/login" className="text-red-600 hover:text-red-700 font-bold hover:underline underline-offset-4 transition-all">
                                Return to login
                            </Link>
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Success Modal */}
            {success && !error && !formError && (
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
                        <h3 className="text-2xl font-bold text-gray-900 mb-2">Check Your Inbox</h3>
                        <p className="text-gray-600 mb-8">
                            We've sent password reset instructions to <span className="font-semibold text-gray-900">{email}</span>.
                            <br /><br />
                            Please check your spam folder if you don't see it within a few minutes.
                        </p>
                        <Link to="/login">
                            <Button fullWidth size="lg" className="bg-red-600 hover:bg-red-700 text-white">
                                OK, Return to Login
                            </Button>
                        </Link>
                    </motion.div>
                </div>
            )}
        </div>
    );
};

export default ForgotPassword;
