import { Tv } from "lucide-react";
import { MovieCard } from "@/components/MovieCard";
import { useApp } from "@/contexts/AppContext";

const TvShows = () => {
  const { movies } = useApp();
  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Tv className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">TV Shows</h1>
        </div>

        {movies.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {[...movies].reverse().map((movie, index) => (
              <MovieCard key={`${movie.id}-${index}`} movie={movie} index={index} />
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No shows available.</p>
        )}
      </div>
    </div>
  );
};

export default TvShows;
