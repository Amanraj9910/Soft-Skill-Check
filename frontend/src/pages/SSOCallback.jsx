// SSO Callback Handler - Accepts tokens from external apps for seamless login
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../services/supabase';

const SSOCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [error, setError] = useState(null);
    const [status, setStatus] = useState('Authenticating...');

    useEffect(() => {
        const handleSSO = async () => {
            const accessToken = searchParams.get('access_token');
            const refreshToken = searchParams.get('refresh_token');
            const type = searchParams.get('type');
            const redirectTo = searchParams.get('redirect') || '/dashboard';

            console.log('🔐 [SSO] Processing SSO callback...');

            // Validate SSO request
            if (type !== 'sso' || !accessToken || !refreshToken) {
                console.error('❌ [SSO] Invalid SSO request - missing parameters');
                setError('Invalid SSO request. Redirecting to login...');
                setTimeout(() => navigate('/login'), 2000);
                return;
            }

            try {
                setStatus('Validating session...');

                // Set the session from tokens passed by the other app
                const { data, error: sessionError } = await supabase.auth.setSession({
                    access_token: accessToken,
                    refresh_token: refreshToken,
                });

                if (sessionError) {
                    throw sessionError;
                }

                if (!data.session) {
                    throw new Error('Failed to establish session');
                }

                console.log('✅ [SSO] Session established for:', data.session.user?.email);
                setStatus('Success! Redirecting...');

                // Clear tokens from URL for security (prevent token leakage in browser history)
                window.history.replaceState({}, document.title, '/sso-callback');

                // Small delay to show success message, then redirect
                setTimeout(() => {
                    navigate(redirectTo, { replace: true });
                }, 500);

            } catch (err) {
                console.error('❌ [SSO] Authentication error:', err);
                setError(err.message || 'Authentication failed. Please login manually.');
                setTimeout(() => navigate('/login'), 3000);
            }
        };

        handleSSO();
    }, [searchParams, navigate]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <div className="text-center p-8 bg-white rounded-xl shadow-lg max-w-md w-full mx-4">
                {error ? (
                    <>
                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
                            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-semibold text-slate-900 mb-2">Authentication Error</h2>
                        <p className="text-red-600">{error}</p>
                        <p className="text-sm text-slate-500 mt-2">Redirecting to login...</p>
                    </>
                ) : (
                    <>
                        <div className="w-16 h-16 mx-auto mb-4">
                            <div className="animate-spin rounded-full h-16 w-16 border-4 border-slate-200 border-t-red-600"></div>
                        </div>
                        <h2 className="text-xl font-semibold text-slate-900 mb-2">Single Sign-On</h2>
                        <p className="text-slate-600">{status}</p>
                    </>
                )}
            </div>
        </div>
    );
};

export default SSOCallback;
