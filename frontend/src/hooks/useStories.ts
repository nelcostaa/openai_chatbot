import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Story {
    id: number;
    title: string;
    description: string;
    created_at: string;
    updated_at: string;
    user_id: number;
}

// Snippet types for game card generation
export interface Snippet {
    id?: number;
    title: string;
    content: string;
    phase: string;
    theme: string;
    display_order: number;
}

export interface SnippetsResponse {
    success: boolean;
    snippets: Snippet[];
    count: number;
    model: string | null;
    error?: string;
}

interface CreateStoryDto {
    title: string;
    description?: string;
}

interface UpdateStoryDto {
    title?: string;
    description?: string;
}

// Fetch all stories for current user
export const useStories = () => {
    return useQuery({
        queryKey: ['stories'],
        queryFn: async () => {
            const response = await api.get<Story[]>('/api/stories/');
            return response.data;
        },
        staleTime: 2 * 60 * 1000, // 2 minutes
    });
};

// Fetch single story by ID
export const useStory = (storyId: number | undefined) => {
    return useQuery({
        queryKey: ['stories', storyId],
        queryFn: async () => {
            const response = await api.get<Story>(`/api/stories/${storyId}`);
            return response.data;
        },
        enabled: !!storyId,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
};

// Create new story
export const useCreateStory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (data: CreateStoryDto) => {
            const response = await api.post<Story>('/api/stories/', data);
            return response.data;
        },
        onSuccess: () => {
            // Invalidate stories list to refetch
            queryClient.invalidateQueries({ queryKey: ['stories'] });
        },
    });
};

// Update existing story
export const useUpdateStory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ id, data }: { id: number; data: UpdateStoryDto }) => {
            const response = await api.put<Story>(`/api/stories/${id}`, data);
            return response.data;
        },
        onSuccess: (updatedStory) => {
            // Invalidate both list and individual story queries
            queryClient.invalidateQueries({ queryKey: ['stories'] });
            queryClient.invalidateQueries({ queryKey: ['stories', updatedStory.id] });
        },
    });
};

// Delete story
export const useDeleteStory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/api/stories/${id}`);
            return id;
        },
        onSuccess: () => {
            // Invalidate stories list to refetch
            queryClient.invalidateQueries({ queryKey: ['stories'] });
        },
    });
};

/**
 * Generate story snippets (game cards) for a story.
 * 
 * This is a mutation because:
 * 1. It triggers AI processing (expensive operation)
 * 2. We want explicit user control over when to generate
 * 3. Results can be cached per story_id for future requests
 * 
 * Usage:
 *   const { mutate: generateSnippets, data, isPending } = useStorySnippets();
 *   generateSnippets(storyId);
 */
export const useStorySnippets = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (storyId: number): Promise<SnippetsResponse> => {
            // POST to /api/snippets/{story_id} - story_id is in the URL path
            const response = await api.post<SnippetsResponse>(`/api/snippets/${storyId}`);
            return response.data;
        },
        onSuccess: (data, storyId) => {
            // Cache the snippets for this story so we don't regenerate unnecessarily
            queryClient.setQueryData(['snippets', storyId], data);
        },
    });
};

/**
 * Get cached snippets for a story (if previously generated).
 * 
 * This is useful if you want to check if snippets exist before
 * showing a "regenerate" vs "generate" button.
 */
export const useCachedSnippets = (storyId: number | undefined) => {
    return useQuery({
        queryKey: ['snippets', storyId],
        queryFn: () => null, // We never fetch - only use cache
        enabled: false, // Disable automatic fetching
        staleTime: Infinity, // Never consider cached data stale
    });
};

/**
 * Reorder snippets for a story.
 * 
 * Usage:
 *   const { mutate: reorderSnippets } = useReorderSnippets(storyId);
 *   reorderSnippets([3, 1, 2, 5, 4]); // Array of snippet IDs in new order
 */
export const useReorderSnippets = (storyId: number | undefined) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (snippetIds: number[]): Promise<{ success: boolean; message: string }> => {
            const response = await api.put(`/api/snippets/${storyId}/reorder`, {
                snippet_ids: snippetIds,
            });
            return response.data;
        },
        onSuccess: () => {
            // Invalidate cached snippets to refetch with new order
            queryClient.invalidateQueries({ queryKey: ['snippets', storyId] });
        },
    });
};
