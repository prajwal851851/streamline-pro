import { useState } from "react";
import { Play, Plus, Check, Heart, Download } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Movie } from "@/types/api";
import { cn } from "@/lib/utils";
import { useApp } from "@/contexts/AppContext";
import { toast } from "@/hooks/use-toast";

interface MovieCardProps {
  movie: Movie;
  index?: number;
}

export function MovieCard({ movie, index = 0 }: MovieCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const navigate = useNavigate();
  const {
    addToMyList,
    removeFromMyList,
    isInMyList,
    addToFavorites,
    removeFromFavorites,
    isFavorite,
    addToDownloads,
    isDownloaded,
    addToHistory,
  } = useApp();

  const inMyList = isInMyList(movie.id);
  const isFav = isFavorite(movie.id);
  const downloaded = isDownloaded(movie.id);

  const handleAddToList = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (inMyList) {
      removeFromMyList(movie.id);
      toast({ title: "Removed from My List" });
    } else {
      addToMyList(movie.id);
      toast({ title: "Added to My List" });
    }
  };

  const handleFavorite = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isFav) {
      removeFromFavorites(movie.id);
      toast({ title: "Removed from Favorites" });
    } else {
      addToFavorites(movie.id);  // Fixed: Pass only movie.id, not entire movie object
      toast({ title: "Added to Favorites" });
    }
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!downloaded) {
      addToDownloads(movie.id);
      toast({ title: "Download started", description: movie.title });
    }
  };

  const handlePlay = () => {
    addToHistory(movie.id);
    toast({ title: "Now Playing", description: movie.title });
    navigate(`/movies/${movie.id}`);
  };

  return (
    <div
      className={cn(
        "relative flex-shrink-0 w-[200px] cursor-pointer transition-all duration-300 ease-out",
        isHovered && "z-20"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => navigate(`/watch/${movie.id}`)}
    >
      {/* Base Card */}
      <div
        className={cn(
          "relative aspect-[2/3] rounded-md overflow-hidden transition-all duration-300",
          isHovered && "scale-110 shadow-2xl"
        )}
      >
        <img
          src={movie.image_url}
          alt={movie.title}
          className="w-full h-full object-cover"
        />
        
        {/* Gradient Overlay */}
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent transition-opacity duration-300",
            isHovered ? "opacity-100" : "opacity-0"
          )}
        />

        {/* New Badge - Fixed: Use is_new instead of isNew */}
        {movie.is_new && (
          <div className="absolute top-2 left-2 px-2 py-0.5 bg-primary text-primary-foreground text-xs font-semibold rounded">
            NEW
          </div>
        )}

        {/* Rating Badge */}
        <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-background/80 text-foreground text-xs font-medium rounded border border-border">
          {movie.rating}
        </div>

        {/* Hover Content */}
        <div
          className={cn(
            "absolute inset-0 flex flex-col justify-end p-3 transition-all duration-300",
            isHovered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          )}
        >
          {/* Action Buttons */}
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={handlePlay}
              className="w-8 h-8 rounded-full bg-foreground flex items-center justify-center hover:bg-foreground/90 transition-colors"
            >
              <Play className="w-4 h-4 text-background fill-background" />
            </button>
            <button
              onClick={handleAddToList}
              className="w-8 h-8 rounded-full bg-secondary/80 border border-border flex items-center justify-center hover:bg-secondary transition-colors"
            >
              {inMyList ? (
                <Check className="w-4 h-4 text-primary" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={handleFavorite}
              className="w-8 h-8 rounded-full bg-secondary/80 border border-border flex items-center justify-center hover:bg-secondary transition-colors"
            >
              <Heart className={cn("w-4 h-4", isFav && "fill-primary text-primary")} />
            </button>
            <button
              onClick={handleDownload}
              className="w-8 h-8 rounded-full bg-secondary/80 border border-border flex items-center justify-center hover:bg-secondary transition-colors"
            >
              <Download className={cn("w-4 h-4", downloaded && "text-primary")} />
            </button>
          </div>

          {/* Match & Info */}
          <div className="flex items-center gap-2 text-xs">
            {movie.match_score ? (
              <span className="text-green-500 font-semibold">{movie.match_score}% Match</span>
            ) : null}
            <span className="text-muted-foreground">{movie.year}</span>
            <span className="text-muted-foreground">{movie.duration_minutes} min</span>
          </div>

          {/* Genres */}
          <div className="flex flex-wrap gap-1 mt-1">
            {movie.genre.slice(0, 2).map((g) => (
              <span key={g} className="text-xs text-muted-foreground">
                {g}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Title (visible on hover) */}
      <div
        className={cn(
          "absolute -bottom-8 left-0 right-0 text-center transition-all duration-300",
          isHovered ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"
        )}
      >
        <h3 className="text-sm font-medium truncate px-2">{movie.title}</h3>
      </div>
    </div>
  );
}