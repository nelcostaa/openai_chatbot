/**
 * Authentication Hooks (TanStack Query)
 * Handles registration, login, logout, and user profile
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import api from '@/lib/api';
import { useAuthStore, User } from '@/stores/authStore';

interface RegisterData {
    email: string;
    password: string;
    display_name: string;
}

interface LoginData {
    email: string;
    password: string;
}

interface AuthResponse {
    access_token: string;
    token_type: string;
}

/**
 * Register new user
 */
export const useRegister = () => {
    const { login } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: async (data: RegisterData) => {
            const response = await api.post<AuthResponse>('/api/auth/register', data);
            return response.data;
        },
        onSuccess: async (data) => {
            try {
                const userResponse = await api.get<User>('/api/auth/me', {
                    headers: { Authorization: `Bearer ${data.access_token}` },
                });

                login(data.access_token, userResponse.data);

                // Create a default project for the new user (API endpoint remains /api/stories/)
                const response = await api.post('/api/stories', {
                    title: 'My First Project',
                    status: 'active',
                });

                navigate(`/project/${response.data.id}`);

            } catch (err) {
                console.error('Error creating project:', err);
                navigate('/onboarding');
            }
        },
    });
};

/**
 * Login existing user
 */
export const useLogin = () => {
    const { login } = useAuthStore();
    const navigate = useNavigate();

    return useMutation({
        mutationFn: async (data: LoginData) => {
            const response = await api.post<AuthResponse>('/api/auth/login', data);
            return response.data;
        },
        onSuccess: async (data) => {
            // Fetch user profile after login
            const userResponse = await api.get<User>('/api/auth/me', {
                headers: { Authorization: `Bearer ${data.access_token}` },
            });
            login(data.access_token, userResponse.data);
            navigate('/dashboard');
        },
    });
};

/**
 * Get current authenticated user
 */
export const useCurrentUser = () => {
    const { token, setUser } = useAuthStore();

    const query = useQuery({
        queryKey: ['auth', 'me'],
        queryFn: async () => {
            const response = await api.get<User>('/api/auth/me');
            return response.data;
        },
        enabled: !!token,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });

    // Update store when data changes (use useEffect to avoid infinite loop)
    useEffect(() => {
        if (query.data) {
            setUser(query.data);
        }
    }, [query.data, setUser]);

    return query;
};

/**
 * Logout user
 */
export const useLogout = () => {
    const { logout } = useAuthStore();
    const queryClient = useQueryClient();
    const navigate = useNavigate();

    return () => {
        logout();
        queryClient.clear();
        navigate('/login');
    };
};
