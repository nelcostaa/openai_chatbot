import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Project {
    id: number;
    title: string;
    description: string;
    created_at: string;
    updated_at: string;
    user_id: number;
}

// Snippet types for game card generation
export interface Snippet {
    title: string;
    content: string;
    phase: string;
    theme: string;
}

export interface SnippetsResponse {
    success: boolean;
    snippets: Snippet[];
    count: number;
    model: string | null;
    error?: string;
}

interface CreateProjectDto {
    title: string;
    description?: string;
}

interface UpdateProjectDto {
    title?: string;
    description?: string;
}

// Fetch all projects for current user
export const useProjects = () => {
    return useQuery({
        queryKey: ['projects'],
        queryFn: async () => {
            // API endpoint remains /api/stories/ (backend unchanged)
            const response = await api.get<Project[]>('/api/stories/');
            return response.data;
        },
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
};

// Fetch single project by ID
export const useProject = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['projects', projectId],
        queryFn: async () => {
            // API endpoint remains /api/stories/{id} (backend unchanged)
            const response = await api.get<Project>(`/api/stories/${projectId}`);
            return response.data;
        },
        enabled: !!projectId,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};

// Create new project
export const useCreateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: CreateProjectDto) => {
            // API endpoint remains /api/stories/ (backend unchanged)
            const response = await api.post<Project>('/api/stories/', data);
            return response.data;
        },
        onSuccess: () => {
            // Invalidate projects list to refetch
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });
};

// Update existing project
export const useUpdateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: UpdateProjectDto }) => {
            // API endpoint remains /api/stories/{id} (backend unchanged)
            const response = await api.put<Project>(`/api/stories/${id}`, data);
            return response.data;
        },
        onSuccess: (updatedProject) => {
            // Invalidate both list and individual project queries
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            queryClient.invalidateQueries({ queryKey: ['projects', updatedProject.id] });
        },
    });
};

// Delete project
export const useDeleteProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: number) => {
            // API endpoint remains /api/stories/{id} (backend unchanged)
            await api.delete(`/api/stories/${id}`);
            return id;
        },
        onSuccess: () => {
            // Invalidate projects list to refetch
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });
};

/**
 * Generate project snippets (game cards) for a project.
 * 
 * This is a mutation because:
 * 1. It triggers AI processing (expensive operation)
 * 2. We want explicit user control over when to generate
 * 3. Results can be cached per project_id for future requests
 * 
 * Usage:
 *   const { mutate: generateSnippets, data, isPending } = useProjectSnippets();
 *   generateSnippets(projectId);
 */
export const useProjectSnippets = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (projectId: number): Promise<SnippetsResponse> => {
            // POST to /api/snippets/{story_id} - story_id is in the URL path (backend unchanged)
            const response = await api.post<SnippetsResponse>(`/api/snippets/${projectId}`);
            return response.data;
        },
        onSuccess: (data, projectId) => {
            // Cache the snippets for this project so we don't regenerate unnecessarily
            queryClient.setQueryData(['snippets', projectId], data);
        },
    });
};

/**
 * Get cached snippets for a project (if previously generated).
 * 
 * This is useful if you want to check if snippets exist before
 * showing a "regenerate" vs "generate" button.
 */
export const useCachedSnippets = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['snippets', projectId],
        queryFn: () => null, // We never fetch - only use cache
        enabled: false, // Disable automatic fetching
        staleTime: Infinity, // Never consider cached data stale
    });
};

// Legacy exports for backward compatibility during migration
// TODO: Remove these after all consumers are updated
export {
    Project as Story,
    useProjects as useStories,
    useProject as useStory,
    useCreateProject as useCreateStory,
    useUpdateProject as useUpdateStory,
    useDeleteProject as useDeleteStory,
    useProjectSnippets as useStorySnippets,
};
