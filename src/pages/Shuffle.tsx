import { useState } from "react";
import { Shuffle as ShuffleIcon, RefreshCw, Play } from "lucide-react";
import { movies } from "@/data/mockData";
import { Button } from "@/components/ui/button";
import { useApp } from "@/contexts/AppContext";
import { toast } from "@/hooks/use-toast";

const Shuffle = () => {
  const [currentMovie, setCurrentMovie] = useState(movies[Math.floor(Math.random() * movies.length)]);
  const [isShuffling, setIsShuffling] = useState(false);
  const { addToHistory } = useApp();

  const shuffle = () => {
    setIsShuffling(true);
    let count = 0;
    const interval = setInterval(() => {
      setCurrentMovie(movies[Math.floor(Math.random() * movies.length)]);
      count++;
      if (count >= 10) {
        clearInterval(interval);
        setIsShuffling(false);
      }
    }, 100);
  };

  const handlePlay = () => {
    addToHistory(currentMovie);
    toast({ title: "Now Playing", description: currentMovie.title });
  };

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-4xl mx-auto text-center animate-fade-in">
        <div className="flex items-center justify-center gap-3 mb-8">
          <ShuffleIcon className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">Random Pick</h1>
        </div>

        <p className="text-muted-foreground mb-8">
          Can't decide what to watch? Let us pick for you!
        </p>

        {/* Selected Movie */}
        <div className="relative max-w-sm mx-auto mb-8">
          <div
            className={`aspect-[2/3] rounded-xl overflow-hidden shadow-2xl transition-all duration-300 ${
              isShuffling ? "animate-pulse scale-95" : "scale-100"
            }`}
          >
            <img
              src={currentMovie.image}
              alt={currentMovie.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-6 text-left">
              <h2 className="text-2xl font-bold mb-2">{currentMovie.title}</h2>
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                <span className="text-green-500 font-semibold">{currentMovie.match}% Match</span>
                <span>{currentMovie.year}</span>
                <span>{currentMovie.duration}</span>
                <span className="px-1.5 py-0.5 bg-secondary rounded text-xs">
                  {currentMovie.rating}
                </span>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {currentMovie.description}
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-center gap-4">
          <Button
            onClick={shuffle}
            disabled={isShuffling}
            variant="secondary"
            size="lg"
            className="gap-2"
          >
            <RefreshCw className={`w-5 h-5 ${isShuffling ? "animate-spin" : ""}`} />
            Shuffle Again
          </Button>
          <Button onClick={handlePlay} size="lg" className="gap-2">
            <Play className="w-5 h-5 fill-current" />
            Watch Now
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Shuffle;
