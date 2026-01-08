import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { ChapterNames } from './useChat';

export interface Project {
    id: number;
    title: string;
    user_id: number;
    route_type: string;
    current_phase: string;
    age_range: string | null;
    status: string;
    chapter_names: ChapterNames | null;
    created_at?: string;
}

// Snippet types for game card generation
export interface Snippet {
    id?: number;
    title: string;
    content: string;
    phase: string;
    theme: string;
    is_locked?: boolean;
    is_active?: boolean;
    display_order: number;
    created_at?: string;
}

export interface SnippetsResponse {
    success: boolean;
    snippets: Snippet[];
    count: number;
    cached?: boolean;  // True if from database, false if freshly generated
    locked_count?: number;  // Number of locked snippets
    model?: string | null;
    error?: string;
}

export interface ArchivedSnippetsResponse {
    success: boolean;
    snippets: Snippet[];
    count: number;
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
 * Generate/regenerate project snippets (game cards) for a project.
 * 
 * This is a mutation because:
 * 1. It triggers AI processing (expensive operation)
 * 2. We want explicit user control over when to generate
 * 3. Clears existing snippets and creates new ones
 * 
 * Usage:
 *   const { mutate: generateSnippets, data, isPending } = useProjectSnippets();
 *   generateSnippets(projectId);
 */
export const useProjectSnippets = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (projectId: number): Promise<SnippetsResponse> => {
            // POST to /api/snippets/{story_id} - regenerates snippets
            const response = await api.post<SnippetsResponse>(`/api/snippets/${projectId}`);
            return response.data;
        },
        onSuccess: (data, projectId) => {
            // Invalidate and refetch snippets query to get fresh data
            queryClient.invalidateQueries({ queryKey: ['snippets', projectId] });
        },
    });
};

/**
 * Fetch existing snippets for a project from the database.
 * 
 * This queries the GET endpoint to retrieve persisted snippets.
 * Use this to display snippets without triggering regeneration.
 * 
 * Usage:
 *   const { data, isLoading, refetch } = useSnippets(projectId);
 */
export const useSnippets = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['snippets', projectId],
        queryFn: async (): Promise<SnippetsResponse> => {
            if (!projectId) {
                return { success: true, snippets: [], count: 0, cached: false };
            }
            const response = await api.get<SnippetsResponse>(`/api/snippets/${projectId}`);
            return response.data;
        },
        enabled: !!projectId,
        staleTime: 5 * 60 * 1000, // 5 minutes - snippets don't change often
    });
};

/**
 * Update an individual snippet's title, content, theme, or phase.
 * 
 * Uses optimistic updates for instant UI feedback, with rollback on error.
 * 
 * Usage:
 *   const updateSnippet = useUpdateSnippet();
 *   updateSnippet.mutate({ 
 *     snippetId: 123, 
 *     projectId: 456,
 *     data: { title: "New Title", content: "New content" } 
 *   });
 */
export interface UpdateSnippetDto {
    title?: string;
    content?: string;
    theme?: string;
    phase?: string;
}

export const useUpdateSnippet = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            snippetId,
            data
        }: {
            snippetId: number;
            projectId: number;
            data: UpdateSnippetDto
        }): Promise<Snippet> => {
            const response = await api.put<Snippet>(`/api/snippets/${snippetId}`, data);
            return response.data;
        },
        onMutate: async ({ snippetId, projectId, data }) => {
            // Cancel any outgoing refetches
            await queryClient.cancelQueries({ queryKey: ['snippets', projectId] });

            // Snapshot the previous value
            const previousSnippets = queryClient.getQueryData<SnippetsResponse>(['snippets', projectId]);

            // Optimistically update to the new value
            if (previousSnippets) {
                queryClient.setQueryData<SnippetsResponse>(['snippets', projectId], {
                    ...previousSnippets,
                    snippets: previousSnippets.snippets.map(s =>
                        s.id === snippetId ? { ...s, ...data } : s
                    ),
                });
            }

            // Return context with the snapshotted value
            return { previousSnippets, projectId };
        },
        onError: (err, variables, context) => {
            // Rollback to the previous value on error
            if (context?.previousSnippets) {
                queryClient.setQueryData(['snippets', context.projectId], context.previousSnippets);
            }
        },
        onSettled: (data, error, variables) => {
            // Always refetch after error or success
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId] });
        },
    });
};

/**
 * Get cached snippets for a project (if previously generated).
 * 
 * @deprecated Use useSnippets instead which fetches from the database.
 * This is kept for backward compatibility during migration.
 */
export const useCachedSnippets = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['snippets', projectId],
        queryFn: () => null, // We never fetch - only use cache
        enabled: false, // Disable automatic fetching
        staleTime: Infinity, // Never consider cached data stale
    });
};

/**
 * Toggle lock status of a snippet.
 * 
 * Locked snippets are protected during regeneration.
 */
export const useLockSnippet = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            snippetId,
            projectId
        }: {
            snippetId: number;
            projectId: number;
        }): Promise<Snippet> => {
            const response = await api.patch<Snippet>(`/api/snippets/${snippetId}/lock`);
            return response.data;
        },
        onMutate: async ({ snippetId, projectId }) => {
            // Cancel any outgoing refetches
            await queryClient.cancelQueries({ queryKey: ['snippets', projectId] });

            // Snapshot the previous value
            const previousSnippets = queryClient.getQueryData<SnippetsResponse>(['snippets', projectId]);

            // Optimistically toggle the lock
            if (previousSnippets) {
                queryClient.setQueryData<SnippetsResponse>(['snippets', projectId], {
                    ...previousSnippets,
                    snippets: previousSnippets.snippets.map(s =>
                        s.id === snippetId ? { ...s, is_locked: !s.is_locked } : s
                    ),
                });
            }

            return { previousSnippets, projectId };
        },
        onError: (err, variables, context) => {
            if (context?.previousSnippets) {
                queryClient.setQueryData(['snippets', context.projectId], context.previousSnippets);
            }
        },
        onSettled: (data, error, variables) => {
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId] });
        },
    });
};

/**
 * Fetch archived (soft-deleted) snippets for a project.
 */
export const useArchivedSnippets = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['snippets', projectId, 'archived'],
        queryFn: async (): Promise<ArchivedSnippetsResponse> => {
            if (!projectId) {
                return { success: true, snippets: [], count: 0 };
            }
            const response = await api.get<ArchivedSnippetsResponse>(`/api/snippets/${projectId}/archived`);
            return response.data;
        },
        enabled: !!projectId,
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
};

/**
 * Restore an archived snippet.
 */
export const useRestoreSnippet = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            snippetId,
            projectId
        }: {
            snippetId: number;
            projectId: number;
        }): Promise<Snippet> => {
            const response = await api.post<Snippet>(`/api/snippets/${snippetId}/restore`);
            return response.data;
        },
        onSuccess: (data, variables) => {
            // Invalidate both active and archived snippets queries
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId] });
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId, 'archived'] });
        },
    });
};

/**
 * Delete a snippet (soft-delete by default).
 * 
 * Pass permanent: true to permanently delete.
 */
export const useDeleteSnippet = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({
            snippetId,
            projectId,
            permanent = false
        }: {
            snippetId: number;
            projectId: number;
            permanent?: boolean;
        }): Promise<Snippet> => {
            const url = permanent
                ? `/api/snippets/${snippetId}?permanent=true`
                : `/api/snippets/${snippetId}`;
            const response = await api.delete<Snippet>(url);
            return response.data;
        },
        onMutate: async ({ snippetId, projectId }) => {
            // Cancel any outgoing refetches
            await queryClient.cancelQueries({ queryKey: ['snippets', projectId] });

            // Snapshot the previous value
            const previousSnippets = queryClient.getQueryData<SnippetsResponse>(['snippets', projectId]);

            // Optimistically remove the snippet from active list
            if (previousSnippets) {
                queryClient.setQueryData<SnippetsResponse>(['snippets', projectId], {
                    ...previousSnippets,
                    snippets: previousSnippets.snippets.filter(s => s.id !== snippetId),
                    count: previousSnippets.count - 1,
                });
            }

            return { previousSnippets, projectId };
        },
        onError: (err, variables, context) => {
            if (context?.previousSnippets) {
                queryClient.setQueryData(['snippets', context.projectId], context.previousSnippets);
            }
        },
        onSettled: (data, error, variables) => {
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId] });
            queryClient.invalidateQueries({ queryKey: ['snippets', variables.projectId, 'archived'] });
        },
    });
};

/**
 * Reorder snippets for a project.
 * 
 * Usage:
 *   const { mutate: reorderSnippets } = useReorderSnippets(projectId);
 *   reorderSnippets([3, 1, 2, 5, 4]); // Array of snippet IDs in new order
 */
export const useReorderSnippets = (projectId: number | undefined) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (snippetIds: number[]): Promise<{ success: boolean; message: string }> => {
            const response = await api.put(`/api/snippets/${projectId}/reorder`, {
                snippet_ids: snippetIds,
            });
            return response.data;
        },
        onSuccess: () => {
            // Invalidate cached snippets to refetch with new order
            queryClient.invalidateQueries({ queryKey: ['snippets', projectId] });
        },
    });
};

// Legacy exports for backward compatibility during migration
// TODO: Remove these after all consumers are updated
export type { Project as Story };
export {
    useProjects as useStories,
    useProject as useStory,
    useCreateProject as useCreateStory,
    useUpdateProject as useUpdateStory,
    useDeleteProject as useDeleteStory,
    useProjectSnippets as useStorySnippets,
    useSnippets as useStorySnippetsQuery,
    useLockSnippet as useLockStorySnippet,
    useArchivedSnippets as useArchivedStorySnippets,
    useRestoreSnippet as useRestoreStorySnippet,
    useDeleteSnippet as useDeleteStorySnippet,
};
