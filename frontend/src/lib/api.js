/**
 * API Configuration
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API Client for backend communication
 */
class ApiClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    /**
     * Generic request handler
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

/**
 * API Service Methods
 */
const api = new ApiClient();

export const apiService = {
    /**
     * Health Check
     */
    health: {
        check: () => api.get('/health'),
    },

    /**
     * Messages API
     */
    messages: {
        list: (skip = 0, limit = 100) => api.get('/api/messages/', { skip, limit }),
        create: (role, content) => api.post('/api/messages/', { role, content }),
    },

    /**
     * Stories API (Not yet implemented in backend)
     */
    stories: {
        list: () => {
            console.warn('Stories API not yet implemented in backend');
            return Promise.resolve([]);
        },
        get: (id) => {
            console.warn('Stories API not yet implemented in backend');
            return Promise.resolve(null);
        },
        create: (data) => {
            console.warn('Stories API not yet implemented in backend');
            return Promise.resolve(null);
        },
    },

    /**
     * Auth API (Not yet implemented in backend)
     */
    auth: {
        login: (email, password) => {
            console.warn('Auth API not yet implemented in backend');
            return Promise.resolve({ token: 'mock-token', user: { email } });
        },
        register: (email, password) => {
            console.warn('Auth API not yet implemented in backend');
            return Promise.resolve({ token: 'mock-token', user: { email } });
        },
        logout: () => {
            console.warn('Auth API not yet implemented in backend');
            return Promise.resolve();
        },
    },
};

export default apiService;
