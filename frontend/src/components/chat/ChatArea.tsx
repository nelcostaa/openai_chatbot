import { useState, useRef, useEffect } from "react";
import { PhaseTimeline } from "./PhaseTimeline";
import { ChatMessage } from "./ChatMessage";
import { AgeSelectionCards } from "./AgeSelectionCards";
import { InputBar } from "./InputBar";
import { ChapterNamesDialog } from "./ChapterNamesDialog";
import { useProjectMessages, SendMessageResponse, PHASE_DISPLAY_INFO, useJumpToPhase, PhaseJumpResponse, useUpdateChapterNames, getChapterLabel, type ChapterNames } from "@/hooks/useChat";
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
  initialPhase?: string;
  initialAgeRange?: string | null;
  initialChapterNames?: ChapterNames | null;
}

export function ChatArea({ sendMessage, projectId, initialPhase, initialAgeRange, initialChapterNames }: ChatAreaProps) {
  const queryClient = useQueryClient();
  const { data: apiMessages = [], isLoading } = useProjectMessages(projectId);
  const [selectedAge, setSelectedAge] = useState<string | null>(initialAgeRange || null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Phase jump mutation
  const jumpToPhase = useJumpToPhase(projectId);

  // Chapter names state and mutation
  const [chapterNames, setChapterNames] = useState<ChapterNames | null>(initialChapterNames || null);
  const [isChapterNamesDialogOpen, setIsChapterNamesDialogOpen] = useState(false);
  const updateChapterNames = useUpdateChapterNames(projectId);

  // Phase state tracking - initialize with project data if available
  const [phaseState, setPhaseState] = useState<PhaseState>({
    phase: initialPhase || "GREETING",
    phaseOrder: [],
    phaseIndex: 0,
    ageRange: initialAgeRange || null,
  });

  // Update state when project data loads (for returning to existing projects)
  useEffect(() => {
    if (initialPhase || initialAgeRange) {
      setPhaseState(prev => ({
        ...prev,
        phase: initialPhase || prev.phase,
        ageRange: initialAgeRange || prev.ageRange,
      }));
      if (initialAgeRange) {
        setSelectedAge(initialAgeRange);
      }
    }
  }, [initialPhase, initialAgeRange]);

  // Update chapter names when initial data changes
  useEffect(() => {
    if (initialChapterNames !== undefined) {
      setChapterNames(initialChapterNames);
    }
  }, [initialChapterNames]);

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

  // Handle clicking on a phase in the timeline to jump to it
  const handlePhaseSelect = async (phaseId: string) => {
    // Don't jump if already on this phase or if jumping is in progress
    if (phaseId === phaseState.phase || jumpToPhase.isPending) {
      return;
    }

    try {
      const response = await jumpToPhase.mutateAsync(phaseId);
      // Update phase state with response from backend
      setPhaseState(prev => ({
        ...prev,
        phase: response.current_phase,
        phaseIndex: response.phase_index,
        phaseOrder: response.phase_order,
      }));
      // Refresh messages to show any transition message
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'messages'] });
    } catch (error) {
      console.error("Failed to jump to phase:", error);
    }
  };

  // Handle saving chapter names
  const handleSaveChapterNames = async (newChapterNames: ChapterNames) => {
    try {
      await updateChapterNames.mutateAsync(newChapterNames);
      setChapterNames(newChapterNames);
      setIsChapterNamesDialogOpen(false);
      // Invalidate project query to refresh chapter names
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    } catch (error) {
      console.error("Failed to save chapter names:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading conversation...</p>
      </div>
    );
  }

  // Get next phase name for button display (use custom name if available)
  const nextPhaseIndex = phaseState.phaseIndex + 1;
  const nextPhaseName = nextPhaseIndex < phaseState.phaseOrder.length
    ? getChapterLabel(phaseState.phaseOrder[nextPhaseIndex], chapterNames)
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
        onPhaseSelect={handlePhaseSelect}
        isJumping={jumpToPhase.isPending}
        chapterNames={chapterNames}
        onEditChapterNames={() => setIsChapterNamesDialogOpen(true)}
      />

      {/* Chapter Names Edit Dialog */}
      <ChapterNamesDialog
        isOpen={isChapterNamesDialogOpen}
        onClose={() => setIsChapterNamesDialogOpen(false)}
        onSave={handleSaveChapterNames}
        currentChapterNames={chapterNames}
        phaseOrder={phaseState.phaseOrder}
        isSaving={updateChapterNames.isPending}
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
