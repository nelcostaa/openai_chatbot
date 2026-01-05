import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, FolderOpen, ArrowRight, User, LogOut, Play, Sparkles, BookOpen, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { SnippetPreview } from "@/components/projects/SnippetPreview";
import { useProjects, useDeleteProject } from "@/hooks/useProjects";
import { useLogout, useCurrentUser } from "@/hooks/useAuth";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

export default function MyProjects() {
    const navigate = useNavigate();
    const { data: projects, isLoading } = useProjects();
    const { data: user } = useCurrentUser();
    const deleteMutation = useDeleteProject();
    const logout = useLogout();

    // State for snippet preview modal
    const [previewProjectId, setPreviewProjectId] = useState<number | null>(null);
    const [isPreviewOpen, setIsPreviewOpen] = useState(false);

    const currentDate = new Date().toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
    });

    const handleContinue = (id: string) => {
        navigate(`/project/${id}`);
    };

    const handleDelete = async (id: string) => {
        if (confirm("Are you sure you want to delete this project?")) {
            await deleteMutation.mutateAsync(parseInt(id));
        }
    };

    const handleNewProject = () => {
        navigate("/project/new");
    };

    const handleLogout = () => {
        logout();
    };

    const handlePreview = (id: string) => {
        setPreviewProjectId(parseInt(id));
        setIsPreviewOpen(true);
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <p className="text-lg text-muted-foreground">Loading your projects...</p>
            </div>
        );
    }

    const projectsArray = projects || [];
    const userName = user?.display_name || "there";
    const lastProject = projectsArray.length > 0 ? projectsArray[0] : null;
    const otherProjects = projectsArray.slice(1);

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="border-b border-border bg-card">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                            <FolderOpen className="w-5 h-5 text-primary" />
                        </div>
                        <span className="font-project text-xl font-semibold text-foreground">
                            LifeProject
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" className="h-11 w-11">
                            <User className="w-5 h-5" />
                        </Button>
                        <Button
                            variant="outline"
                            onClick={handleLogout}
                            className="h-11 px-4 text-base"
                        >
                            <LogOut className="w-4 h-4 mr-2" />
                            Sign Out
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-6xl mx-auto px-6 py-10">
                {/* Welcome Section */}
                <div className="mb-8">
                    <p className="text-muted-foreground text-base mb-2">{currentDate}</p>
                    <h1 className="font-project text-4xl font-semibold text-foreground">
                        Welcome back, {userName}
                    </h1>
                </div>

                {/* Hero: Continue Last Project - Only show if there's a project */}
                {lastProject && (
                    <section className="mb-12">
                        <div
                            className={cn(
                                "relative overflow-hidden rounded-2xl",
                                "bg-gradient-to-br from-primary/90 via-primary to-primary/80",
                                "p-8 md:p-10"
                            )}
                        >
                            {/* Background decorative elements */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
                            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4" />

                            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                                {/* Left side - Content */}
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className="flex items-center gap-2 px-3 py-1.5 bg-white/20 rounded-full">
                                            <Clock className="w-4 h-4 text-white/90" />
                                            <span className="text-sm font-medium text-white/90">
                                                Last edited {lastProject.updated_at || lastProject.created_at 
                                                    ? formatDistanceToNow(new Date(lastProject.updated_at || lastProject.created_at), { addSuffix: true })
                                                    : "recently"}
                                            </span>
                                        </div>
                                    </div>

                                    <h2 className="font-project text-3xl md:text-4xl font-bold text-white mb-3">
                                        Continue Your Story
                                    </h2>

                                    <p className="text-lg text-white/80 mb-2">
                                        Pick up where you left off on:
                                    </p>

                                    <p className="text-2xl md:text-3xl font-semibold text-white mb-6">
                                        "{lastProject.title}"
                                    </p>

                                    <p className="text-white/70 max-w-md">
                                        Every memory you capture brings your story closer to completion.
                                        Your family will treasure these moments forever.
                                    </p>
                                </div>

                                {/* Right side - CTA */}
                                <div className="flex flex-col items-center lg:items-end gap-4">
                                    <Button
                                        onClick={() => handleContinue(lastProject.id.toString())}
                                        size="lg"
                                        className={cn(
                                            "h-16 px-10 text-xl font-semibold",
                                            "bg-emerald-500 text-white hover:bg-emerald-600",
                                            "border-2 border-emerald-400",
                                            "shadow-xl shadow-emerald-500/30 hover:shadow-2xl hover:shadow-emerald-500/40",
                                            "transition-all duration-300 hover:scale-105",
                                            "group"
                                        )}
                                    >
                                        <Play className="w-6 h-6 mr-3 group-hover:scale-110 transition-transform" />
                                        Continue Project
                                        <ArrowRight className="w-5 h-5 ml-3 group-hover:translate-x-1 transition-transform" />
                                    </Button>

                                    <button
                                        onClick={() => handlePreview(lastProject.id.toString())}
                                        className="text-white/70 hover:text-white text-sm underline underline-offset-2 transition-colors"
                                    >
                                        Preview story cards
                                    </button>
                                </div>
                            </div>
                        </div>
                    </section>
                )}

                {/* Secondary: Start New Project */}
                <section className="mb-12">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="font-project text-xl font-semibold text-foreground">
                                {lastProject ? "Or start something new" : "Start Your First Project"}
                            </h3>
                            <p className="text-muted-foreground text-sm mt-1">
                                {lastProject
                                    ? "Begin capturing memories for another chapter of your life"
                                    : "Begin preserving your precious memories for generations to come"
                                }
                            </p>
                        </div>

                        <Button
                            onClick={handleNewProject}
                            variant={lastProject ? "outline" : "default"}
                            className={cn(
                                lastProject
                                    ? "h-12 px-5 text-base"
                                    : "h-14 px-8 text-lg font-medium"
                            )}
                        >
                            <Plus className="w-5 h-5 mr-2" />
                            New Project
                        </Button>
                    </div>
                </section>

                {/* Stats - Only show if there are projects */}
                {projectsArray.length > 0 && (
                    <div className="flex gap-8 mb-10 pb-10 border-b border-border">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                                <BookOpen className="w-6 h-6 text-primary" />
                            </div>
                            <div>
                                <p className="text-2xl font-semibold text-foreground">
                                    {projectsArray.length}
                                </p>
                                <p className="text-muted-foreground text-sm">
                                    {projectsArray.length === 1 ? "Project" : "Projects"}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Other Projects Grid - Only show if there are other projects */}
                {otherProjects.length > 0 && (
                    <div>
                        <h2 className="font-project text-2xl font-semibold text-foreground mb-6">
                            Other Projects
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {otherProjects.map((project) => (
                                <ProjectCard
                                    key={project.id}
                                    id={project.id.toString()}
                                    title={project.title}
                                    lastEdited={project.updated_at || project.created_at ? formatDistanceToNow(new Date(project.updated_at || project.created_at), { addSuffix: true }) : 'Just now'}
                                    progress=""
                                    status="in-progress"
                                    onContinue={handleContinue}
                                    onDelete={handleDelete}
                                    onPreview={handlePreview}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty State - Only show if no projects at all */}
                {projectsArray.length === 0 && (
                    <div className="text-center py-16 px-6 bg-card border border-border rounded-xl">
                        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Sparkles className="w-10 h-10 text-primary" />
                        </div>
                        <h3 className="font-project text-2xl font-semibold text-foreground mb-3">
                            Your story awaits
                        </h3>
                        <p className="text-muted-foreground text-lg mb-8 max-w-md mx-auto">
                            Start your first project and begin preserving your precious memories
                            for generations to come.
                        </p>
                        <Button
                            onClick={handleNewProject}
                            className="h-14 px-8 text-lg font-medium"
                        >
                            <Plus className="w-5 h-5 mr-2" />
                            Create Your First Project
                        </Button>
                    </div>
                )}
            </main>

            {/* Snippet Preview Modal */}
            <SnippetPreview
                projectId={previewProjectId}
                open={isPreviewOpen}
                onOpenChange={setIsPreviewOpen}
            />
        </div>
    );
}
