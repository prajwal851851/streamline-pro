import { useEffect, useMemo, useState } from "react";
import { Search as SearchIcon, X } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { MovieCard } from "@/components/MovieCard";
import { useApp } from "@/contexts/AppContext";

const genres = ["All", "Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance", "Documentary", "Animation"];

const Search = () => {
  const { movies } = useApp();
  const [queryParams, setQueryParams] = useSearchParams();
  const initialCategory = queryParams.get("category") || "All";
  const [query, setQuery] = useState("");
  const [selectedGenre, setSelectedGenre] = useState(initialCategory);

  useEffect(() => {
    const category = queryParams.get("category");
    if (category) setSelectedGenre(category);
  }, [queryParams]);

  const filteredMovies = useMemo(() => {
    return movies.filter((movie) => {
      const matchesQuery = movie.title.toLowerCase().includes(query.toLowerCase()) ||
        movie.genre.some((g) => g.toLowerCase().includes(query.toLowerCase()));
      const matchesGenre = selectedGenre === "All" || movie.genre.includes(selectedGenre);
      return matchesQuery && matchesGenre;
    });
  }, [query, selectedGenre]);

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <h1 className="text-3xl font-bold mb-8">Search</h1>

        {/* Search Input */}
        <div className="relative mb-6">
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search movies, TV shows, genres..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-12 pr-12 py-6 text-lg bg-card"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-4 top-1/2 -translate-y-1/2"
            >
              <X className="w-5 h-5 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>

        {/* Genre Filters */}
        <div className="flex flex-wrap gap-2 mb-8">
          {genres.map((genre) => (
            <button
              key={genre}
              onClick={() => {
                setSelectedGenre(genre);
                if (genre === "All") {
                  queryParams.delete("category");
                  setQueryParams(queryParams, { replace: true });
                } else {
                  setQueryParams({ category: genre }, { replace: true });
                }
              }}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                selectedGenre === genre
                  ? "bg-primary text-primary-foreground"
                  : "bg-card hover:bg-secondary"
              }`}
            >
              {genre}
            </button>
          ))}
        </div>

        {/* Results */}
        {query || selectedGenre !== "All" ? (
          <>
            <p className="text-muted-foreground mb-4">
              {filteredMovies.length} result{filteredMovies.length !== 1 ? "s" : ""} found
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {filteredMovies.map((movie, index) => (
                <MovieCard key={movie.id} movie={movie} index={index} />
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <SearchIcon className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">Start searching</h2>
            <p className="text-muted-foreground">
              Find your favorite movies and TV shows
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
