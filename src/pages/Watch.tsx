import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMovie } from "@/api/movies";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

const Watch = () => {
  const { id } = useParams<{ id: string }>();
  const movieId = Number(id);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const { movieStates, setProgress } = useApp();
  const [localProgress, setLocalProgress] = useState(0);

  const { data: movie } = useQuery({
    queryKey: ["movie", movieId],
    queryFn: () => fetchMovie(movieId),
    enabled: !!movieId,
  });

  useEffect(() => {
    const state = movieStates[movieId];
    if (state && videoRef.current) {
      const duration = videoRef.current.duration || movie?.duration_minutes * 60 || 0;
      if (duration && state.position_seconds) {
        videoRef.current.currentTime = state.position_seconds;
      }
    }
  }, [movieId, movieStates, movie]);

  if (!movie) return null;

  const onTimeUpdate = () => {
    const video = videoRef.current;
    if (!video) return;
    const pct = Math.min(100, (video.currentTime / (video.duration || 1)) * 100);
    setLocalProgress(pct);
  };

  const persistProgress = (status?: "watching" | "watched") => {
    const video = videoRef.current;
    if (!video) return;
    const pct = Math.min(100, (video.currentTime / (video.duration || 1)) * 100);
    const seconds = Math.floor(video.currentTime);
    setProgress(movieId, Math.round(pct), status || (pct >= 95 ? "watched" : "watching")).catch(() => {});
    // store seconds too
    // we reuse setProgress only supports percent; position is stored in state via upsertState (not implemented)
  };

  return (
    <div className="min-h-screen bg-black text-white pt-16">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-4">
        <div className="relative aspect-video bg-black rounded-lg overflow-hidden shadow-2xl">
          <video
            ref={videoRef}
            className="w-full h-full"
            controls
            src={movie.video_url}
            poster={movie.image_url}
            onTimeUpdate={onTimeUpdate}
            onPause={() => persistProgress()}
            onEnded={() => persistProgress("watched")}
          />
        </div>
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{movie.title}</h1>
            <p className="text-sm text-muted-foreground">
              {movie.year} • {movie.duration_minutes} min • {movie.genre.join(", ")}
            </p>
          </div>
          <Button variant="secondary" onClick={() => persistProgress()}>
            Save Progress
          </Button>
        </div>
        <div className="space-y-1">
          <Progress value={localProgress || movieStates[movieId]?.progress_percent || 0} />
          <p className="text-xs text-muted-foreground">
            {Math.round(localProgress || movieStates[movieId]?.progress_percent || 0)}% watched
          </p>
        </div>
        <p className="text-sm text-muted-foreground">{movie.description}</p>
      </div>
    </div>
  );
};

export default Watch;

