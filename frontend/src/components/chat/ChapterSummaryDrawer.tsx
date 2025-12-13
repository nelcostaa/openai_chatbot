import { X, BookOpen, Feather } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface StorySnippet {
  id: string;
  chapter: string;
  content: string;
  timestamp: string;
}

interface ChapterSummaryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  snippets: StorySnippet[];
}

export function ChapterSummaryDrawer({
  isOpen,
  onClose,
  snippets,
}: ChapterSummaryDrawerProps) {
  return (
    <>
      {/* Backdrop with transparency */}
      <div
        className={cn(
          "fixed inset-0 bg-foreground/20 backdrop-blur-sm z-40 transition-opacity duration-300",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-lg bg-card/95 backdrop-blur-md border-l border-border shadow-2xl z-50 transition-transform duration-300 ease-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
              <Feather className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-project text-xl font-semibold text-foreground">
                Your Story So Far
              </h2>
              <p className="text-sm text-muted-foreground">
                {snippets.length} {snippets.length === 1 ? "memory" : "memories"} captured
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-11 w-11"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 h-[calc(100%-88px)] scrollbar-thin">
          {snippets.length > 0 ? (
            <div className="space-y-6">
              {snippets.map((snippet, index) => (
                <div
                  key={snippet.id}
                  className="animate-fade-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-1 rounded-full">
                      {snippet.chapter}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {snippet.timestamp}
                    </span>
                  </div>
                  <p className="font-project text-base text-foreground leading-relaxed pl-1 border-l-2 border-primary/30">
                    {snippet.content}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                <BookOpen className="w-8 h-8 text-primary" />
              </div>
              <h3 className="font-project text-lg font-semibold text-foreground mb-2">
                No memories yet
              </h3>
              <p className="text-muted-foreground text-base max-w-xs">
                As you share your stories in the chat, they will appear here as
                beautiful snippets of your life.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
