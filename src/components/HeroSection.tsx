import { Play, Info, Plus, Volume2, VolumeX } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { useApp } from "@/contexts/AppContext";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export function HeroSection() {
  const [muted, setMuted] = useState(true);
  const { movies, addToMyList, isInMyList, addToHistory } = useApp();
  const featuredMovie = useMemo(
    () =>
      movies.find((m) => m.is_trending) ||
      movies.find((m) => m.is_new) ||
      movies[0],
    [movies]
  );

  if (!featuredMovie) return null;

  const handlePlay = () => {
    addToHistory(featuredMovie.id);
    toast({ title: "Now Playing", description: featuredMovie.title });
  };

  const handleAddToList = () => {
    addToMyList(featuredMovie.id);
    toast({ title: "Added to My List" });
  };

  return (
    <section className="relative h-[85vh] min-h-[600px] -mt-16 overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0">
        <img
          src={featuredMovie.image_url}
          alt={featuredMovie.title}
          className="w-full h-full object-cover animate-fade-in"
        />
        {/* Gradients */}
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
      </div>

      {/* Content */}
      <div className="relative h-full flex flex-col justify-center pt-16 px-4 max-w-2xl animate-slide-up">
        {/* Series Badge */}
        <div className="flex items-center gap-2 mb-4">
          <div className="bg-primary px-2 py-1 rounded text-primary-foreground font-bold text-xs tracking-widest">
            ORIGINAL
          </div>
          <span className="text-sm font-medium tracking-widest text-muted-foreground">
            SERIES
          </span>
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-bold mb-4 tracking-tight">
          {featuredMovie.title}
        </h1>

        {/* Ranking */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center justify-center bg-primary text-primary-foreground font-bold text-xs px-2 py-1 rounded">
            TOP 10
          </div>
          <span className="text-sm font-semibold">
            #{featuredMovie.rank} in TV Shows Today
          </span>
        </div>

        {/* Description */}
        <p className="text-base md:text-lg text-muted-foreground mb-6 line-clamp-3 max-w-xl">
          {featuredMovie.description}
        </p>

        {/* Buttons */}
        <div className="flex items-center gap-3">
          <Button
            onClick={handlePlay}
            size="lg"
            className="gap-2 px-8 bg-foreground text-background hover:bg-foreground/90 font-semibold"
          >
            <Play className="w-5 h-5 fill-current" />
            Play
          </Button>
          <Button
            onClick={handleAddToList}
            size="lg"
            variant="secondary"
            className="gap-2 px-6"
          >
            {isInMyList(featuredMovie.id) ? (
              <>
                <span className="text-primary">✓</span>
                In My List
              </>
            ) : (
              <>
                <Plus className="w-5 h-5" />
                My List
              </>
            )}
          </Button>
          <Button size="lg" variant="secondary" className="gap-2 px-6">
            <Info className="w-5 h-5" />
            More Info
          </Button>
        </div>
      </div>

      {/* Rating & Mute */}
      <div className="absolute bottom-32 right-8 flex items-center gap-4">
        <button
          onClick={() => setMuted(!muted)}
          className="w-10 h-10 rounded-full border border-muted-foreground/50 flex items-center justify-center hover:bg-secondary transition-colors"
        >
          {muted ? (
            <VolumeX className="w-5 h-5 text-muted-foreground" />
          ) : (
            <Volume2 className="w-5 h-5" />
          )}
        </button>
        <div className="flex items-center border-l-2 border-muted-foreground/50 pl-3 bg-secondary/50 pr-4 py-1">
          <span className="text-sm font-medium">{featuredMovie.rating}</span>
        </div>
      </div>
    </section>
  );
}
