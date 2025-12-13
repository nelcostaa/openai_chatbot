import { useState } from "react";
import { X, ChevronLeft, ChevronRight, RefreshCw, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { SnippetCard } from "@/components/projects/SnippetCard";
import { SnippetEditDialog } from "@/components/projects/SnippetEditDialog";
import type { Snippet, UpdateSnippetDto } from "@/hooks/useProjects";

const CARDS_PER_PAGE = 6; // 3x2 grid

interface SnippetsOverlayProps {
    isOpen: boolean;
    onClose: () => void;
    snippets: Snippet[];
    isLoading?: boolean;
    isGenerating?: boolean;
    onGenerate?: () => void;
    onUpdateSnippet?: (snippetId: number, data: UpdateSnippetDto) => void;
    isUpdatingSnippet?: boolean;
    projectTitle?: string;
}

/**
 * Full-screen overlay for displaying project snippets (game cards).
 * 
 * Features:
 * - Full viewport overlay with backdrop blur
 * - 3x2 grid layout (6 cards per page)
 * - Pagination for >6 snippets
 * - Generate/Regenerate button
 * - Edit cards via dialog (click card or edit button)
 * - Loading states
 */
export function SnippetsOverlay({
    isOpen,
    onClose,
    snippets,
    isLoading = false,
    isGenerating = false,
    onGenerate,
    onUpdateSnippet,
    isUpdatingSnippet = false,
    projectTitle,
}: SnippetsOverlayProps) {
    const [currentPage, setCurrentPage] = useState(0);
    const [editingSnippet, setEditingSnippet] = useState<Snippet | null>(null);

    // Calculate pagination
    const totalPages = Math.ceil(snippets.length / CARDS_PER_PAGE);
    const startIndex = currentPage * CARDS_PER_PAGE;
    const endIndex = startIndex + CARDS_PER_PAGE;
    const currentSnippets = snippets.slice(startIndex, endIndex);

    // Reset to first page when snippets change
    const handlePrevPage = () => {
        setCurrentPage((prev) => Math.max(0, prev - 1));
    };

    const handleNextPage = () => {
        setCurrentPage((prev) => Math.min(totalPages - 1, prev + 1));
    };

    // Reset page when overlay closes
    const handleClose = () => {
        setCurrentPage(0);
        setEditingSnippet(null);
        onClose();
    };

    // Handle edit card click
    const handleEditCard = (snippet: Snippet) => {
        setEditingSnippet(snippet);
    };

    // Handle save edit
    const handleSaveEdit = (data: UpdateSnippetDto) => {
        if (editingSnippet?.id && onUpdateSnippet) {
            onUpdateSnippet(editingSnippet.id, data);
            setEditingSnippet(null);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-background/80 backdrop-blur-md"
                onClick={handleClose}
            />

            {/* Overlay content */}
            <div className="relative z-10 w-full max-w-6xl mx-4 max-h-[90vh] flex flex-col bg-card/95 backdrop-blur-md rounded-2xl border border-border shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h2 className="font-project text-xl font-semibold text-foreground">
                                {projectTitle || "Your Story"}
                            </h2>
                            <p className="text-sm text-muted-foreground">
                                {snippets.length} {snippets.length === 1 ? "card" : "cards"} generated
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {onGenerate && (
                            <Button
                                variant="outline"
                                onClick={onGenerate}
                                disabled={isGenerating}
                                className="h-11 px-4"
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                        Generating...
                                    </>
                                ) : snippets.length > 0 ? (
                                    <>
                                        <RefreshCw className="w-4 h-4 mr-2" />
                                        Regenerate
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="w-4 h-4 mr-2" />
                                        Generate Cards
                                    </>
                                )}
                            </Button>
                        )}
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={handleClose}
                            className="h-11 w-11"
                        >
                            <X className="w-5 h-5" />
                        </Button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6">
                    {isLoading || isGenerating ? (
                        <div className="flex flex-col items-center justify-center h-64">
                            <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
                            <p className="text-lg text-muted-foreground">
                                {isGenerating ? "Generating your story cards..." : "Loading cards..."}
                            </p>
                        </div>
                    ) : snippets.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {currentSnippets.map((snippet, index) => (
                                <SnippetCard
                                    key={snippet.id || `${snippet.title}-${startIndex + index}`}
                                    snippet={snippet}
                                    index={startIndex + index}
                                    className="animate-fade-in"
                                    onEdit={onUpdateSnippet ? handleEditCard : undefined}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-64 text-center px-6">
                            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                                <Sparkles className="w-8 h-8 text-primary" />
                            </div>
                            <h3 className="font-project text-lg font-semibold text-foreground mb-2">
                                No cards yet
                            </h3>
                            <p className="text-muted-foreground text-base max-w-md mb-4">
                                Generate story cards from your interview to capture the memorable moments of your life story.
                            </p>
                            {onGenerate && (
                                <Button onClick={onGenerate} disabled={isGenerating}>
                                    <Sparkles className="w-4 h-4 mr-2" />
                                    Generate Cards
                                </Button>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer with pagination */}
                {snippets.length > CARDS_PER_PAGE && (
                    <div className="flex items-center justify-between p-6 border-t border-border">
                        <Button
                            variant="outline"
                            onClick={handlePrevPage}
                            disabled={currentPage === 0}
                            className="h-11"
                        >
                            <ChevronLeft className="w-4 h-4 mr-2" />
                            Previous
                        </Button>
                        <span className="text-sm text-muted-foreground">
                            Page {currentPage + 1} of {totalPages}
                        </span>
                        <Button
                            variant="outline"
                            onClick={handleNextPage}
                            disabled={currentPage === totalPages - 1}
                            className="h-11"
                        >
                            Next
                            <ChevronRight className="w-4 h-4 ml-2" />
                        </Button>
                    </div>
                )}
            </div>

            {/* Edit Dialog */}
            <SnippetEditDialog
                snippet={editingSnippet}
                isOpen={!!editingSnippet}
                onClose={() => setEditingSnippet(null)}
                onSave={handleSaveEdit}
                isSaving={isUpdatingSnippet}
            />
        </div>
    );
}
