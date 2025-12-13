import { Heart } from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { MovieCard } from "@/components/MovieCard";

const Favorites = () => {
  const { favorites, movies } = useApp();

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Heart className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">My Favorites</h1>
        </div>

        {favorites.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {favorites.map((movie, index) => (
              <MovieCard key={movie.id} movie={movie} index={index} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Heart className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No favorites yet</h2>
            <p className="text-muted-foreground mb-6">
              Start adding movies and shows to your favorites!
            </p>
            <div className="mt-8">
              <h3 className="text-lg font-medium mb-4">Suggested for you</h3>
              {movies.length > 0 && (
                <div className="flex flex-wrap justify-center gap-4">
                  {movies.slice(0, 4).map((movie, index) => (
                    <MovieCard key={movie.id} movie={movie} index={index} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Favorites;
