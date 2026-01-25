// API service for backend communication
import axios from 'axios';
import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000; // 30s for AI/assessment ops

console.log('📡 API Configuration:', { API_BASE_URL, API_TIMEOUT });

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Helper function to check if token is expired (with 60s buffer)
function isTokenExpired(expiresAt) {
    if (!expiresAt) return true;
    const expiryTime = expiresAt * 1000; // Convert to milliseconds
    const now = Date.now();
    const buffer = 60 * 1000; // 60 seconds buffer
    return now >= (expiryTime - buffer);
}

// Request interceptor to add auth token
api.interceptors.request.use(
    async (config) => {
        const requestId = Date.now().toString(36);
        console.log(`🔄 [${requestId}] Request starting: ${config.method?.toUpperCase()} ${config.url}`);

        try {
            console.log(`🔑 [${requestId}] Getting auth session...`);
            const startTime = Date.now();

            // First try to get current session
            let { data } = await supabase.auth.getSession();
            let session = data?.session;

            // If no session or token is expired, try to refresh
            if (!session || isTokenExpired(session.expires_at)) {
                console.log(`🔄 [${requestId}] Session expired or missing, refreshing...`);
                const refreshResult = await supabase.auth.refreshSession();
                if (refreshResult.data?.session) {
                    session = refreshResult.data.session;
                    console.log(`✅ [${requestId}] Session refreshed successfully`);
                } else if (refreshResult.error) {
                    console.error(`❌ [${requestId}] Session refresh failed:`, refreshResult.error.message);
                }
            }

            const duration = Date.now() - startTime;
            console.log(`🔑 [${requestId}] Session check completed in ${duration}ms`);

            const token = session?.access_token;
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
                const expiresAt = session.expires_at ? new Date(session.expires_at * 1000).toISOString() : 'unknown';
                console.log(`✅ [${requestId}] Auth token attached (expires: ${expiresAt})`);
            } else {
                console.warn(`⚠️ [${requestId}] No auth token available - user may need to log in again`);
            }
        } catch (error) {
            console.error(`❌ [${requestId}] Error getting auth token:`, error.message);
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
