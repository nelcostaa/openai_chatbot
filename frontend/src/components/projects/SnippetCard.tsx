import { Pencil, Lock, Unlock, Trash2, RotateCcw, ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Snippet } from "@/hooks/useProjects";

/**
 * Theme-to-gradient mapping for visual variety.
 * 
 * Each theme gets a distinct gradient that evokes its emotional tone:
 * - family: warm oranges/reds (warmth, love)
 * - growth: greens/teals (progress, nature)
 * - challenge: purples/blues (depth, overcoming)
 * - adventure: yellows/oranges (excitement, energy)
 * - love: pinks/roses (romance, heart)
 * - legacy: golds/ambers (timelessness, value)
 * - identity: indigos/violets (introspection)
 * - friendship: sky blues (trust, openness)
 */
const themeGradients: Record<string, string> = {
    family: "from-orange-400 via-rose-400 to-red-400",
    growth: "from-emerald-400 via-teal-400 to-cyan-400",
    challenge: "from-violet-400 via-purple-400 to-indigo-400",
    adventure: "from-amber-400 via-orange-400 to-yellow-400",
    love: "from-pink-400 via-rose-400 to-red-300",
    legacy: "from-amber-500 via-yellow-400 to-orange-400",
    identity: "from-indigo-400 via-violet-400 to-purple-400",
    friendship: "from-sky-400 via-blue-400 to-indigo-400",
    // Default fallback
    default: "from-slate-400 via-gray-400 to-zinc-400",
};

/**
 * Human-readable phase display names
 */
const phaseDisplayNames: Record<string, string> = {
    FAMILY_HISTORY: "Family History",
    CHILDHOOD: "Childhood",
    ADOLESCENCE: "Adolescence",
    EARLY_ADULTHOOD: "Early Adulthood",
    MIDLIFE: "Midlife",
    PRESENT: "Present Day",
};

interface SnippetCardProps {
    snippet: Snippet;
    index?: number;
    totalCount?: number;
    className?: string;
    onEdit?: (snippet: Snippet) => void;
    onLock?: (snippet: Snippet) => void;
    onDelete?: (snippet: Snippet) => void;
    onRestore?: (snippet: Snippet) => void;
    onMoveUp?: () => void;
    onMoveDown?: () => void;
    isArchived?: boolean;
}

/**
 * A single snippet card component for displaying project highlights.
 * 
 * Redesigned with integrated action controls:
 * - Gradient background based on emotional theme
 * - Title and content with proper typography
 * - Phase indicator for context
 * - Consistent aspect ratio for printing
 * - Actions integrated in bottom toolbar (no overlay conflicts)
 * - Lock/unlock toggle to protect cards during regeneration
 * - Gold border ring when locked for clear visual indicator
 * - Reorder controls in top-left corner
 */
export function SnippetCard({ snippet, index, totalCount, className, onEdit, onLock, onDelete, onRestore, onMoveUp, onMoveDown, isArchived = false }: SnippetCardProps) {
    const gradient = themeGradients[snippet.theme] || themeGradients.default;
    const phaseName = phaseDisplayNames[snippet.phase] || snippet.phase;
    const isLocked = snippet.is_locked ?? false;

    const canMoveUp = index !== undefined && index > 0;
    const canMoveDown = index !== undefined && totalCount !== undefined && index < totalCount - 1;

    const handleEditClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onEdit?.(snippet);
    };

    const handleLockClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onLock?.(snippet);
    };

    const handleDeleteClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete?.(snippet);
    };

    const handleRestoreClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onRestore?.(snippet);
    };

    return (
        <div
            className={cn(
                // Card structure - flex column for toolbar at bottom
                "group relative overflow-hidden rounded-xl flex flex-col",
                // Aspect ratio for print consistency (roughly 2.5:3.5 like playing cards)
                "aspect-[5/7] min-h-[280px]",
                // Gradient background
                "bg-gradient-to-br",
                gradient,
                // Shadow and hover effects
                "shadow-lg hover:shadow-xl transition-all duration-300",
                // LOCKED INDICATOR: Gold border ring when locked
                isLocked && !isArchived && "ring-4 ring-amber-400 ring-offset-2 ring-offset-background",
                // Archived indicator: opacity and dashed border
                isArchived && "opacity-75 ring-2 ring-dashed ring-muted-foreground/30",
                className
            )}
            role="article"
            aria-label={`Project card: ${snippet.title}${isLocked ? " (locked)" : ""}${isArchived ? " (archived)" : ""}`}
        >
            {/* Top bar with card number, reorder controls, and status badges */}
            <div className="relative z-20 flex items-start justify-between p-3">
                {/* Left side: Card number and reorder */}
                <div className="flex items-center gap-2">
                    {/* Card number badge */}
                    {index !== undefined && (
                        <div className="w-7 h-7 rounded-full bg-white/25 backdrop-blur-sm flex items-center justify-center">
                            <span className="text-xs font-bold text-white">
                                {index + 1}
                            </span>
                        </div>
                    )}

                    {/* Reorder controls - always visible */}
                    {!isArchived && (onMoveUp || onMoveDown) && (
                        <div className="flex gap-0.5">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onMoveUp?.();
                                }}
                                disabled={!canMoveUp}
                                className={cn(
                                    "w-6 h-6 rounded bg-white/20 backdrop-blur-sm flex items-center justify-center transition-all",
                                    canMoveUp
                                        ? "hover:bg-white/40 cursor-pointer"
                                        : "opacity-30 cursor-not-allowed"
                                )}
                                aria-label="Move card up"
                                tabIndex={0}
                            >
                                <ChevronUp className="w-4 h-4 text-white" />
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onMoveDown?.();
                                }}
                                disabled={!canMoveDown}
                                className={cn(
                                    "w-6 h-6 rounded bg-white/20 backdrop-blur-sm flex items-center justify-center transition-all",
                                    canMoveDown
                                        ? "hover:bg-white/40 cursor-pointer"
                                        : "opacity-30 cursor-not-allowed"
                                )}
                                aria-label="Move card down"
                                tabIndex={0}
                            >
                                <ChevronDown className="w-4 h-4 text-white" />
                            </button>
                        </div>
                    )}
                </div>

                {/* Center: Status badges */}
                <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
                    {/* Archived badge */}
                    {isArchived && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded-full shadow-lg">
                            <span className="text-xs font-semibold text-muted-foreground">Archived</span>
                        </div>
                    )}

                    {/* Lock indicator badge - always visible when locked */}
                    {isLocked && !isArchived && (
                        <div className="flex items-center gap-1 px-2 py-1 bg-amber-400 rounded-full shadow-lg">
                            <Lock className="w-3 h-3 text-amber-900" />
                            <span className="text-xs font-semibold text-amber-900">Protected</span>
                        </div>
                    )}
                </div>

                {/* Right side: Phase badge */}
                <span className="px-2 py-1 text-xs font-medium bg-white/20 backdrop-blur-sm rounded-full text-white">
                    {phaseName}
                </span>
            </div>

            {/* Content area - takes remaining space */}
            <div className="flex-1 relative flex flex-col justify-end p-4 pt-0">
                {/* Dark overlay for text readability */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent pointer-events-none" />

                {/* Text content */}
                <div className="relative z-10 space-y-2">
                    <h3 className="text-lg font-bold text-white leading-tight">
                        {snippet.title}
                    </h3>
                    <p className="text-sm text-white/90 leading-relaxed line-clamp-5">
                        {snippet.content}
                    </p>
                </div>
            </div>

            {/* Bottom action toolbar - always visible, integrated with card */}
            <div className="relative z-20 flex items-center justify-between gap-2 px-3 py-2.5 bg-black/40 backdrop-blur-sm border-t border-white/10">
                {/* Restore button for archived cards */}
                {isArchived && onRestore && (
                    <button
                        onClick={handleRestoreClick}
                        className={cn(
                            "flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5",
                            "bg-emerald-500 hover:bg-emerald-600 rounded-lg",
                            "text-sm font-medium text-white",
                            "transition-colors"
                        )}
                        aria-label={`Restore ${snippet.title}`}
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Restore Card
                    </button>
                )}

                {/* Active card actions */}
                {!isArchived && (
                    <>
                        {/* Edit button */}
                        {onEdit && (
                            <button
                                onClick={handleEditClick}
                                className={cn(
                                    "flex items-center gap-1.5 px-3 py-1.5",
                                    "bg-white/20 hover:bg-white/30 rounded-lg",
                                    "text-sm font-medium text-white",
                                    "transition-colors"
                                )}
                                aria-label={`Edit ${snippet.title}`}
                            >
                                <Pencil className="w-3.5 h-3.5" />
                                Edit
                            </button>
                        )}

                        {/* Lock/Unlock toggle */}
                        {onLock && (
                            <button
                                onClick={handleLockClick}
                                className={cn(
                                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors",
                                    isLocked
                                        ? "bg-amber-400 hover:bg-amber-500 text-amber-900"
                                        : "bg-white/20 hover:bg-white/30 text-white"
                                )}
                                aria-label={isLocked ? `Unlock ${snippet.title}` : `Lock ${snippet.title}`}
                                title={isLocked ? "Unlock (allow regeneration)" : "Lock (protect from regeneration)"}
                            >
                                {isLocked ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                                <span className="text-sm font-medium">{isLocked ? "Unlock" : "Lock"}</span>
                            </button>
                        )}

                        {/* Spacer */}
                        <div className="flex-1" />

                        {/* Delete button */}
                        {onDelete && (
                            <button
                                onClick={handleDeleteClick}
                                className={cn(
                                    "flex items-center gap-1.5 px-3 py-1.5",
                                    "bg-red-500/20 hover:bg-red-500/40 rounded-lg",
                                    "text-red-200 hover:text-white",
                                    "transition-colors"
                                )}
                                aria-label={`Delete ${snippet.title}`}
                                title="Delete card"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </>
                )}
            </div>

            {/* Decorative corner accent */}
            <div className="absolute -bottom-8 -right-8 w-24 h-24 rounded-full bg-white/10 pointer-events-none" />
        </div>
    );
}
