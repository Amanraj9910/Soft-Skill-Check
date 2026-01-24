// Authentication context for managing auth state
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { auth } from '../services/supabase';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Initialize auth state
    useEffect(() => {
        let mounted = true;

        const initializeAuth = async () => {
            try {
                const { session: currentSession } = await auth.getSession();
                if (mounted) {
                    setSession(currentSession);
                    setUser(currentSession?.user || null);
                    setLoading(false);
                }
            } catch (err) {
                console.error('Auth initialization error:', err);
                if (mounted) {
                    setError(err.message);
                    setLoading(false);
                }
            }
        };

        initializeAuth();

        // Subscribe to auth changes
        const { data: { subscription } } = auth.onAuthStateChange((event, newSession) => {
            if (mounted) {
                setSession(newSession);
                setUser(newSession?.user || null);
                setLoading(false);

                if (event === 'SIGNED_OUT') {
                    setUser(null);
                    setSession(null);
                }
            }
        });

        return () => {
            mounted = false;
            subscription?.unsubscribe();
        };
    }, []);

    // Sign up
    const signUp = useCallback(async (email, password, metadata = {}) => {
        setLoading(true);
        setError(null);
        try {
            const { data, error: signUpError } = await auth.signUp(email, password, metadata);
            if (signUpError) throw signUpError;
            return { data, error: null };
        } catch (err) {
            setError(err.message);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    }, []);

    // Sign in
    const signIn = useCallback(async (email, password) => {
        setLoading(true);
        setError(null);
        try {
            const { data, error: signInError } = await auth.signInWithPassword({
                email,
                password,
            });
            if (signInError) throw signInError;
            return { data, error: null };
        } catch (err) {
            setError(err.message);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    }, []);

    // Sign in with Google
    const signInWithGoogle = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const { data, error: signInError } = await auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/dashboard`,
                },
            });
            if (signInError) throw signInError;
            return { data, error: null };
        } catch (err) {
            setError(err.message);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    }, []);

    // Sign out
    const signOut = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const { error: signOutError } = await auth.signOut();
            if (signOutError) throw signOutError;
            setUser(null);
            setSession(null);
            return { error: null };
        } catch (err) {
            setError(err.message);
            return { error: err };
        } finally {
            setLoading(false);
        }
    }, []);

    // Reset password
    const resetPassword = useCallback(async (email) => {
        setLoading(true);
        setError(null);
        try {
            const { data, error: resetError } = await auth.resetPassword(email);
            if (resetError) throw resetError;
            return { data, error: null };
        } catch (err) {
            setError(err.message);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    }, []);

    // Update user profile
    const updateProfile = useCallback(async (updates) => {
        setLoading(true);
        setError(null);
        try {
            const { data, error: updateError } = await auth.updateUser(updates);
            if (updateError) throw updateError;
            setUser(data?.user || user);
            return { data, error: null };
        } catch (err) {
            setError(err.message);
            return { data: null, error: err };
        } finally {
            setLoading(false);
        }
    }, [user]);

    const value = {
        user,
        session,
        loading,
        error,
        isAuthenticated: !!session,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        resetPassword,
        updateProfile,
        clearError: () => setError(null),
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext;
