// Supabase client configuration
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

console.log('🔧 Supabase Configuration:', {
    url: supabaseUrl ? `${supabaseUrl.substring(0, 30)}...` : 'NOT SET',
    anonKey: supabaseAnonKey ? `${supabaseAnonKey.substring(0, 20)}...` : 'NOT SET'
});

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('❌ Supabase credentials not found. Please check your .env.frontend file.');
}

export const supabase = createClient(
    supabaseUrl || '',
    supabaseAnonKey || '',
    {
        auth: {
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true,
            // Use default storage key to preserve existing sessions
        },
    }
);

// Debug: Check initial session state
supabase.auth.getSession().then(({ data, error }) => {
    if (error) {
        console.error('❌ Initial session check error:', error.message);
    } else if (data?.session) {
        console.log('✅ Initial session found:', {
            userId: data.session.user?.id?.substring(0, 8) + '...',
            expiresAt: new Date(data.session.expires_at * 1000).toISOString()
        });
    } else {
        console.warn('⚠️ No initial session found - user needs to log in');
    }
});

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
    signInWithOAuth: async ({ provider, options = {} }) => {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider,
            options: {
                ...options,
                queryParams: {
                    prompt: 'select_account',  // Force Google to show account picker
                },
            },
        });
        return { data, error };
    },

    // Sign in with password (method used by AuthContext)
    signInWithPassword: async ({ email, password }) => {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
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
