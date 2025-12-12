import { TrendingUp } from "lucide-react";
import { movies } from "@/data/mockData";
import { MovieCard } from "@/components/MovieCard";

const Trending = () => {
  const trendingMovies = movies.filter((m) => m.isTrending);

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <TrendingUp className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">Trending Now</h1>
        </div>

        {/* Top 10 Section */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold mb-4">Top 10 Today</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {movies.slice(0, 5).map((movie, index) => (
              <div key={movie.id} className="relative animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                <span className="absolute -left-4 bottom-0 text-8xl font-bold text-foreground/10 z-10">
                  {index + 1}
                </span>
                <MovieCard movie={movie} index={index} />
              </div>
            ))}
          </div>
        </div>

        {/* All Trending */}
        <h2 className="text-xl font-semibold mb-4">All Trending</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {[...trendingMovies, ...movies].map((movie, index) => (
            <MovieCard key={`${movie.id}-${index}`} movie={movie} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Trending;
