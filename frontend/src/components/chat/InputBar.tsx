import { useState } from "react";
import { Send, Mic, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface InputBarProps {
  onSend: (message: string) => void;
  onNextChapter?: () => void;
  disabled?: boolean;
  showNextChapter?: boolean;
  currentPhase?: string;
  nextPhaseName?: string;
}

// Phases where "Next Chapter" button should NOT appear
const PHASES_WITHOUT_NEXT_BUTTON = ["GREETING", "SYNTHESIS"];

export function InputBar({
  onSend,
  onNextChapter,
  disabled,
  showNextChapter = false,
  currentPhase = "",
  nextPhaseName = ""
}: InputBarProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleNextChapter = () => {
    if (onNextChapter && !disabled) {
      onNextChapter();
    }
  };

  // Determine if we should show the Next Chapter button
  const shouldShowNextChapter = showNextChapter &&
    !PHASES_WITHOUT_NEXT_BUTTON.includes(currentPhase) &&
    currentPhase !== "";

  return (
    <div className="p-5 border-t border-border bg-card">
      <form onSubmit={handleSubmit} className="flex items-end gap-4">
        <div className="flex-1">
          <div
            className={cn(
              "flex items-end bg-background rounded-xl border border-border transition-all",
              "input-glow focus-within:border-primary"
            )}
          >
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your response here..."
              disabled={disabled}
              rows={1}
              className={cn(
                "flex-1 bg-transparent px-5 py-4 text-lg text-foreground placeholder:text-muted-foreground",
                "resize-none focus:outline-none max-h-40 scrollbar-thin",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
              style={{ minHeight: "56px" }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <button
              type="button"
              className="p-4 text-muted-foreground hover:text-foreground transition-colors"
              title="Voice input (coming soon)"
            >
              <Mic className="w-6 h-6" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className={cn(
            "w-14 h-14 rounded-xl flex items-center justify-center transition-all",
            "bg-primary text-primary-foreground",
            "hover:bg-primary/90",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          <Send className="w-6 h-6" />
        </button>
      </form>

      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-muted-foreground">
          Take your time. There's no rush.
        </p>

        {shouldShowNextChapter && (
          <Button
            type="button"
            variant="outline"
            onClick={handleNextChapter}
            disabled={disabled}
            className="flex items-center gap-2 text-sm"
          >
            Next Chapter
            <ChevronRight className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
