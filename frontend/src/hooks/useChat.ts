import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
    id?: number;
    project_id?: number;
    phase_context?: string;
    created_at?: string;
}

interface SendMessageDto {
    message: string;
}

interface SendMessageResponse {
    response: string;
}

// Fetch messages for a project
export const useProjectMessages = (projectId: number | undefined) => {
    return useQuery({
        queryKey: ['projects', projectId, 'messages'],
        queryFn: async () => {
            if (!projectId) {
                return [];
            }
            // API endpoint remains /api/stories/{id}/messages (backend unchanged)
            const response = await api.get<Message[]>(`/api/stories/${projectId}/messages`);
            return response.data;
        },
        enabled: !!projectId,
        staleTime: 30 * 1000, // 30 seconds
        refetchInterval: 5000, // Refetch every 5 seconds to get new messages
    });
};

// Send message to project interview endpoint
export const useSendMessage = (projectId: number | undefined) => {
    return useMutation({
        mutationFn: async (data: SendMessageDto) => {
            if (!projectId) {
                throw new Error('Project ID is required');
            }
            // API endpoint remains /api/interview/{id} (backend unchanged)
            const response = await api.post<SendMessageResponse>(
                `/api/interview/${projectId}`,
                data
            );
            return response.data;
        },
    });
};

// Legacy export for backward compatibility
export { useProjectMessages as useStoryMessages };
