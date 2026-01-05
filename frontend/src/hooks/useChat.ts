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
    advance_phase?: boolean;
}

export interface SendMessageResponse {
    id: number;
    role: string;
    content: string;
    phase: string;
    phase_order: string[];
    phase_index: number;
    age_range: string | null;
    phase_description: string;
}

// Phase display info for UI
export const PHASE_DISPLAY_INFO: Record<string, { label: string; ageRange?: string }> = {
    GREETING: { label: "Welcome" },
    FAMILY_HISTORY: { label: "Family History" },
    CHILDHOOD: { label: "Childhood", ageRange: "Ages 0-12" },
    ADOLESCENCE: { label: "Adolescence", ageRange: "Ages 13-18" },
    EARLY_ADULTHOOD: { label: "Early Adulthood", ageRange: "Ages 19-35" },
    MIDLIFE: { label: "Midlife", ageRange: "Ages 36-60" },
    PRESENT: { label: "Present Day" },
    SYNTHESIS: { label: "Your Story" },
};

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
        mutationFn: async (data: SendMessageDto): Promise<SendMessageResponse> => {
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

// Phase jump response type (subset of SendMessageResponse)
export interface PhaseJumpResponse {
    phase: string;
    phase_order: string[];
    phase_index: number;
    age_range: string | null;
    phase_description: string;
}

// Jump to a specific phase/chapter
export const useJumpToPhase = (projectId: number | undefined) => {
    return useMutation({
        mutationFn: async (targetPhase: string): Promise<PhaseJumpResponse> => {
            if (!projectId) {
                throw new Error('Project ID is required');
            }
            const response = await api.put<PhaseJumpResponse>(
                `/api/interview/${projectId}/phase`,
                { target_phase: targetPhase }
            );
            return response.data;
        },
    });
};

// Legacy export for backward compatibility
export { useProjectMessages as useStoryMessages };
