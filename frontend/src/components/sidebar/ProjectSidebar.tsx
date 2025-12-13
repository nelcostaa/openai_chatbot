import { useState } from "react";
import { Plus, Settings, FolderOpen, ChevronLeft, ChevronRight, Eye, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Link } from "react-router-dom";
import { useProjects } from "@/hooks/useProjects";
import { Skeleton } from "@/components/ui/skeleton";

interface ProjectSidebarProps {
    isCollapsed: boolean;
    onToggle: () => void;
    onPreviewProject?: (projectId: number) => void;
}

export function ProjectSidebar({ isCollapsed, onToggle, onPreviewProject }: ProjectSidebarProps) {
    const [activeProject, setActiveProject] = useState<number | null>(null);

    // Fetch real projects from API
    const { data: projects, isLoading, error } = useProjects();

    const handlePreviewClick = (e: React.MouseEvent, projectId: number) => {
        // Stop propagation so we don't also select the project
        e.stopPropagation();
        onPreviewProject?.(projectId);
    };

    return (
        <aside
            className={cn(
                "h-full bg-sidebar border-r border-sidebar-border flex flex-col shrink-0 transition-all duration-300",
                isCollapsed ? "w-20" : "w-72"
            )}
        >
            {/* Header */}
            <div className="p-4 border-b border-sidebar-border">
                <div className="flex items-center justify-between">
                    {!isCollapsed && (
                        <Link to="/" className="flex items-center gap-3">
                            <FolderOpen className="w-6 h-6 text-primary" />
                            <span className="text-lg font-semibold text-sidebar-foreground font-project">Life Project</span>
                        </Link>
                    )}
                    <button
                        onClick={onToggle}
                        className="p-3 rounded-lg hover:bg-sidebar-accent transition-colors text-sidebar-foreground"
                    >
                        {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                    </button>
                </div>

                <button
                    className={cn(
                        "mt-4 flex items-center justify-center gap-2 rounded-lg transition-colors",
                        "bg-primary text-primary-foreground hover:bg-primary/90",
                        isCollapsed ? "w-full p-3" : "w-full px-4 py-3 text-lg font-medium"
                    )}
                >
                    <Plus className="w-5 h-5" />
                    {!isCollapsed && "New Project"}
                </button>
            </div>

            {/* Projects List */}
            <div className="flex-1 overflow-y-auto p-3 scrollbar-thin">
                {!isCollapsed && (
                    <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider px-3 mb-3">
                        My Projects
                    </p>
                )}

                <div className="space-y-1">
                    {/* Loading state */}
                    {isLoading && (
                        <>
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="p-3 rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <Skeleton className="w-5 h-5 rounded" />
                                        {!isCollapsed && (
                                            <div className="flex-1 space-y-2">
                                                <Skeleton className="h-4 w-3/4" />
                                                <Skeleton className="h-3 w-1/2" />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </>
                    )}

                    {/* Error state */}
                    {error && !isCollapsed && (
                        <p className="text-sm text-destructive px-3 py-2">
                            Failed to load projects
                        </p>
                    )}

                    {/* Projects */}
                    {projects?.map((project) => (
                        <div
                            key={project.id}
                            className={cn(
                                "w-full flex items-center gap-3 p-3 rounded-lg transition-colors group",
                                activeProject === project.id
                                    ? "bg-sidebar-accent text-sidebar-foreground"
                                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                            )}
                        >
                            <button
                                onClick={() => setActiveProject(project.id)}
                                className="flex items-center gap-3 flex-1 min-w-0 text-left"
                                aria-label={`Select project: ${project.title}`}
                            >
                                <FolderOpen className="w-5 h-5 shrink-0" />
                                {!isCollapsed && (
                                    <div className="flex-1 min-w-0">
                                        <p className="text-base font-medium truncate">{project.title}</p>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-sm text-muted-foreground">
                                                {new Date(project.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </button>

                            {/* Preview button - only show when expanded */}
                            {!isCollapsed && (
                                <button
                                    onClick={(e) => handlePreviewClick(e, project.id)}
                                    className={cn(
                                        "p-2 rounded-lg transition-all",
                                        "opacity-0 group-hover:opacity-100",
                                        "hover:bg-primary/10 text-muted-foreground hover:text-primary",
                                        "focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    )}
                                    aria-label={`Preview snippets for ${project.title}`}
                                    tabIndex={0}
                                >
                                    <Eye className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    ))}

                    {/* Empty state */}
                    {!isLoading && !error && projects?.length === 0 && !isCollapsed && (
                        <p className="text-sm text-muted-foreground px-3 py-4 text-center">
                            No projects yet. Create your first one!
                        </p>
                    )}
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-sidebar-border">
                <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-lg">
                        M
                    </div>
                    {!isCollapsed && (
                        <div className="flex-1 min-w-0">
                            <p className="text-base font-medium text-sidebar-foreground truncate">Margaret</p>
                            <p className="text-sm text-muted-foreground">Free Plan</p>
                        </div>
                    )}
                    <button className="p-2 rounded-lg hover:bg-sidebar-accent transition-colors text-muted-foreground hover:text-sidebar-foreground">
                        <Settings className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </aside>
    );
}
