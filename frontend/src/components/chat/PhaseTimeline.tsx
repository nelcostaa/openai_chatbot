import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { PHASE_DISPLAY_INFO } from "@/hooks/useChat";

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
}

export function PhaseTimeline({
  phases: legacyPhases,
  phaseOrder = [],
  currentPhaseIndex = 0,
  currentStep,
  totalSteps,
  currentPhase = ""
}: PhaseTimelineProps) {
  // Build phases from phaseOrder if provided, otherwise use legacy phases
  const phases: Phase[] = phaseOrder.length > 0
    ? phaseOrder.map((phaseId, index) => ({
      id: phaseId,
      label: PHASE_DISPLAY_INFO[phaseId]?.label || phaseId,
      status: index < currentPhaseIndex
        ? "complete" as const
        : index === currentPhaseIndex
          ? "active" as const
          : "inactive" as const,
    }))
    : legacyPhases || [];

  // Get current phase info for header
  const currentPhaseInfo = PHASE_DISPLAY_INFO[currentPhase] || { label: currentPhase };
  const stepNumber = currentStep ?? (currentPhaseIndex + 1);
  const totalStepCount = totalSteps ?? phases.length;

  // Don't show timeline for GREETING phase (before age selection)
  if (currentPhase === "GREETING" || phases.length === 0) {
    return null;
  }

  return (
    <div className="px-6 py-5 border-b border-border bg-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-foreground">
          {currentPhaseInfo.label}
          {PHASE_DISPLAY_INFO[currentPhase]?.ageRange && (
            <span className="text-muted-foreground font-normal ml-2">
              ({PHASE_DISPLAY_INFO[currentPhase].ageRange})
            </span>
          )}
        </h2>
        <span className="text-base text-muted-foreground">
          Chapter {stepNumber} of {totalStepCount}
        </span>
      </div>

      <div className="flex items-center gap-2">
        {phases.map((phase, index) => (
          <div key={phase.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all",
                  phase.status === "complete" && "bg-timeline-complete text-primary-foreground",
                  phase.status === "active" && "bg-timeline-active text-primary-foreground ring-4 ring-primary/20",
                  phase.status === "inactive" && "bg-timeline-inactive text-muted-foreground"
                )}
              >
                {phase.status === "complete" ? (
                  <Check className="w-5 h-5" />
                ) : (
                  index + 1
                )}
              </div>
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
