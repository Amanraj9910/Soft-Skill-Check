// Supabase client configuration
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn('Supabase credentials not found. Please check your .env.frontend file.');
}

export const supabase = createClient(
    supabaseUrl || '',
    supabaseAnonKey || '',
    {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true,
        },
    }
);

// Auth helper functions
export const auth = {
    // Sign up with email and password
    signUp: async (email, password, metadata = {}, authOptions = {}) => {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata,
                ...authOptions,
            },
        });
        return { data, error };
    },

    // Sign in with email and password
    signIn: async (email, password) => {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        return { data, error };
    },

    // Sign in with OAuth (Google, etc.)
    signInWithOAuth: async (provider) => {
        const { data, error } = await supabase.auth.signInWithOAuth(provider);
        return { data, error };
    },

    // Sign out
    signOut: async () => {
        const { error } = await supabase.auth.signOut();
        return { error };
    },

    // Get current session
    getSession: async () => {
        const { data, error } = await supabase.auth.getSession();
        return { session: data?.session, error };
    },

    // Get current user
    getUser: async () => {
        const { data, error } = await supabase.auth.getUser();
        return { user: data?.user, error };
    },

    // Reset password
    resetPassword: async (email) => {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`,
        });
        return { data, error };
    },

    // Update user
    updateUser: async (updates) => {
        const { data, error } = await supabase.auth.updateUser(updates);
        return { data, error };
    },

    // Subscribe to auth state changes
    onAuthStateChange: (callback) => {
        return supabase.auth.onAuthStateChange(callback);
    },
};

export default supabase;
