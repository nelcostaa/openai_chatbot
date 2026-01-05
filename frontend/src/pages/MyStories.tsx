import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, BookOpen, ArrowRight, User, LogOut, Sparkles, PenLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StoryCard } from "@/components/stories/StoryCard";
import { SnippetPreview } from "@/components/stories/SnippetPreview";
import { useStories, useDeleteStory } from "@/hooks/useStories";
import { useLogout, useCurrentUser } from "@/hooks/useAuth";
import { formatDistanceToNow } from "date-fns";

export default function MyStories() {
  const navigate = useNavigate();
  const { data: stories, isLoading } = useStories();
  const { data: user } = useCurrentUser();
  const deleteMutation = useDeleteStory();
  const logout = useLogout();

  // State for snippet preview modal
  const [previewStoryId, setPreviewStoryId] = useState<number | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const currentDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const handleContinue = (id: string) => {
    navigate(`/story/${id}`);
  };

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to delete this story?")) {
      await deleteMutation.mutateAsync(parseInt(id));
    }
  };

  const handleNewStory = () => {
    navigate("/story/new");
  };

  const handleLogout = () => {
    logout();
  };

  const handlePreview = (id: string) => {
    setPreviewStoryId(parseInt(id));
    setIsPreviewOpen(true);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading your stories...</p>
      </div>
    );
  }

  const storiesArray = stories || [];
  const userName = user?.display_name || "there";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-primary" />
            </div>
            <span className="font-story text-xl font-semibold text-foreground">
              LifeStory
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
        <div className="mb-6">
          <p className="text-muted-foreground text-base mb-2">{currentDate}</p>
          <h1 className="font-story text-4xl font-semibold text-foreground mb-2">
            Welcome back, {userName}
          </h1>
        </div>

        {/* Hero Continue Story Section */}
        {storiesArray.length > 0 && (
          <div className="mb-10 relative overflow-hidden bg-gradient-to-br from-primary/10 via-primary/5 to-background border border-primary/20 rounded-2xl p-8">
            <div className="absolute top-4 right-4 opacity-10">
              <Sparkles className="w-32 h-32 text-primary" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center gap-2 text-primary mb-3">
                <PenLine className="w-5 h-5" />
                <span className="text-sm font-medium uppercase tracking-wide">Pick up where you left off</span>
              </div>
              <h2 className="font-story text-3xl font-semibold text-foreground mb-2">
                {storiesArray[0].title}
              </h2>
              <p className="text-muted-foreground text-lg mb-6 max-w-xl">
                Your story is waiting. Every memory you capture becomes a treasure for generations to come.
              </p>
              <Button
                onClick={() => handleContinue(storiesArray[0].id.toString())}
                size="lg"
                className="h-14 px-8 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-200 bg-primary hover:bg-primary/90"
              >
                Continue Your Story
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Secondary Actions */}
        <div className="flex flex-wrap gap-4 mb-10">
          <Button
            onClick={handleNewStory}
            variant="outline"
            className="h-12 px-5 text-base font-medium"
          >
            <Plus className="w-5 h-5 mr-2" />
            Start New Story
          </Button>
        </div>

        {/* Stories Grid - Only show if more than 1 story */}
        {storiesArray.length > 1 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-story text-2xl font-semibold text-foreground">
                All Your Stories
              </h2>
              <span className="text-muted-foreground text-sm">
                {storiesArray.length} stories
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {storiesArray.map((story) => (
                <StoryCard
                  key={story.id}
                  id={story.id.toString()}
                  title={story.title}
                  lastEdited={story.updated_at || story.created_at ? formatDistanceToNow(new Date(story.updated_at || story.created_at), { addSuffix: true }) : 'Just now'}
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

        {/* Empty State - Only shows when no stories */}
        {storiesArray.length === 0 && (
          <div className="text-center py-16 px-6 bg-card border border-border rounded-xl">
            <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <BookOpen className="w-10 h-10 text-primary" />
            </div>
            <h3 className="font-story text-2xl font-semibold text-foreground mb-3">
              No stories yet
            </h3>
            <p className="text-muted-foreground text-lg mb-6 max-w-md mx-auto">
              Start your first story and begin preserving your precious memories
              for generations to come.
            </p>
            <Button
              onClick={handleNewStory}
              className="h-14 px-8 text-lg font-medium"
            >
              <Plus className="w-5 h-5 mr-2" />
              Create Your First Story
            </Button>
          </div>
        )}
      </main>

      {/* Snippet Preview Modal */}
      <SnippetPreview
        storyId={previewStoryId}
        open={isPreviewOpen}
        onOpenChange={setIsPreviewOpen}
      />
    </div>
  );
}
