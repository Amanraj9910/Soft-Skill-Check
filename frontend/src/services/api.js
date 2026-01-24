// API service for backend communication
import axios from 'axios';
import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000;

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
api.interceptors.request.use(
    async (config) => {
        try {
            const { data } = await supabase.auth.getSession();
            const token = data?.session?.access_token;

            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        } catch (error) {
            console.error('Error getting auth token:', error);
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const { data, error: refreshError } = await supabase.auth.refreshSession();

                if (refreshError) {
                    throw refreshError;
                }

                const newToken = data?.session?.access_token;
                if (newToken) {
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                // Redirect to login or handle logout
                window.location.href = '/login';
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
