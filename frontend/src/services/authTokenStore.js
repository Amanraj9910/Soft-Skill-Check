/**
 * Auth Token Store - Singleton for sharing auth token between AuthContext and API service
 * 
 * This solves the race condition where api.js calls supabase.auth.getSession() 
 * while Supabase is in the middle of _recoverAndRefresh, causing a deadlock.
 * 
 * AuthContext updates this store when session changes.
 * api.js reads from this store synchronously (no await needed).
 */

let currentAccessToken = null;
let currentSession = null;
let tokenUpdateCallbacks = [];

export const authTokenStore = {
    /**
     * Set the current session and access token.
     * Called by AuthContext when session changes.
     */
    setSession(session) {
        currentSession = session;
        currentAccessToken = session?.access_token || null;

        // Notify any listeners
        tokenUpdateCallbacks.forEach(cb => {
            try {
                cb(currentAccessToken, session);
            } catch (e) {
                console.error('[AuthTokenStore] Callback error:', e);
            }
        });

        if (session) {
            console.log('[AuthTokenStore] Token updated, expires:',
                new Date(session.expires_at * 1000).toISOString());
        } else {
            console.log('[AuthTokenStore] Token cleared');
        }
    },

    /**
     * Get the current access token synchronously.
     * Returns null if not authenticated.
     */
    getAccessToken() {
        return currentAccessToken;
    },

    /**
     * Get the full session object synchronously.
     */
    getSession() {
        return currentSession;
    },

    /**
     * Check if we have a valid (non-expired) token.
     * Checks with a 60-second buffer.
     */
    hasValidToken() {
        if (!currentSession?.access_token || !currentSession?.expires_at) {
            return false;
        }
        const expiryTime = currentSession.expires_at * 1000;
        const buffer = 60 * 1000; // 60 seconds
        return Date.now() < (expiryTime - buffer);
    },

    /**
     * Subscribe to token updates.
     * Returns unsubscribe function.
     */
    onTokenUpdate(callback) {
        tokenUpdateCallbacks.push(callback);
        return () => {
            tokenUpdateCallbacks = tokenUpdateCallbacks.filter(cb => cb !== callback);
        };
    },

    /**
     * Clear the store (e.g., on sign out).
     */
    clear() {
        currentAccessToken = null;
        currentSession = null;
        tokenUpdateCallbacks.forEach(cb => {
            try {
                cb(null, null);
            } catch (e) {
                console.error('[AuthTokenStore] Callback error:', e);
            }
        });
    }
};

export default authTokenStore;
