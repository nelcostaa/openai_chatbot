import { FolderOpen, Clock, CheckCircle, Trash2, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ProjectCardProps {
    id: string;
    title: string;
    lastEdited: string;
    progress: string;
    status: "in-progress" | "completed";
    onContinue: (id: string) => void;
    onDelete: (id: string) => void;
    onPreview?: (id: string) => void;
}

export function ProjectCard({
    id,
    title,
    lastEdited,
    progress,
    status,
    onContinue,
    onDelete,
    onPreview,
}: ProjectCardProps) {
    return (
        <div className="bg-card border border-border rounded-xl p-6 hover:shadow-md transition-shadow duration-200">
            {/* Header with icon */}
            <div className="flex items-start justify-between mb-4">
                <div className="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center">
                    <FolderOpen className="w-7 h-7 text-primary" />
                </div>
                <div
                    className={`px-3 py-1.5 rounded-full text-sm font-medium ${status === "completed"
                        ? "bg-green-100 text-green-800"
                        : "bg-amber-100 text-amber-800"
                        }`}
                >
                    {status === "completed" ? "Completed" : "In Progress"}
                </div>
            </div>

            {/* Title */}
            <h3 className="font-project text-xl font-semibold text-foreground mb-2 leading-tight">
                {title}
            </h3>

            {/* Progress */}
            <p className="text-muted-foreground text-base mb-2">{progress}</p>

            {/* Last edited */}
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-6">
                <Clock className="w-4 h-4" />
                <span>Last edited {lastEdited}</span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
                <Button
                    onClick={() => onContinue(id)}
                    className="flex-1 h-12 text-base font-medium"
                >
                    {status === "completed" ? (
                        <>
                            <CheckCircle className="w-5 h-5 mr-2" />
                            View Project
                        </>
                    ) : (
                        "Continue Working"
                    )}
                </Button>

                {/* Preview Cards Button */}
                {onPreview && (
                    <Button
                        variant="outline"
                        size="icon"
                        className="h-12 w-12 text-muted-foreground hover:text-primary hover:border-primary"
                        onClick={() => onPreview(id)}
                        aria-label="Preview project cards"
                        tabIndex={0}
                    >
                        <Eye className="w-5 h-5" />
                    </Button>
                )}

                <Button
                    variant="outline"
                    size="icon"
                    className="h-12 w-12 text-muted-foreground hover:text-destructive hover:border-destructive"
                    onClick={() => onDelete(id)}
                >
                    <Trash2 className="w-5 h-5" />
                </Button>
            </div>
        </div>
    );
}
