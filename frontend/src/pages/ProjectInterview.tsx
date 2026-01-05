import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FolderOpen, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatArea } from "@/components/chat/ChatArea";
import { SnippetsOverlay } from "@/components/projects/SnippetsOverlay";
import { useProject, useCreateProject, useSnippets, useProjectSnippets, useUpdateSnippet, useArchivedSnippets, useLockSnippet, useDeleteSnippet, useRestoreSnippet, useReorderSnippets } from "@/hooks/useProjects";
import type { UpdateSnippetDto } from "@/hooks/useProjects";
import { useSendMessage } from "@/hooks/useChat";

export default function ProjectInterview() {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const [isOverlayOpen, setIsOverlayOpen] = useState(false);
    const [isCreatingProject, setIsCreatingProject] = useState(false);

    const projectId = id && id !== "new" ? parseInt(id) : undefined;

    const { data: project, isLoading } = useProject(projectId);
    const sendMessage = useSendMessage(projectId);
    const createProject = useCreateProject();

    // Snippets hooks
    const {
        data: snippetsData,
        isLoading: isLoadingSnippets
    } = useSnippets(projectId);
    const { data: archivedData } = useArchivedSnippets(projectId);
    const generateSnippets = useProjectSnippets();
    const updateSnippet = useUpdateSnippet();
    const lockSnippet = useLockSnippet();
    const deleteSnippet = useDeleteSnippet();
    const restoreSnippet = useRestoreSnippet();
    const reorderSnippets = useReorderSnippets(projectId);

    // Auto-create project when id === "new"
    useEffect(() => {
        if (id === "new" && !isCreatingProject && !createProject.isPending) {
            setIsCreatingProject(true);
            createProject.mutateAsync({
                title: "My New Project",
            }).then((newProject) => {
                // Navigate to the newly created project
                navigate(`/project/${newProject.id}`, { replace: true });
            }).catch((error) => {
                console.error("Failed to create project:", error);
                setIsCreatingProject(false);
            });
        }
    }, [id, isCreatingProject, createProject, navigate]);

    const handleGenerateSnippets = () => {
        if (projectId) {
            generateSnippets.mutate(projectId);
        }
    };

    const handleUpdateSnippet = (snippetId: number, data: UpdateSnippetDto) => {
        if (projectId) {
            updateSnippet.mutate({ snippetId, projectId, data });
        }
    };

    const handleLockSnippet = (snippetId: number) => {
        if (projectId) {
            lockSnippet.mutate({ snippetId, projectId });
        }
    };

    const handleDeleteSnippet = (snippetId: number) => {
        if (projectId) {
            deleteSnippet.mutate({ snippetId, projectId });
        }
    };

    const handleRestoreSnippet = (snippetId: number) => {
        if (projectId) {
            restoreSnippet.mutate({ snippetId, projectId });
        }
    };

    const handleReorderSnippets = (snippetIds: number[]) => {
        reorderSnippets.mutate(snippetIds);
    };

    if (isLoading || (id === "new" && (isCreatingProject || createProject.isPending))) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <p className="text-lg text-muted-foreground">
                    {id === "new" ? "Creating your project..." : "Loading project..."}
                </p>
            </div>
        );
    }

    if (!project && id !== "new") {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <p className="text-lg text-destructive">Project not found</p>
            </div>
        );
    }

    const snippets = snippetsData?.snippets || [];
    const archivedSnippets = archivedData?.snippets || [];
    const lockedCount = snippetsData?.locked_count || 0;

    return (
        <div className="flex flex-col h-screen w-full overflow-hidden bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card px-6 py-4 flex items-center gap-4">
                <Button
                    variant="ghost"
                    onClick={() => navigate("/dashboard")}
                    className="h-11 px-4 text-base"
                >
                    <ArrowLeft className="w-5 h-5 mr-2" />
                    Back to Projects
                </Button>

                <div className="flex items-center gap-3 ml-auto">
                    <Button
                        variant="outline"
                        onClick={() => setIsOverlayOpen(true)}
                        className="h-11 px-4 text-base"
                    >
                        <Sparkles className="w-5 h-5 mr-2" />
                        View Stories
                        {snippets.length > 0 && (
                            <span className="ml-2 bg-primary/10 text-primary text-xs px-2 py-0.5 rounded-full">
                                {snippets.length}
                            </span>
                        )}
                    </Button>
                    <div className="flex items-center gap-2">
                        <FolderOpen className="w-5 h-5 text-primary" />
                        <span className="font-project text-lg text-foreground">
                            {project?.title || "New Project"}
                        </span>
                    </div>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-hidden">
                <ChatArea
                    sendMessage={sendMessage}
                    projectId={projectId}
                    initialPhase={project?.current_phase}
                    initialAgeRange={project?.age_range}
                />
            </div>

            {/* Snippets Overlay */}
            <SnippetsOverlay
                isOpen={isOverlayOpen}
                onClose={() => setIsOverlayOpen(false)}
                snippets={snippets}
                archivedSnippets={archivedSnippets}
                isLoading={isLoadingSnippets}
                isGenerating={generateSnippets.isPending}
                onGenerate={handleGenerateSnippets}
                onUpdateSnippet={handleUpdateSnippet}
                onLockSnippet={handleLockSnippet}
                onDeleteSnippet={handleDeleteSnippet}
                onRestoreSnippet={handleRestoreSnippet}
                onReorderSnippets={handleReorderSnippets}
                isUpdatingSnippet={updateSnippet.isPending}
                projectTitle={project?.title}
                lockedCount={lockedCount}
            />
        </div>
    );
}
