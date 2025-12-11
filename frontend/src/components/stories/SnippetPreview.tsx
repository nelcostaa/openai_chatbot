import { Loader2, RefreshCw, X } from "lucide-react";
import { useEffect } from "react";

import { SnippetCard } from "./SnippetCard";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { useStorySnippets, useStory } from "@/hooks/useStories";
import { cn } from "@/lib/utils";

interface SnippetPreviewProps {
    storyId: number | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

/**
 * Modal/Sheet component for displaying generated story snippets.
 * 
 * Features:
 * - Automatically generates snippets when opened with a story ID
 * - Shows loading progress indicator during generation
 * - Displays cards in a responsive grid
 * - Allows regeneration of snippets
 * - Error handling with retry option
 */
export function SnippetPreview({ storyId, open, onOpenChange }: SnippetPreviewProps) {
    const { data: story } = useStory(storyId ?? undefined);
    const {
        mutate: generateSnippets,
        data: snippetsData,
        isPending,
        error,
        reset
    } = useStorySnippets();

    // Generate snippets when modal opens with a valid story ID
    useEffect(() => {
        if (open && storyId && !snippetsData && !isPending) {
            generateSnippets(storyId);
        }
    }, [open, storyId, snippetsData, isPending, generateSnippets]);

    // Reset state when modal closes
    useEffect(() => {
        if (!open) {
            // Small delay to allow close animation
            const timer = setTimeout(() => {
                reset();
            }, 300);
            return () => clearTimeout(timer);
        }
    }, [open, reset]);

    const handleRegenerate = () => {
        if (storyId) {
            reset();
            generateSnippets(storyId);
        }
    };

    const handleClose = () => {
        onOpenChange(false);
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent
                side="right"
                className="w-full sm:max-w-2xl lg:max-w-4xl overflow-y-auto"
            >
                <SheetHeader className="pb-4 border-b">
                    <div className="flex items-center justify-between pr-8">
                        <div>
                            <SheetTitle className="text-xl">
                                Story Snippets
                            </SheetTitle>
                            <SheetDescription>
                                {story?.title || "Loading..."} — Game card previews
                            </SheetDescription>
                        </div>

                        {/* Regenerate button - only show when we have data */}
                        {snippetsData?.success && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleRegenerate}
                                disabled={isPending}
                                className="gap-2"
                            >
                                <RefreshCw className={cn("w-4 h-4", isPending && "animate-spin")} />
                                Regenerate
                            </Button>
                        )}
                    </div>
                </SheetHeader>

                <div className="py-6">
                    {/* Loading State */}
                    {isPending && (
                        <div className="flex flex-col items-center justify-center py-16 space-y-4">
                            <div className="relative">
                                <Loader2 className="w-12 h-12 animate-spin text-primary" />
                            </div>
                            <div className="text-center space-y-2">
                                <p className="text-lg font-medium text-foreground">
                                    Generating your story cards...
                                </p>
                                <p className="text-sm text-muted-foreground max-w-md">
                                    Our AI is analyzing your story and creating memorable snippets.
                                    This usually takes 10-30 seconds.
                                </p>
                            </div>

                            {/* Progress indicator dots */}
                            <div className="flex gap-1 pt-2">
                                {[0, 1, 2].map((i) => (
                                    <div
                                        key={i}
                                        className="w-2 h-2 rounded-full bg-primary/30 animate-pulse"
                                        style={{ animationDelay: `${i * 200}ms` }}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {error && !isPending && (
                        <div className="flex flex-col items-center justify-center py-16 space-y-4">
                            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
                                <X className="w-8 h-8 text-destructive" />
                            </div>
                            <div className="text-center space-y-2">
                                <p className="text-lg font-medium text-foreground">
                                    Failed to generate snippets
                                </p>
                                <p className="text-sm text-muted-foreground max-w-md">
                                    {error instanceof Error ? error.message : "An unexpected error occurred"}
                                </p>
                            </div>
                            <Button onClick={handleRegenerate} variant="outline" className="gap-2">
                                <RefreshCw className="w-4 h-4" />
                                Try Again
                            </Button>
                        </div>
                    )}

                    {/* Success State - Show Cards */}
                    {snippetsData?.success && !isPending && (
                        <div className="space-y-6">
                            {/* Stats bar */}
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                <span>{snippetsData.count} cards generated</span>
                                {snippetsData.model && (
                                    <>
                                        <span className="text-muted-foreground/50">•</span>
                                        <span>Model: {snippetsData.model}</span>
                                    </>
                                )}
                            </div>

                            {/* Cards Grid */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {snippetsData.snippets.map((snippet, index) => (
                                    <SnippetCard
                                        key={`${snippet.title}-${index}`}
                                        snippet={snippet}
                                        index={index}
                                    />
                                ))}
                            </div>

                            {/* Footer hint */}
                            <p className="text-xs text-muted-foreground text-center pt-4 border-t">
                                These cards are designed for printing. Each card is under 300 characters.
                            </p>
                        </div>
                    )}

                    {/* Empty state (API returned success but no snippets) */}
                    {snippetsData && !snippetsData.success && !isPending && (
                        <div className="flex flex-col items-center justify-center py-16 space-y-4">
                            <p className="text-lg font-medium text-foreground">
                                No snippets generated
                            </p>
                            <p className="text-sm text-muted-foreground max-w-md text-center">
                                {snippetsData.error || "The story might not have enough content yet. Continue your interview to add more details."}
                            </p>
                        </div>
                    )}
                </div>
            </SheetContent>
        </Sheet>
    );
}
