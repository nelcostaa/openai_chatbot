import { useState, useRef, useEffect } from "react";
import { PhaseTimeline } from "./PhaseTimeline";
import { ChatMessage } from "./ChatMessage";
import { AgeSelectionCards } from "./AgeSelectionCards";
import { InputBar } from "./InputBar";
import { useProjectMessages, SendMessageResponse, PHASE_DISPLAY_INFO } from "@/hooks/useChat";
import { useQueryClient } from "@tanstack/react-query";

interface Message {
  id: string;
  type: "ai" | "user";
  content: string;
}

interface PhaseState {
  phase: string;
  phaseOrder: string[];
  phaseIndex: number;
  ageRange: string | null;
}

interface ChatAreaProps {
  sendMessage: {
    mutateAsync: (data: { message: string; advance_phase?: boolean }) => Promise<SendMessageResponse>;
    isPending: boolean;
  };
  projectId: number | undefined;
}

export function ChatArea({ sendMessage, projectId }: ChatAreaProps) {
  const queryClient = useQueryClient();
  const { data: apiMessages = [], isLoading } = useProjectMessages(projectId);
  const [selectedAge, setSelectedAge] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Phase state tracking
  const [phaseState, setPhaseState] = useState<PhaseState>({
    phase: "GREETING",
    phaseOrder: [],
    phaseIndex: 0,
    ageRange: null,
  });

  // Determine if age selection should be shown
  // Show when: in GREETING phase AND no age selected yet
  const showAgeSelection = phaseState.phase === "GREETING" && !phaseState.ageRange && !selectedAge;

  // Convert API messages to display format
  const messages: Message[] = apiMessages.map((msg) => ({
    id: msg.id?.toString() || Date.now().toString(),
    type: msg.role === "assistant" ? "ai" : "user",
    content: msg.content,
  }));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sendMessage.isPending]);

  // Update phase state from last API response
  const updatePhaseState = (response: SendMessageResponse) => {
    setPhaseState({
      phase: response.phase,
      phaseOrder: response.phase_order,
      phaseIndex: response.phase_index,
      ageRange: response.age_range,
    });
    if (response.age_range) {
      setSelectedAge(response.age_range);
    }
  };

  const handleSendMessage = async (content: string) => {
    try {
      const response = await sendMessage.mutateAsync({ message: content });
      updatePhaseState(response);
      // Invalidate messages query to refetch updated conversation
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'messages'] });
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  const handleAgeSelect = async (ageRange: string, marker: string) => {
    setSelectedAge(ageRange);
    try {
      // Send the age selection marker to backend
      const response = await sendMessage.mutateAsync({ message: marker });
      updatePhaseState(response);
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'messages'] });
    } catch (error) {
      console.error("Failed to send age selection:", error);
      setSelectedAge(null); // Revert on error
    }
  };

  const handleNextChapter = async () => {
    // Get next phase name from phase order
    const nextIndex = phaseState.phaseIndex + 1;
    if (nextIndex < phaseState.phaseOrder.length) {
      const nextPhase = phaseState.phaseOrder[nextIndex];
      const marker = `[Moving to next phase: ${nextPhase}]`;
      try {
        const response = await sendMessage.mutateAsync({
          message: marker,
          advance_phase: true
        });
        updatePhaseState(response);
        queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'messages'] });
      } catch (error) {
        console.error("Failed to advance phase:", error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading conversation...</p>
      </div>
    );
  }

  // Get next phase name for button display
  const nextPhaseIndex = phaseState.phaseIndex + 1;
  const nextPhaseName = nextPhaseIndex < phaseState.phaseOrder.length
    ? PHASE_DISPLAY_INFO[phaseState.phaseOrder[nextPhaseIndex]]?.label || phaseState.phaseOrder[nextPhaseIndex]
    : "";

  // Default welcome message for new projects
  const defaultWelcomeMessage = {
    id: "welcome",
    type: "ai" as const,
    content: "Welcome! I'm here to help you capture your life story, chapter by chapter. Before we begin, please select your age range so I can tailor our journey together."
  };

  // Show welcome message if no messages and in GREETING phase
  const displayMessages = messages.length === 0 && showAgeSelection
    ? [defaultWelcomeMessage]
    : messages;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      {/* Phase Timeline - shows after age selection */}
      <PhaseTimeline
        phaseOrder={phaseState.phaseOrder}
        currentPhaseIndex={phaseState.phaseIndex}
        currentPhase={phaseState.phase}
      />

      <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
        <div className="max-w-3xl mx-auto flex flex-col gap-4">
          {displayMessages.map((message) => (
            <ChatMessage key={message.id} type={message.type} content={message.content} />
          ))}

          {/* Age Selection Cards - show in GREETING phase */}
          {showAgeSelection && (
            <AgeSelectionCards
              onSelect={handleAgeSelect}
              selectedAge={selectedAge || undefined}
              disabled={sendMessage.isPending}
            />
          )}

          {sendMessage.isPending && <ChatMessage type="ai" content="" isTyping />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <InputBar
        onSend={handleSendMessage}
        onNextChapter={handleNextChapter}
        disabled={sendMessage.isPending}
        showNextChapter={phaseState.ageRange !== null}
        currentPhase={phaseState.phase}
        nextPhaseName={nextPhaseName}
      />
    </div>
  );
}
