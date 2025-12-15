import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tv, Play } from "lucide-react";
import { fetchStreamingMoviesByType } from "@/api/movies";
import { StreamingMovie } from "@/types/api";
import { useNavigate } from "react-router-dom";

const TvShows = () => {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery<StreamingMovie[]>({
    queryKey: ["streaming-movies", "show"],
    queryFn: () => fetchStreamingMoviesByType("show"),
  });

  const shows = useMemo(() => data || [], [data]);

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in space-y-6">
        <div className="flex items-center gap-3">
          <Tv className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">TV Shows</h1>
        </div>

        {isLoading && <p className="text-muted-foreground">Loading TV shows...</p>}
        {isError && <p className="text-destructive">Could not load TV shows.</p>}

        {!isLoading && !isError && shows.length === 0 && (
          <p className="text-muted-foreground">No TV shows available yet. Run the scraper to add some.</p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {shows.map((show) => (
            <button
              key={show.id}
              onClick={() => navigate(`/streaming/${show.id}`)}
              className="group relative rounded-lg overflow-hidden border border-border/70 hover:border-primary transition-colors"
            >
              <div className="aspect-[2/3] bg-muted">
                {show.poster_url ? (
                  <img
                    src={show.poster_url}
                    alt={show.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
                    No poster
                  </div>
                )}
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="absolute bottom-0 left-0 right-0 p-3 flex items-center justify-between gap-2 text-left">
                <div>
                  <p className="text-sm font-semibold text-white line-clamp-1">{show.title}</p>
                  <p className="text-xs text-white/80">
                    {show.year || "Unknown"} • {show.type}
                  </p>
                </div>
                <span className="w-8 h-8 inline-flex items-center justify-center rounded-full bg-white text-black shadow-lg">
                  <Play className="w-4 h-4 fill-black" />
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TvShows;
