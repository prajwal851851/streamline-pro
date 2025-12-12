import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Movie, movies } from "@/data/mockData";

interface AppState {
  theme: "dark" | "light";
  language: string;
  subtitles: string;
  favorites: Movie[];
  watchHistory: Movie[];
  downloads: Movie[];
  myList: Movie[];
}

interface AppContextType extends AppState {
  toggleTheme: () => void;
  setLanguage: (lang: string) => void;
  setSubtitles: (lang: string) => void;
  addToFavorites: (movie: Movie) => void;
  removeFromFavorites: (movieId: string) => void;
  isFavorite: (movieId: string) => boolean;
  addToHistory: (movie: Movie) => void;
  addToDownloads: (movie: Movie) => void;
  removeFromDownloads: (movieId: string) => void;
  isDownloaded: (movieId: string) => boolean;
  addToMyList: (movie: Movie) => void;
  removeFromMyList: (movieId: string) => void;
  isInMyList: (movieId: string) => boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(() => {
    const saved = localStorage.getItem("streamflix-state");
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      theme: "dark",
      language: "en",
      subtitles: "off",
      favorites: [],
      watchHistory: movies.slice(0, 3),
      downloads: [],
      myList: [],
    };
  });

  useEffect(() => {
    localStorage.setItem("streamflix-state", JSON.stringify(state));
    document.documentElement.classList.toggle("light", state.theme === "light");
    document.documentElement.classList.toggle("dark", state.theme === "dark");
  }, [state]);

  const toggleTheme = () => {
    setState((prev) => ({ ...prev, theme: prev.theme === "dark" ? "light" : "dark" }));
  };

  const setLanguage = (language: string) => {
    setState((prev) => ({ ...prev, language }));
  };

  const setSubtitles = (subtitles: string) => {
    setState((prev) => ({ ...prev, subtitles }));
  };

  const addToFavorites = (movie: Movie) => {
    setState((prev) => ({
      ...prev,
      favorites: prev.favorites.some((m) => m.id === movie.id)
        ? prev.favorites
        : [...prev.favorites, movie],
    }));
  };

  const removeFromFavorites = (movieId: string) => {
    setState((prev) => ({
      ...prev,
      favorites: prev.favorites.filter((m) => m.id !== movieId),
    }));
  };

  const isFavorite = (movieId: string) => state.favorites.some((m) => m.id === movieId);

  const addToHistory = (movie: Movie) => {
    setState((prev) => ({
      ...prev,
      watchHistory: [movie, ...prev.watchHistory.filter((m) => m.id !== movie.id)].slice(0, 20),
    }));
  };

  const addToDownloads = (movie: Movie) => {
    setState((prev) => ({
      ...prev,
      downloads: prev.downloads.some((m) => m.id === movie.id)
        ? prev.downloads
        : [...prev.downloads, movie],
    }));
  };

  const removeFromDownloads = (movieId: string) => {
    setState((prev) => ({
      ...prev,
      downloads: prev.downloads.filter((m) => m.id !== movieId),
    }));
  };

  const isDownloaded = (movieId: string) => state.downloads.some((m) => m.id === movieId);

  const addToMyList = (movie: Movie) => {
    setState((prev) => ({
      ...prev,
      myList: prev.myList.some((m) => m.id === movie.id)
        ? prev.myList
        : [...prev.myList, movie],
    }));
  };

  const removeFromMyList = (movieId: string) => {
    setState((prev) => ({
      ...prev,
      myList: prev.myList.filter((m) => m.id !== movieId),
    }));
  };

  const isInMyList = (movieId: string) => state.myList.some((m) => m.id === movieId);

  return (
    <AppContext.Provider
      value={{
        ...state,
        toggleTheme,
        setLanguage,
        setSubtitles,
        addToFavorites,
        removeFromFavorites,
        isFavorite,
        addToHistory,
        addToDownloads,
        removeFromDownloads,
        isDownloaded,
        addToMyList,
        removeFromMyList,
        isInMyList,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
}
