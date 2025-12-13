import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FolderOpen, Feather } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatArea } from "@/components/chat/ChatArea";
import { ChapterSummaryDrawer } from "@/components/chat/ChapterSummaryDrawer";
import { useProject, useCreateProject } from "@/hooks/useProjects";
import { useSendMessage } from "@/hooks/useChat";

export default function ProjectInterview() {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [isCreatingProject, setIsCreatingProject] = useState(false);

    const { data: project, isLoading } = useProject(id ? parseInt(id) : undefined);
    const sendMessage = useSendMessage(id ? parseInt(id) : undefined);
    const createProject = useCreateProject();

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

    const mockSnippets: any[] = [];

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
                        onClick={() => setIsDrawerOpen(true)}
                        className="h-11 px-4 text-base"
                    >
                        <Feather className="w-5 h-5 mr-2" />
                        View Project
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
                <ChatArea sendMessage={sendMessage} projectId={id ? parseInt(id) : undefined} />
            </div>

            {/* Chapter Summary Drawer */}
            <ChapterSummaryDrawer
                isOpen={isDrawerOpen}
                onClose={() => setIsDrawerOpen(false)}
                snippets={mockSnippets}
            />
        </div>
    );
}
