import { Download, Trash2, Wifi, WifiOff } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { movies } from "@/data/mockData";
import { MovieCard } from "@/components/MovieCard";
import { toast } from "@/hooks/use-toast";

const Downloads = () => {
  const { downloads, removeFromDownloads } = useApp();

  const handleRemove = (id: string) => {
    removeFromDownloads(id);
    toast({ title: "Download removed" });
  };

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-5xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Download className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">Your Downloads</h1>
        </div>

        {/* Storage Info */}
        <div className="bg-card p-4 rounded-lg mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Storage Used</span>
            <span className="text-sm text-muted-foreground">
              {downloads.length * 1.2} GB of 10 GB
            </span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${Math.min(downloads.length * 12, 100)}%` }}
            />
          </div>
        </div>

        {downloads.length > 0 ? (
          <div className="space-y-4">
            {downloads.map((movie, index) => (
              <div
                key={movie.id}
                className="flex gap-4 p-4 bg-card rounded-lg hover:bg-secondary/50 transition-colors animate-fade-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <img
                  src={movie.image}
                  alt={movie.title}
                  className="w-32 h-20 object-cover rounded"
                />
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">{movie.title}</h3>
                  <p className="text-sm text-muted-foreground mb-2">
                    {movie.genre.join(" • ")} • {movie.duration}
                  </p>
                  <div className="flex items-center gap-2">
                    <WifiOff className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-green-500">Available offline</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">1.2 GB</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemove(movie.id)}
                  >
                    <Trash2 className="w-4 h-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Download className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No downloads yet</h2>
            <p className="text-muted-foreground mb-6">
              Download movies and shows to watch offline!
            </p>
            <div className="mt-8">
              <h3 className="text-lg font-medium mb-4">Available for download</h3>
              <div className="flex flex-wrap justify-center gap-4">
                {movies.slice(0, 4).map((movie, index) => (
                  <MovieCard key={movie.id} movie={movie} index={index} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Downloads;
