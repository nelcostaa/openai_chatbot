import { Check, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import { PHASE_DISPLAY_INFO, getChapterInfo, type ChapterNames } from "@/hooks/useChat";
import { Button } from "@/components/ui/button";

interface Phase {
  id: string;
  label: string;
  status: "complete" | "active" | "inactive";
}

interface PhaseTimelineProps {
  phases?: Phase[];
  phaseOrder?: string[];
  currentPhaseIndex?: number;
  currentStep?: number;
  totalSteps?: number;
  currentPhase?: string;
  onPhaseSelect?: (phaseId: string) => void;
  isJumping?: boolean;
  chapterNames?: ChapterNames | null;
  onEditChapterNames?: () => void;
}

export function PhaseTimeline({
  phases: legacyPhases,
  phaseOrder = [],
  currentPhaseIndex = 0,
  currentStep,
  totalSteps,
  currentPhase = "",
  onPhaseSelect,
  isJumping = false,
  chapterNames,
  onEditChapterNames,
}: PhaseTimelineProps) {
  // Build phases from phaseOrder if provided, otherwise use legacy phases
  // Use custom chapter names if available
  const phases: Phase[] = phaseOrder.length > 0
    ? phaseOrder.map((phaseId, index) => ({
      id: phaseId,
      label: getChapterInfo(phaseId, chapterNames).label,
      status: index < currentPhaseIndex
        ? "complete" as const
        : index === currentPhaseIndex
          ? "active" as const
          : "inactive" as const,
    }))
    : legacyPhases || [];

  // Get current phase info for header (use custom name if available)
  const currentPhaseInfo = getChapterInfo(currentPhase, chapterNames);
  const stepNumber = currentStep ?? (currentPhaseIndex + 1);
  const totalStepCount = totalSteps ?? phases.length;

  // Don't show timeline for GREETING phase (before age selection)
  if (currentPhase === "GREETING" || phases.length === 0) {
    return null;
  }

  // Handle click on phase ball
  const handlePhaseClick = (phaseId: string, index: number) => {
    // Don't allow clicking if already on this phase or during jump transition
    if (index === currentPhaseIndex || isJumping || !onPhaseSelect) {
      return;
    }
    onPhaseSelect(phaseId);
  };

  return (
    <div className="px-6 py-5 border-b border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-medium text-foreground">
            {currentPhaseInfo.label}
            {currentPhaseInfo.ageRange && (
              <span className="text-muted-foreground font-normal ml-2">
                ({currentPhaseInfo.ageRange})
              </span>
            )}
          </h2>
          {onEditChapterNames && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-foreground"
              onClick={onEditChapterNames}
              aria-label="Edit chapter names"
              title="Edit chapter names"
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
        <div className="flex items-center gap-3">
          {onPhaseSelect && (
            <span className="text-xs text-muted-foreground">
              Click any chapter to jump
            </span>
          )}
          <span className="text-base text-muted-foreground">
            Chapter {stepNumber} of {totalStepCount}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {phases.map((phase, index) => (
          <div key={phase.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <button
                type="button"
                onClick={() => handlePhaseClick(phase.id, index)}
                disabled={isJumping || index === currentPhaseIndex || !onPhaseSelect}
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all",
                  phase.status === "complete" && "bg-timeline-complete text-primary-foreground",
                  phase.status === "active" && "bg-timeline-active text-primary-foreground ring-4 ring-primary/20",
                  phase.status === "inactive" && "bg-timeline-inactive text-muted-foreground",
                  // Clickable styles
                  onPhaseSelect && index !== currentPhaseIndex && !isJumping && [
                    "cursor-pointer hover:scale-110 hover:ring-2 hover:ring-primary/40",
                    phase.status === "complete" && "hover:bg-timeline-complete/90",
                    phase.status === "inactive" && "hover:bg-muted hover:text-foreground",
                  ],
                  // Disabled styles
                  (isJumping || index === currentPhaseIndex || !onPhaseSelect) && "cursor-default",
                  isJumping && "opacity-50"
                )}
                aria-label={`Jump to ${phase.label}`}
                title={index === currentPhaseIndex ? "Current chapter" : `Jump to ${phase.label}`}
              >
                {phase.status === "complete" ? (
                  <Check className="w-5 h-5" />
                ) : (
                  index + 1
                )}
              </button>
              <span
                className={cn(
                  "text-sm mt-2 text-center",
                  phase.status === "active" ? "text-foreground font-medium" : "text-muted-foreground"
                )}
              >
                {phase.label}
              </span>
            </div>

            {index < phases.length - 1 && (
              <div
                className={cn(
                  "h-1 flex-1 mx-2 rounded-full transition-colors",
                  phase.status === "complete" ? "bg-timeline-complete" : "bg-timeline-inactive"
                )}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
