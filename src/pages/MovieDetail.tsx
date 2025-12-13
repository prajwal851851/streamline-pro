import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Play, Clock } from "lucide-react";
import { fetchMovie, fetchRecommendations } from "@/api/movies";
import { MovieCard } from "@/components/MovieCard";
import { useApp } from "@/contexts/AppContext";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

const MovieDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const movieId = Number(id);
  const { setProgress, movieStates } = useApp();

  const { data: movie } = useQuery({
    queryKey: ["movie", movieId],
    queryFn: () => fetchMovie(movieId),
    enabled: !!movieId,
  });

  const { data: recommendations } = useQuery({
    queryKey: ["movie", movieId, "recommendations"],
    queryFn: () => fetchRecommendations(movieId),
    enabled: !!movieId,
  });

  useEffect(() => {
    if (movieId) {
      setProgress(movieId, movieStates[movieId]?.progress_percent ?? 10, "watching");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [movieId]);

  if (!movie) return null;

  const state = movieStates[movieId];

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <img
              src={movie.image_url}
              alt={movie.title}
              className="w-full h-[360px] object-cover rounded-xl shadow-lg"
            />
            <div className="flex items-center gap-3">
              <Button size="lg" className="gap-2" onClick={() => navigate(`/watch/${movie.id}`)}>
                <Play className="w-4 h-4" />
                Play
              </Button>
              <Button
                size="lg"
                variant="secondary"
                className="gap-2"
                onClick={() => setProgress(movieId, 50, "watching")}
              >
                <Clock className="w-4 h-4" />
                Resume
              </Button>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">
                {movie.year} • {movie.duration_minutes} min • {movie.genre.join(", ")}
              </p>
              <h1 className="text-3xl font-bold mt-2">{movie.title}</h1>
              <p className="mt-3 text-muted-foreground">{movie.description}</p>
            </div>
            {state && (
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold">Progress</p>
                  <span className="text-sm text-muted-foreground">{state.progress_percent}%</span>
                </div>
                <Progress value={state.progress_percent} />
                <p className="text-xs text-muted-foreground mt-2">
                  Status: {state.status === "watching" ? "Currently watching" : "Watched"}
                </p>
              </div>
            )}
          </div>
          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Details</h3>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Rating: {movie.rating}</p>
              <p>Match: {movie.match_score}%</p>
              {movie.rank && <p>Rank: #{movie.rank}</p>}
            </div>
          </div>
        </div>

        {recommendations && recommendations.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Recommended</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {recommendations.map((rec, index) => (
                <MovieCard key={rec.id} movie={rec} index={index} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MovieDetail;

