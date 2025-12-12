import { Users, Star } from "lucide-react";
import { movies } from "@/data/mockData";
import { MovieCard } from "@/components/MovieCard";

const Kids = () => {
  const kidsMovies = movies.filter((m) => m.rating === "G" || m.rating === "PG-13");

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Users className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">Kids</h1>
        </div>

        {/* Featured Kids Banner */}
        <div className="relative rounded-2xl overflow-hidden mb-8 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 p-8 animate-fade-in">
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-5 h-5 text-yellow-300 fill-yellow-300" />
              <span className="text-sm font-medium text-primary-foreground">Kid-Friendly Content</span>
            </div>
            <h2 className="text-2xl font-bold text-primary-foreground mb-2">Safe for All Ages</h2>
            <p className="text-primary-foreground/80 max-w-md">
              Explore our collection of family-friendly movies and shows perfect for kids of all ages.
            </p>
          </div>
          <div className="absolute right-8 top-1/2 -translate-y-1/2 text-6xl">🎬 🍿 ⭐</div>
        </div>

        {/* Kids Content */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {[...kidsMovies, ...kidsMovies, ...kidsMovies].map((movie, index) => (
            <MovieCard key={`${movie.id}-${index}`} movie={movie} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Kids;
