import { useState, useMemo, useCallback } from "react";
import { X, ChevronLeft, ChevronRight, RefreshCw, Loader2, Sparkles, Archive, AlertTriangle, Lock, ChevronDown } from "lucide-react";
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
    archivedSnippets?: Snippet[];
    isLoading?: boolean;
    isGenerating?: boolean;
    onGenerate?: () => void;
    onUpdateSnippet?: (snippetId: number, data: UpdateSnippetDto) => void;
    onLockSnippet?: (snippetId: number) => void;
    onDeleteSnippet?: (snippetId: number) => void;
    onRestoreSnippet?: (snippetId: number) => void;
    onReorderSnippets?: (snippetIds: number[]) => void;
    isUpdatingSnippet?: boolean;
    projectTitle?: string;
    lockedCount?: number;
}

/**
 * Full-screen overlay for displaying project snippets (game cards).
 * 
 * Features:
 * - Full viewport overlay with backdrop blur
 * - 3x2 grid layout (6 cards per page)
 * - Pagination for >6 snippets
 * - Generate/Regenerate button with warning modal
 * - Edit, lock, and delete cards
 * - Archived cards tab for restoring deleted cards
 * - Loading states
 */
export function SnippetsOverlay({
    isOpen,
    onClose,
    snippets,
    archivedSnippets = [],
    isLoading = false,
    isGenerating = false,
    onGenerate,
    onUpdateSnippet,
    onLockSnippet,
    onDeleteSnippet,
    onRestoreSnippet,
    onReorderSnippets,
    isUpdatingSnippet = false,
    projectTitle,
    lockedCount = 0,
}: SnippetsOverlayProps) {
    const [currentPage, setCurrentPage] = useState(0);
    const [editingSnippet, setEditingSnippet] = useState<Snippet | null>(null);
    const [showRegenerateWarning, setShowRegenerateWarning] = useState(false);
    const [viewMode, setViewMode] = useState<'active' | 'archived'>('active');
    const [selectedPhase, setSelectedPhase] = useState<string>('all');
    const [isPhaseDropdownOpen, setIsPhaseDropdownOpen] = useState(false);

    // Local state for optimistic reordering
    const [localSnippets, setLocalSnippets] = useState<Snippet[]>(snippets);

    // Sync local snippets when props change
    useMemo(() => {
        setLocalSnippets(snippets);
    }, [snippets]);

    // Phase display names mapping
    const phaseDisplayNames: Record<string, string> = {
        all: "All Chapters",
        FAMILY_HISTORY: "Family History",
        CHILDHOOD: "Childhood",
        ADOLESCENCE: "Adolescence",
        EARLY_ADULTHOOD: "Early Adulthood",
        MIDLIFE: "Midlife",
        PRESENT: "Present Day",
    };

    // Get unique phases from snippets
    const availablePhases = useMemo(() => {
        const phases = new Set(snippets.map(s => s.phase).filter(Boolean));
        return ['all', ...Array.from(phases)];
    }, [snippets]);

    // Get the snippets to display based on view mode and phase filter
    const baseSnippets = viewMode === 'active' ? localSnippets : archivedSnippets;
    const displaySnippets = useMemo(() => {
        if (selectedPhase === 'all') return baseSnippets;
        return baseSnippets.filter(s => s.phase === selectedPhase);
    }, [baseSnippets, selectedPhase]);

    // Calculate pagination
    const totalPages = Math.ceil(displaySnippets.length / CARDS_PER_PAGE);
    const startIndex = currentPage * CARDS_PER_PAGE;
    const endIndex = startIndex + CARDS_PER_PAGE;
    const currentSnippets = displaySnippets.slice(startIndex, endIndex);

    // Count unlocked cards that will be affected by regeneration
    const unlockedCount = snippets.filter(s => !s.is_locked).length;

    // Reset to first page when snippets change
    const handlePrevPage = () => {
        setCurrentPage((prev) => Math.max(0, prev - 1));
    };

    const handleNextPage = () => {
        setCurrentPage((prev) => Math.min(totalPages - 1, prev + 1));
    };

    // Reset page when overlay closes or view mode changes
    const handleClose = () => {
        setCurrentPage(0);
        setEditingSnippet(null);
        setShowRegenerateWarning(false);
        setViewMode('active');
        setSelectedPhase('all');
        setIsPhaseDropdownOpen(false);
        onClose();
    };

    // Handle view mode change
    const handleViewModeChange = (mode: 'active' | 'archived') => {
        setViewMode(mode);
        setCurrentPage(0);
        setSelectedPhase('all');
    };

    // Handle phase filter change
    const handlePhaseChange = (phase: string) => {
        setSelectedPhase(phase);
        setCurrentPage(0);
        setIsPhaseDropdownOpen(false);
    };

    // Handle edit card click
    const handleEditCard = (snippet: Snippet) => {
        setEditingSnippet(snippet);
    };

    // Handle lock toggle
    const handleLockCard = (snippet: Snippet) => {
        if (snippet.id && onLockSnippet) {
            onLockSnippet(snippet.id);
        }
    };

    // Handle reorder - move snippet from one position to another
    const handleMoveSnippet = useCallback((fromIndex: number, toIndex: number) => {
        if (toIndex < 0 || toIndex >= localSnippets.length) return;

        const newSnippets = [...localSnippets];
        const [movedSnippet] = newSnippets.splice(fromIndex, 1);
        newSnippets.splice(toIndex, 0, movedSnippet);

        // Optimistic update
        setLocalSnippets(newSnippets);

        // Persist to backend
        if (onReorderSnippets) {
            const snippetIds = newSnippets
                .filter(s => s.id !== undefined)
                .map(s => s.id as number);

            if (snippetIds.length > 0) {
                onReorderSnippets(snippetIds);
            }
        }
    }, [localSnippets, onReorderSnippets]);

    // Handle delete
    const handleDeleteCard = (snippet: Snippet) => {
        if (snippet.id && onDeleteSnippet) {
            onDeleteSnippet(snippet.id);
        }
    };

    // Handle restore
    const handleRestoreCard = (snippet: Snippet) => {
        if (snippet.id && onRestoreSnippet) {
            onRestoreSnippet(snippet.id);
        }
    };

    // Handle regenerate with warning
    const handleRegenerateClick = () => {
        if (snippets.length > 0 && unlockedCount > 0) {
            setShowRegenerateWarning(true);
        } else {
            onGenerate?.();
        }
    };

    // Confirm regeneration
    const handleConfirmRegenerate = () => {
        setShowRegenerateWarning(false);
        onGenerate?.();
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
                    {/* Left section - Title */}
                    <div className="flex items-center gap-3 flex-1">
                        <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h2 className="font-project text-xl font-semibold text-foreground">
                                {projectTitle || "Your Story"}
                            </h2>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <span>{displaySnippets.length} {displaySnippets.length === 1 ? "card" : "cards"}{selectedPhase !== 'all' && ` in ${phaseDisplayNames[selectedPhase] || selectedPhase}`}</span>
                                {onReorderSnippets && viewMode === 'active' && displaySnippets.length > 1 && (
                                    <span className="text-primary">• Use arrows to reorder</span>
                                )}
                                {lockedCount > 0 && (
                                    <span className="flex items-center gap-1 text-amber-600">
                                        <Lock className="w-3 h-3" />
                                        {lockedCount} protected
                                    </span>
                                )}
                                {archivedSnippets.length > 0 && (
                                    <span className="text-muted-foreground">
                                        • {archivedSnippets.length} archived
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Center section - Chapter Filter Dropdown */}
                    {snippets.length > 0 && viewMode === 'active' && (
                        <div className="relative flex-shrink-0 mx-4">
                            <button
                                onClick={() => setIsPhaseDropdownOpen(!isPhaseDropdownOpen)}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2.5 rounded-lg border border-border",
                                    "bg-background hover:bg-muted transition-colors",
                                    "text-sm font-medium text-foreground",
                                    "min-w-[180px] justify-between"
                                )}
                                aria-haspopup="listbox"
                                aria-expanded={isPhaseDropdownOpen}
                                aria-label="Select chapter to filter cards"
                            >
                                <span>{phaseDisplayNames[selectedPhase] || selectedPhase}</span>
                                <ChevronDown className={cn(
                                    "w-4 h-4 text-muted-foreground transition-transform",
                                    isPhaseDropdownOpen && "rotate-180"
                                )} />
                            </button>

                            {/* Dropdown Menu */}
                            {isPhaseDropdownOpen && (
                                <>
                                    {/* Backdrop to close dropdown */}
                                    <div
                                        className="fixed inset-0 z-10"
                                        onClick={() => setIsPhaseDropdownOpen(false)}
                                    />
                                    <div className="absolute top-full left-0 mt-1 w-full min-w-[180px] py-1 bg-card border border-border rounded-lg shadow-lg z-20">
                                        {availablePhases.map((phase) => (
                                            <button
                                                key={phase}
                                                onClick={() => handlePhaseChange(phase)}
                                                className={cn(
                                                    "w-full px-4 py-2 text-left text-sm transition-colors",
                                                    selectedPhase === phase
                                                        ? "bg-primary/10 text-primary font-medium"
                                                        : "text-foreground hover:bg-muted"
                                                )}
                                                role="option"
                                                aria-selected={selectedPhase === phase}
                                            >
                                                {phaseDisplayNames[phase] || phase}
                                            </button>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* Right section - Actions */}
                    <div className="flex items-center gap-3 flex-1 justify-end">
                        {/* View Mode Toggle */}
                        {archivedSnippets.length > 0 && (
                            <div className="flex items-center rounded-lg border border-border overflow-hidden">
                                <button
                                    onClick={() => handleViewModeChange('active')}
                                    className={cn(
                                        "px-3 py-2 text-sm font-medium transition-colors",
                                        viewMode === 'active'
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-background text-muted-foreground hover:bg-muted"
                                    )}
                                >
                                    Active
                                </button>
                                <button
                                    onClick={() => handleViewModeChange('archived')}
                                    className={cn(
                                        "px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1.5",
                                        viewMode === 'archived'
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-background text-muted-foreground hover:bg-muted"
                                    )}
                                >
                                    <Archive className="w-3.5 h-3.5" />
                                    Archived
                                </button>
                            </div>
                        )}
                        {onGenerate && viewMode === 'active' && (
                            <Button
                                variant="outline"
                                onClick={handleRegenerateClick}
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
                    ) : displaySnippets.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {currentSnippets.map((snippet, index) => {
                                const globalIndex = startIndex + index;
                                return (
                                    <SnippetCard
                                        key={snippet.id || `${snippet.title}-${globalIndex}`}
                                        snippet={snippet}
                                        index={globalIndex}
                                        totalCount={displaySnippets.length}
                                        className="animate-fade-in"
                                        onEdit={viewMode === 'active' && onUpdateSnippet ? handleEditCard : undefined}
                                        onLock={viewMode === 'active' && onLockSnippet ? handleLockCard : undefined}
                                        onDelete={viewMode === 'active' && onDeleteSnippet ? handleDeleteCard : undefined}
                                        onRestore={viewMode === 'archived' && onRestoreSnippet ? handleRestoreCard : undefined}
                                        onMoveUp={viewMode === 'active' && onReorderSnippets ? () => handleMoveSnippet(globalIndex, globalIndex - 1) : undefined}
                                        onMoveDown={viewMode === 'active' && onReorderSnippets ? () => handleMoveSnippet(globalIndex, globalIndex + 1) : undefined}
                                        isArchived={viewMode === 'archived'}
                                    />
                                );
                            })}
                        </div>
                    ) : viewMode === 'archived' ? (
                        <div className="flex flex-col items-center justify-center h-64 text-center px-6">
                            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                                <Archive className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <h3 className="font-project text-lg font-semibold text-foreground mb-2">
                                No archived cards
                            </h3>
                            <p className="text-muted-foreground text-base max-w-md">
                                Deleted cards will appear here and can be restored.
                            </p>
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
                {displaySnippets.length > CARDS_PER_PAGE && (
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

            {/* Regeneration Warning Modal */}
            {showRegenerateWarning && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center">
                    <div
                        className="absolute inset-0 bg-black/50"
                        onClick={() => setShowRegenerateWarning(false)}
                    />
                    <div className="relative z-10 w-full max-w-md mx-4 bg-card rounded-xl border border-border shadow-2xl p-6">
                        <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <AlertTriangle className="w-6 h-6 text-amber-600" />
                            </div>
                            <div className="flex-1">
                                <h3 className="text-lg font-semibold text-foreground mb-2">
                                    Regenerate Cards?
                                </h3>
                                <p className="text-muted-foreground mb-4">
                                    {lockedCount > 0 ? (
                                        <>
                                            This will replace <strong>{unlockedCount} unlocked {unlockedCount === 1 ? 'card' : 'cards'}</strong> with new ones.
                                            Your <strong>{lockedCount} locked {lockedCount === 1 ? 'card' : 'cards'}</strong> will be preserved.
                                        </>
                                    ) : (
                                        <>
                                            This will replace all <strong>{snippets.length} {snippets.length === 1 ? 'card' : 'cards'}</strong> with new ones.
                                            Deleted cards can be restored from the Archived tab.
                                        </>
                                    )}
                                </p>
                                <p className="text-sm text-muted-foreground mb-4">
                                    <strong>Tip:</strong> Lock cards you want to keep before regenerating.
                                </p>
                                <div className="flex gap-3">
                                    <Button
                                        variant="outline"
                                        onClick={() => setShowRegenerateWarning(false)}
                                        className="flex-1"
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        onClick={handleConfirmRegenerate}
                                        className="flex-1"
                                    >
                                        <RefreshCw className="w-4 h-4 mr-2" />
                                        Regenerate
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
