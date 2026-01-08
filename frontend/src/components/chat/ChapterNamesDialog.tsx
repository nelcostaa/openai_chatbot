import { useState, useEffect } from "react";
import { Loader2, RotateCcw, Info } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PHASE_DISPLAY_INFO, type ChapterNames } from "@/hooks/useChat";

const MAX_CHAPTER_NAME_LENGTH = 40;

interface ChapterNamesDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (chapterNames: ChapterNames) => void;
    currentChapterNames: ChapterNames | null;
    phaseOrder: string[];
    isSaving?: boolean;
}

/**
 * Dialog for editing custom chapter display names.
 * 
 * Features:
 * - Edit display name for each chapter
 * - Character limit (40 chars)
 * - Reset individual or all chapters to default
 * - Visual-only notice to set expectations
 */
export function ChapterNamesDialog({
    isOpen,
    onClose,
    onSave,
    currentChapterNames,
    phaseOrder,
    isSaving = false,
}: ChapterNamesDialogProps) {
    // Local state for editable names
    const [editedNames, setEditedNames] = useState<ChapterNames>({});

    // Initialize form when dialog opens or chapter names change
    useEffect(() => {
        if (isOpen) {
            // Pre-populate with current custom names or empty
            setEditedNames(currentChapterNames || {});
        }
    }, [isOpen, currentChapterNames]);

    // Get display value for input (custom name or empty for placeholder)
    const getInputValue = (phaseId: string): string => {
        return editedNames[phaseId] || "";
    };

    // Get placeholder (default name)
    const getPlaceholder = (phaseId: string): string => {
        return PHASE_DISPLAY_INFO[phaseId]?.label || phaseId;
    };

    // Handle input change
    const handleNameChange = (phaseId: string, value: string) => {
        const trimmedValue = value.slice(0, MAX_CHAPTER_NAME_LENGTH);
        setEditedNames(prev => {
            const updated = { ...prev };
            if (trimmedValue === "" || trimmedValue === getPlaceholder(phaseId)) {
                // Remove if empty or same as default (revert to default)
                delete updated[phaseId];
            } else {
                updated[phaseId] = trimmedValue;
            }
            return updated;
        });
    };

    // Reset single chapter to default
    const handleResetOne = (phaseId: string) => {
        setEditedNames(prev => {
            const updated = { ...prev };
            delete updated[phaseId];
            return updated;
        });
    };

    // Reset all chapters to defaults
    const handleResetAll = () => {
        setEditedNames({});
    };

    // Save changes
    const handleSave = () => {
        onSave(editedNames);
    };

    // Check if there are unsaved changes
    const hasChanges = JSON.stringify(editedNames) !== JSON.stringify(currentChapterNames || {});

    // Filter out GREETING as it's not typically shown as a "chapter"
    const editablePhases = phaseOrder.filter(p => p !== "GREETING" && p !== "AGE_SELECTION");

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[500px] max-h-[85vh] overflow-hidden flex flex-col">
                <DialogHeader>
                    <DialogTitle>Edit Chapter Names</DialogTitle>
                    <DialogDescription>
                        Customize how your chapters are displayed in the timeline.
                    </DialogDescription>
                </DialogHeader>

                {/* Visual-only notice */}
                <Alert className="bg-muted/50 border-muted">
                    <Info className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                        These are <strong>display names only</strong>. The interview questions and prompts remain unchanged.
                    </AlertDescription>
                </Alert>

                {/* Chapter names form */}
                <div className="flex-1 overflow-y-auto py-2 space-y-4 pr-2">
                    {editablePhases.map((phaseId) => {
                        const defaultName = getPlaceholder(phaseId);
                        const currentValue = getInputValue(phaseId);
                        const hasCustomName = !!currentValue;
                        const ageRange = PHASE_DISPLAY_INFO[phaseId]?.ageRange;

                        return (
                            <div key={phaseId} className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <Label
                                        htmlFor={`chapter-${phaseId}`}
                                        className="text-sm font-medium"
                                    >
                                        {defaultName}
                                        {ageRange && (
                                            <span className="text-muted-foreground font-normal ml-1">
                                                ({ageRange})
                                            </span>
                                        )}
                                    </Label>
                                    {hasCustomName && (
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                                            onClick={() => handleResetOne(phaseId)}
                                            aria-label={`Reset ${defaultName} to default`}
                                        >
                                            <RotateCcw className="h-3 w-3 mr-1" />
                                            Reset
                                        </Button>
                                    )}
                                </div>
                                <Input
                                    id={`chapter-${phaseId}`}
                                    value={currentValue}
                                    onChange={(e) => handleNameChange(phaseId, e.target.value)}
                                    placeholder={defaultName}
                                    maxLength={MAX_CHAPTER_NAME_LENGTH}
                                    className="h-9"
                                    aria-describedby={`chapter-${phaseId}-hint`}
                                />
                                <p
                                    id={`chapter-${phaseId}-hint`}
                                    className="text-xs text-muted-foreground"
                                >
                                    {currentValue.length}/{MAX_CHAPTER_NAME_LENGTH} characters
                                </p>
                            </div>
                        );
                    })}
                </div>

                <DialogFooter className="flex-shrink-0 gap-2 sm:gap-0">
                    <Button
                        type="button"
                        variant="outline"
                        onClick={handleResetAll}
                        disabled={Object.keys(editedNames).length === 0}
                        className="mr-auto"
                    >
                        <RotateCcw className="h-4 w-4 mr-2" />
                        Reset All
                    </Button>
                    <Button
                        type="button"
                        variant="ghost"
                        onClick={onClose}
                        disabled={isSaving}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        onClick={handleSave}
                        disabled={isSaving || !hasChanges}
                    >
                        {isSaving ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            "Save Changes"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
