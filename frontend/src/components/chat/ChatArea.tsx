import { useState, useRef, useEffect } from "react";
import { PhaseTimeline } from "./PhaseTimeline";
import { ChatMessage } from "./ChatMessage";
import { AgeSelectionCards } from "./AgeSelectionCards";
import { InputBar } from "./InputBar";
import { useProjectMessages } from "@/hooks/useChat";
import { useQueryClient } from "@tanstack/react-query";

interface Message {
  id: string;
  type: "ai" | "user";
  content: string;
  showAgeCards?: boolean;
}

const initialPhases = [
  { id: "greeting", label: "Greeting", status: "complete" as const },
  { id: "age", label: "Age", status: "complete" as const },
  { id: "childhood", label: "Childhood", status: "active" as const },
  { id: "adolescence", label: "Adolescence", status: "inactive" as const },
  { id: "adulthood", label: "Adulthood", status: "inactive" as const },
  { id: "synthesis", label: "Synthesis", status: "inactive" as const },
];

interface ChatAreaProps {
  sendMessage: any;
  projectId: number | undefined;
}

export function ChatArea({ sendMessage, projectId }: ChatAreaProps) {
  const queryClient = useQueryClient();
  const { data: apiMessages = [], isLoading } = useProjectMessages(projectId);
  const [selectedAge, setSelectedAge] = useState<string>("31-45");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Convert API messages to display format
  const messages: Message[] = apiMessages.map((msg) => ({
    id: msg.id?.toString() || Date.now().toString(),
    type: msg.role === "assistant" ? "ai" : "user",
    content: msg.content,
    showAgeCards: false, // Can add logic to detect age selection prompts
  }));

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sendMessage.isPending]);

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage.mutateAsync({ message: content });
      // Invalidate messages query to refetch updated conversation
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'messages'] });
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  const handleAgeSelect = (age: string) => {
    setSelectedAge(age);
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading conversation...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      <PhaseTimeline phases={initialPhases} currentStep={2} totalSteps={5} />

      <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
        <div className="max-w-3xl mx-auto flex flex-col gap-4">
          {messages.map((message) => (
            <div key={message.id} className="flex flex-col gap-3">
              <ChatMessage type={message.type} content={message.content} />
              {message.showAgeCards && (
                <AgeSelectionCards onSelect={handleAgeSelect} selectedAge={selectedAge} />
              )}
            </div>
          ))}
          {sendMessage.isPending && <ChatMessage type="ai" content="" isTyping />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <InputBar onSend={handleSendMessage} disabled={sendMessage.isPending} />
    </div>
  );
}
