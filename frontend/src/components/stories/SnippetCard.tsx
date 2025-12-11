import { cn } from "@/lib/utils";
import type { Snippet } from "@/hooks/useStories";

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
}

/**
 * A single snippet card component for displaying story highlights.
 * 
 * Designed to look like a printable game card with:
 * - Gradient background based on emotional theme
 * - Title and content with proper typography
 * - Phase indicator for context
 * - Consistent aspect ratio for printing
 */
export function SnippetCard({ snippet, index, className }: SnippetCardProps) {
    const gradient = themeGradients[snippet.theme] || themeGradients.default;
    const phaseName = phaseDisplayNames[snippet.phase] || snippet.phase;

    return (
        <div
            className={cn(
                // Card structure
                "relative overflow-hidden rounded-xl",
                // Aspect ratio for print consistency (roughly 2.5:3.5 like playing cards)
                "aspect-[5/7] min-h-[280px]",
                // Gradient background
                "bg-gradient-to-br",
                gradient,
                // Shadow and hover effects
                "shadow-lg hover:shadow-xl transition-shadow duration-300",
                className
            )}
            role="article"
            aria-label={`Story card: ${snippet.title}`}
        >
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
