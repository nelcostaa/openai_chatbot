import { cn } from "@/lib/utils";
import { BookOpen } from "lucide-react";
import { PHASE_DISPLAY_INFO } from "@/hooks/useChat";

interface ChapterHeaderProps {
    phase: string;
    phaseIndex: number;
    totalPhases: number;
    className?: string;
}

export function ChapterHeader({
    phase,
    phaseIndex,
    totalPhases,
    className
}: ChapterHeaderProps) {
    const phaseInfo = PHASE_DISPLAY_INFO[phase] || { label: phase };

    // Don't show header for GREETING phase
    if (phase === "GREETING") {
        return null;
    }

    return (
        <div className={cn(
            "flex items-center justify-between px-6 py-4 bg-gradient-to-r from-primary/5 to-transparent border-b border-border",
            className
        )}>
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-primary" />
                </div>
                <div>
                    <h2 className="font-project text-lg font-semibold text-foreground">
                        {phaseInfo.label}
                    </h2>
                    {phaseInfo.ageRange && (
                        <p className="text-sm text-muted-foreground">
                            {phaseInfo.ageRange}
                        </p>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                    Chapter {phaseIndex + 1} of {totalPhases}
                </span>
                <div className="flex gap-1">
                    {Array.from({ length: totalPhases }).map((_, i) => (
                        <div
                            key={i}
                            className={cn(
                                "w-2 h-2 rounded-full transition-colors",
                                i < phaseIndex
                                    ? "bg-timeline-complete"
                                    : i === phaseIndex
                                        ? "bg-primary"
                                        : "bg-muted"
                            )}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
