import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  type: "ai" | "user";
  content: string;
  isTyping?: boolean;
}

// Filter out system markers from displayed content
function filterSystemMarkers(content: string): string {
  return content
    .replace(/\[Moving to next phase: [^\]]+\]/g, "")
    .replace(/\[Age selected via button: [^\]]+\]/g, "")
    .trim();
}

export function ChatMessage({ type, content, isTyping }: ChatMessageProps) {
  const isAI = type === "ai";

  // Filter system markers from user messages
  const displayContent = filterSystemMarkers(content);

  // Don't render empty messages (e.g., messages that were only markers)
  if (!isTyping && !displayContent) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex gap-4 max-w-[90%] message-appear",
        isAI ? "self-start" : "self-end flex-row-reverse"
      )}
    >
      <div
        className={cn(
          "w-12 h-12 rounded-full flex items-center justify-center shrink-0",
          isAI ? "bg-secondary text-primary" : "bg-primary/10 text-primary"
        )}
      >
        {isAI ? <Bot className="w-6 h-6" /> : <User className="w-6 h-6" />}
      </div>

      <div
        className={cn(
          "px-5 py-4 rounded-2xl",
          isAI
            ? "bg-bubble-ai rounded-tl-md text-foreground"
            : "bg-bubble-user rounded-tr-md text-primary-foreground"
        )}
      >
        {isTyping ? (
          <div className="flex items-center gap-2 py-1">
            <span className="w-2.5 h-2.5 bg-current rounded-full animate-pulse-soft" style={{ animationDelay: "0ms" }} />
            <span className="w-2.5 h-2.5 bg-current rounded-full animate-pulse-soft" style={{ animationDelay: "200ms" }} />
            <span className="w-2.5 h-2.5 bg-current rounded-full animate-pulse-soft" style={{ animationDelay: "400ms" }} />
          </div>
        ) : (
          <p className="text-lg leading-relaxed">{displayContent}</p>
        )}
      </div>
    </div>
  );
}
