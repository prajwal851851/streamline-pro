import { Layers, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { categories } from "@/data/mockData";

const categoryColors = [
  "from-red-600 to-orange-600",
  "from-blue-600 to-cyan-600",
  "from-purple-600 to-pink-600",
  "from-green-600 to-emerald-600",
  "from-yellow-600 to-amber-600",
  "from-indigo-600 to-violet-600",
  "from-rose-600 to-red-600",
  "from-teal-600 to-green-600",
];

const Categories = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <Layers className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">Categories</h1>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((category, index) => (
            <button
              key={category.name}
              onClick={() => navigate(`/search?category=${encodeURIComponent(category.name)}`)}
              className={`relative h-32 rounded-lg bg-gradient-to-br ${categoryColors[index % categoryColors.length]} p-4 text-left group overflow-hidden transition-transform hover:scale-105 animate-fade-in`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <span className="text-lg font-semibold text-primary-foreground">{category.name}</span>
              <span className="block text-sm text-primary-foreground/80 mt-1">
                {category.movies.length} titles
              </span>
              <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-6 h-6 text-primary-foreground/60 group-hover:translate-x-1 transition-transform" />
              <div className="absolute inset-0 bg-gradient-to-t from-background/20 to-transparent" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Categories;
