// API service for backend communication
import axios from 'axios';
import { supabase } from './supabase';
import { authTokenStore } from './authTokenStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000; // 30s default
const AUDIO_UPLOAD_TIMEOUT = parseInt(import.meta.env.VITE_AUDIO_TIMEOUT) || 60000; // 60s for audio processing (STT + AI + TTS)

console.log('📡 API Configuration:', { API_BASE_URL, API_TIMEOUT });

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Export timeout constants for components that need to match
export const API_TIMEOUTS = { default: API_TIMEOUT, audio: AUDIO_UPLOAD_TIMEOUT };

// Request interceptor to add auth token
// Uses authTokenStore for synchronous token retrieval (no race conditions)
api.interceptors.request.use(
    async (config) => {
        const requestId = Date.now().toString(36);
        console.log(`🔄 [${requestId}] Request starting: ${config.method?.toUpperCase()} ${config.url}`);

        // First, try to get token from our store (synchronous, no waiting)
        let token = authTokenStore.getAccessToken();

        // Check if we have a valid token
        if (token && authTokenStore.hasValidToken()) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log(`✅ [${requestId}] Token attached from store`);
        } else {
            // Token missing or expired - try to get fresh session from Supabase
            // This is a fallback for edge cases (e.g., page refresh before AuthContext initializes)
            console.log(`🔄 [${requestId}] No valid token in store, attempting Supabase fallback...`);

            try {
                // Use a short timeout to prevent hanging
                const timeoutPromise = new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Fallback timeout')), 3000)
                );

                const result = await Promise.race([
                    supabase.auth.getSession(),
                    timeoutPromise
                ]);

                const session = result?.data?.session;
                if (session?.access_token) {
                    token = session.access_token;
                    config.headers.Authorization = `Bearer ${token}`;
                    // Also update the store
                    authTokenStore.setSession(session);
                    console.log(`✅ [${requestId}] Token attached from Supabase fallback`);
                } else {
                    console.warn(`⚠️ [${requestId}] No session available - user may need to log in`);
                }
            } catch (err) {
                // Fallback failed - proceed without token
                // Backend will return 401 and user will be prompted to log in
                console.warn(`⚠️ [${requestId}] Fallback failed (${err.message}) - proceeding without auth`);
            }
        }

        console.log(`🚀 [${requestId}] Sending request to ${config.baseURL}${config.url}`);
        return config;
    },
    (error) => {
        console.error('❌ Request interceptor error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => {
        console.log(`✅ Response received: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
        return response;
    },
    async (error) => {
        console.error(`❌ Request failed: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
            status: error.response?.status,
            message: error.message,
            data: error.response?.data
        });
        const originalRequest = error.config;

        // Handle 401 Unauthorized - try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            console.log('🔄 401 received - attempting token refresh...');

            try {
                const { data, error: refreshError } = await supabase.auth.refreshSession();

                if (refreshError) {
                    console.error('❌ Token refresh returned error:', refreshError.message);
                    throw refreshError;
                }

                const newToken = data?.session?.access_token;
                if (newToken) {
                    console.log('✅ Token refreshed successfully, retrying request...');
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return api(originalRequest);
                } else {
                    console.warn('⚠️ Token refresh returned no token - session may be invalid');
                }
            } catch (refreshError) {
                console.error('❌ Token refresh failed:', refreshError);
                // Don't auto-redirect - let the user see the error
                console.warn('⚠️ User session expired - please log in again');
            }
        }

        // Format error message
        const errorMessage = error.response?.data?.detail
            || error.response?.data?.message
            || error.message
            || 'An unexpected error occurred';

        return Promise.reject({
            message: errorMessage,
            status: error.response?.status,
            data: error.response?.data,
        });
    }
);

// API methods
export const apiService = {
    // Health check
    healthCheck: async () => {
        const response = await api.get('/health');
        return response.data;
    },

    // Test config (debug mode only)
    testConfig: async () => {
        const response = await api.get('/api/v1/config/test');
        return response.data;
    },

    // Generic methods
    get: async (url, config = {}) => {
        const response = await api.get(url, config);
        return response.data;
    },

    post: async (url, data = {}, config = {}) => {
        const response = await api.post(url, data, config);
        return response.data;
    },

    put: async (url, data = {}, config = {}) => {
        const response = await api.put(url, data, config);
        return response.data;
    },

    patch: async (url, data = {}, config = {}) => {
        const response = await api.patch(url, data, config);
        return response.data;
    },

    delete: async (url, config = {}) => {
        const response = await api.delete(url, config);
        return response.data;
    },
};

export default api;
