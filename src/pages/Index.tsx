import { useMemo } from "react";
import { HeroSection } from "@/components/HeroSection";
import { MovieCarousel } from "@/components/MovieCarousel";
import { useApp } from "@/contexts/AppContext";
import { Progress } from "@/components/ui/progress";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();
  const { movies, movieStates } = useApp();

  const derivedCategories = useMemo(() => {
    if (!movies.length) return [];
    return [
      { name: "Trending Now", movies: movies.filter((m) => m.is_trending) },
      { name: "New Releases", movies: movies.filter((m) => m.is_new) },
      { name: "Popular on StreamFlix", movies: [...movies].reverse() },
      {
        name: "Action & Adventure",
        movies: movies.filter((m) => m.genre.includes("Action") || m.genre.includes("Adventure")),
      },
      {
        name: "Comedies",
        movies: movies.filter((m) => m.genre.includes("Comedy")),
      },
      {
        name: "Horror",
        movies: movies.filter((m) => m.genre.includes("Horror")),
      },
      {
        name: "Documentaries",
        movies: movies.filter((m) => m.genre.includes("Documentary")),
      },
      {
        name: "Romantic Movies",
        movies: movies.filter((m) => m.genre.includes("Romance")),
      },
    ].filter((c) => c.movies.length);
  }, [movies]);

  const continueWatching = useMemo(() => {
    const enriched = movies
      .map((m) => ({ movie: m, state: movieStates[m.id] }))
      .filter((item) => item.state)
      .sort((a, b) => {
        const statusOrder = (s?: string) => (s === "watching" ? 0 : 1);
        const diff = statusOrder(a.state?.status) - statusOrder(b.state?.status);
        if (diff !== 0) return diff;
        return new Date(b.state?.last_watched_at ?? 0).getTime() - new Date(a.state?.last_watched_at ?? 0).getTime();
      });
    return enriched;
  }, [movies, movieStates]);

  return (
    <div className="pb-12">
      <HeroSection />

      <div className="px-4 -mt-32 relative z-10 space-y-6">
        {continueWatching.length > 0 && (
          <div className="bg-background/60 backdrop-blur rounded-xl p-4 border border-border/60">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-xl font-semibold">Continue Watching</h2>
              <span className="text-sm text-muted-foreground">
                {continueWatching.filter((c) => c.state?.status === "watching").length} watching ·{" "}
                {continueWatching.filter((c) => c.state?.status === "watched").length} finished
              </span>
            </div>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {continueWatching.map(({ movie, state }) => (
              <button
                key={movie.id}
                onClick={() => navigate(`/watch/${movie.id}`)}
                className="flex gap-3 text-left rounded-lg border border-border/70 p-3 hover:border-primary transition-colors"
              >
                  <div className="w-24 h-16 overflow-hidden rounded-md">
                    <img src={movie.image_url} alt={movie.title} className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold line-clamp-1">{movie.title}</p>
                      <span className="text-xs text-muted-foreground">
                        {state?.status === "watching" ? "Watching" : "Watched"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {movie.genre.slice(0, 2).join(" • ")} · {movie.year}
                    </p>
                    <Progress value={state?.progress_percent ?? 0} className="mt-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {state?.progress_percent ?? 0}% watched
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {derivedCategories.map((category) => (
          <MovieCarousel key={category.name} title={category.name} movies={category.movies} />
        ))}
      </div>
    </div>
  );
};

export default Index;
