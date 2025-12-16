import { Pencil, Lock, Unlock, Trash2, RotateCcw } from "lucide-react";
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
    className?: string;
    onEdit?: (snippet: Snippet) => void;
    onLock?: (snippet: Snippet) => void;
    onDelete?: (snippet: Snippet) => void;
    onRestore?: (snippet: Snippet) => void;
    isArchived?: boolean;
}

/**
 * A single snippet card component for displaying project highlights.
 * 
 * Designed to look like a printable game card with:
 * - Gradient background based on emotional theme
 * - Title and content with proper typography
 * - Phase indicator for context
 * - Consistent aspect ratio for printing
 * - Edit button on hover (when onEdit is provided)
 * - Lock/unlock toggle to protect cards during regeneration
 * - Delete button for soft-deletion
 * - Gold border ring when locked for clear visual indicator
 * - Restore button for archived cards
 */
export function SnippetCard({ snippet, index, className, onEdit, onLock, onDelete, onRestore, isArchived = false }: SnippetCardProps) {
    const gradient = themeGradients[snippet.theme] || themeGradients.default;
    const phaseName = phaseDisplayNames[snippet.phase] || snippet.phase;
    const isLocked = snippet.is_locked ?? false;

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
                // Card structure
                "group relative overflow-hidden rounded-xl",
                // Aspect ratio for print consistency (roughly 2.5:3.5 like playing cards)
                "aspect-[5/7] min-h-[280px]",
                // Gradient background
                "bg-gradient-to-br",
                gradient,
                // Shadow and hover effects
                "shadow-lg hover:shadow-xl transition-all duration-300",
                // Cursor when editable
                onEdit && "cursor-pointer",
                // LOCKED INDICATOR: Gold border ring when locked
                isLocked && !isArchived && "ring-4 ring-amber-400 ring-offset-2 ring-offset-background",
                // Archived indicator: opacity and dashed border
                isArchived && "opacity-75 ring-2 ring-dashed ring-muted-foreground/30",
                className
            )}
            role="article"
            aria-label={`Project card: ${snippet.title}${isLocked ? " (locked)" : ""}${isArchived ? " (archived)" : ""}`}
            onClick={onEdit ? handleEditClick : undefined}
            tabIndex={onEdit ? 0 : undefined}
            onKeyDown={onEdit ? (e) => e.key === "Enter" && onEdit(snippet) : undefined}
        >
            {/* Archived badge */}
            {isArchived && (
                <div className="absolute top-3 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1 px-2 py-1 bg-muted rounded-full shadow-lg">
                    <span className="text-xs font-semibold text-muted-foreground">Archived</span>
                </div>
            )}

            {/* Lock indicator badge - always visible when locked */}
            {isLocked && !isArchived && (
                <div className="absolute top-3 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1 px-2 py-1 bg-amber-400 rounded-full shadow-lg">
                    <Lock className="w-3 h-3 text-amber-900" />
                    <span className="text-xs font-semibold text-amber-900">Protected</span>
                </div>
            )}

            {/* Action buttons - appears on hover */}
            <div className={cn(
                "absolute z-20 flex gap-2",
                (isLocked || isArchived) ? "top-12 left-1/2 -translate-x-1/2" : "top-3 left-1/2 -translate-x-1/2",
                "opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            )}>
                {/* Restore button for archived cards */}
                {isArchived && onRestore && (
                    <button
                        onClick={handleRestoreClick}
                        className={cn(
                            "flex items-center gap-1.5 px-3 py-1.5",
                            "bg-emerald-500 hover:bg-emerald-600 rounded-full",
                            "text-sm font-medium text-white",
                            "shadow-lg"
                        )}
                        aria-label={`Restore ${snippet.title}`}
                    >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Restore
                    </button>
                )}
                {!isArchived && onEdit && (
                    <button
                        onClick={handleEditClick}
                        className={cn(
                            "flex items-center gap-1.5 px-3 py-1.5",
                            "bg-white/95 backdrop-blur-sm rounded-full",
                            "text-sm font-medium text-gray-700",
                            "hover:bg-white shadow-lg"
                        )}
                        aria-label={`Edit ${snippet.title}`}
                    >
                        <Pencil className="w-3.5 h-3.5" />
                        Edit
                    </button>
                )}
                {!isArchived && onLock && (
                    <button
                        onClick={handleLockClick}
                        className={cn(
                            "flex items-center justify-center w-9 h-9",
                            "backdrop-blur-sm rounded-full shadow-lg",
                            isLocked
                                ? "bg-amber-400 hover:bg-amber-500 text-amber-900"
                                : "bg-white/95 hover:bg-white text-gray-700"
                        )}
                        aria-label={isLocked ? `Unlock ${snippet.title}` : `Lock ${snippet.title}`}
                        title={isLocked ? "Unlock (allow regeneration)" : "Lock (protect from regeneration)"}
                    >
                        {isLocked ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
                    </button>
                )}
                {!isArchived && onDelete && (
                    <button
                        onClick={handleDeleteClick}
                        className={cn(
                            "flex items-center justify-center w-9 h-9",
                            "bg-white/95 backdrop-blur-sm rounded-full",
                            "text-red-600 hover:bg-red-50 shadow-lg"
                        )}
                        aria-label={`Delete ${snippet.title}`}
                        title="Delete card"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                )}
            </div>

            {/* Card number badge (optional) */}
                {index !== undefined && (
                    <div className="absolute top-3 left-3 w-8 h-8 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                        <span className="text-sm font-bold text-white">
                            {index + 1}
                        </span>
                    </div>
                )}

                {/* Phase badge */}
                <div className="absolute top-3 right-3">
                    <span className="px-2 py-1 text-xs font-medium bg-white/20 backdrop-blur-sm rounded-full text-white">
                        {phaseName}
                    </span>
                </div>

                {/* Content area */}
                <div className="absolute inset-0 flex flex-col justify-end p-5">
                    {/* Dark overlay for text readability */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />

                    {/* Text content */}
                    <div className="relative z-10 space-y-2">
                        <h3 className="text-lg font-bold text-white leading-tight">
                            {snippet.title}
                        </h3>
                        <p className="text-sm text-white/90 leading-relaxed line-clamp-6">
                            {snippet.content}
                        </p>
                    </div>
                </div>

                {/* Decorative corner accent */}
                <div className="absolute -bottom-8 -right-8 w-24 h-24 rounded-full bg-white/10" />
            </div>
            );
}
