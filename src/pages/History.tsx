import { Clock, Trash2 } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { Progress } from "@/components/ui/progress";

const History = () => {
  const { watchHistory, movieStates, clearHistory: clearHistoryApi } = useApp();

  const clearHistory = async () => {
    await clearHistoryApi();
    toast({ title: "History cleared" });
  };

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-5xl mx-auto animate-fade-in">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">Watch History</h1>
          </div>
          {watchHistory.length > 0 && (
            <Button variant="outline" onClick={clearHistory} className="gap-2">
              <Trash2 className="w-4 h-4" />
              Clear All
            </Button>
          )}
        </div>

        {watchHistory.length > 0 ? (
          <div className="space-y-4">
            {watchHistory.map((movie, index) => (
              <div
                key={`${movie.id}-${index}`}
                className="flex gap-4 p-4 bg-card rounded-lg hover:bg-secondary/50 transition-colors animate-fade-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <img
                  src={movie.image_url}
                  alt={movie.title}
                  className="w-32 h-20 object-cover rounded"
                />
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">{movie.title}</h3>
                  <p className="text-sm text-muted-foreground mb-2">
                    {movie.genre.join(" • ")} • {movie.duration_minutes} min
                  </p>
                  <Progress value={movieStates[movie.id]?.progress_percent ?? 0} />
                </div>
                <div className="text-sm text-muted-foreground">
                  {index === 0 ? "Just now" : `${index} day${index > 1 ? "s" : ""} ago`}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Clock className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No watch history</h2>
            <p className="text-muted-foreground">
              Movies and shows you watch will appear here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default History;
