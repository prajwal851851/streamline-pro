import { HeroSection } from "@/components/HeroSection";
import { MovieCarousel } from "@/components/MovieCarousel";
import { categories, movies } from "@/data/mockData";

const Index = () => {
  return (
    <div className="pb-12">
      <HeroSection />
      
      <div className="px-4 -mt-32 relative z-10 space-y-2">
        {categories.map((category) => (
          <MovieCarousel
            key={category.name}
            title={category.name}
            movies={category.movies.length > 0 ? category.movies : movies}
          />
        ))}
      </div>
    </div>
  );
};

export default Index;
