import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo } from "react";
import { clearHistory, fetchMovies, upsertUserMovieState, updateUserMovieState } from "@/api/movies";
import { Movie, UserMovieState } from "@/types/api";

interface AppState {
  theme: "dark" | "light";
  language: string;
  subtitles: string;
  movies: Movie[];
  movieStates: Record<number, UserMovieState>;
  loading: boolean;
}

interface AppContextType extends AppState {
  toggleTheme: () => void;
  setLanguage: (lang: string) => void;
  setSubtitles: (lang: string) => void;
  refreshMovies: () => Promise<void>;
  addToFavorites: (movieId: number) => Promise<void>;  // Fixed: Takes movieId, not Movie object
  removeFromFavorites: (movieId: number) => Promise<void>;
  isFavorite: (movieId: number) => boolean;
  addToHistory: (movieId: number) => Promise<void>;
  addToDownloads: (movieId: number) => Promise<void>;
  removeFromDownloads: (movieId: number) => Promise<void>;
  isDownloaded: (movieId: number) => boolean;
  addToMyList: (movieId: number) => Promise<void>;
  removeFromMyList: (movieId: number) => Promise<void>;
  isInMyList: (movieId: number) => boolean;
  setProgress: (movieId: number, progress: number, status?: UserMovieState["status"]) => Promise<void>;
  clearHistory: () => Promise<void>;
  favorites: Movie[];
  watchHistory: Movie[];
  downloads: Movie[];
  myList: Movie[];
}

const THEME_KEY = "streamflix-theme";
const LANGUAGE_KEY = "streamflix-language";
const SUBTITLE_KEY = "streamflix-subtitle";

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children, authToken }: { children: ReactNode; authToken?: string }) {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [movieStates, setMovieStates] = useState<Record<number, UserMovieState>>({});
  const [theme, setTheme] = useState<"dark" | "light">(
    (localStorage.getItem(THEME_KEY) as "dark" | "light") || "dark"
  );
  const [language, setLanguageState] = useState<string>(localStorage.getItem(LANGUAGE_KEY) || "en");
  const [subtitles, setSubtitlesState] = useState<string>(localStorage.getItem(SUBTITLE_KEY) || "off");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("light", theme === "light");
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => localStorage.setItem(LANGUAGE_KEY, language), [language]);
  useEffect(() => localStorage.setItem(SUBTITLE_KEY, subtitles), [subtitles]);

  const refreshMovies = async () => {
    setLoading(true);
    try {
      const data = await fetchMovies();
      setMovies(data);
      const stateMap: Record<number, UserMovieState> = {};
      data.forEach((movie) => {
        if (movie.user_state) stateMap[movie.id] = movie.user_state;
      });
      setMovieStates(stateMap);
    } catch (error) {
      console.error("Failed to fetch movies", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken === undefined) {
      refreshMovies();
    } else if (authToken) {
      refreshMovies();
    }
  }, [authToken]);

  const toggleTheme = () => setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  const setLanguage = (lang: string) => setLanguageState(lang);
  const setSubtitles = (lang: string) => setSubtitlesState(lang);

  const upsertState = async (movieId: number, partial: Partial<UserMovieState>) => {
    const existing = movieStates[movieId];
    const updated = existing
      ? await updateUserMovieState(existing.id, partial)
      : await upsertUserMovieState({ movie_id: movieId, ...partial });
    setMovieStates((prev) => ({ ...prev, [movieId]: updated }));
    setMovies((prev) =>
      prev.map((m) => (m.id === movieId ? { ...m, user_state: updated } : m))
    );
  };

  const addToFavorites = (movieId: number) => upsertState(movieId, { is_favorite: true });
  const removeFromFavorites = (movieId: number) => upsertState(movieId, { is_favorite: false });
  const isFavorite = (movieId: number) => !!movieStates[movieId]?.is_favorite;

  const addToHistory = (movieId: number) =>
    upsertState(movieId, { status: "watching", progress_percent: Math.max(10, movieStates[movieId]?.progress_percent ?? 0) });

  const addToDownloads = (movieId: number) => upsertState(movieId, { is_downloaded: true });
  const removeFromDownloads = (movieId: number) => upsertState(movieId, { is_downloaded: false });
  const isDownloaded = (movieId: number) => !!movieStates[movieId]?.is_downloaded;

  const addToMyList = (movieId: number) => upsertState(movieId, { in_my_list: true });
  const removeFromMyList = (movieId: number) => upsertState(movieId, { in_my_list: false });
  const isInMyList = (movieId: number) => !!movieStates[movieId]?.in_my_list;

  const setProgress = (movieId: number, progress: number, status?: UserMovieState["status"]) =>
    upsertState(movieId, {
      progress_percent: progress,
      status: status ?? (progress >= 95 ? "watched" : "watching"),
    });

  const clearHistoryHandler = async () => {
    await clearHistory();
    setMovieStates((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        const id = Number(key);
        const state = next[id];
        if (!state) return;
        next[id] = {
          ...state,
          status: null,
          progress_percent: 0,
          position_seconds: 0,
        };
      });
      return next;
    });
    setMovies((prev) =>
      prev.map((m) =>
        m.user_state
          ? {
              ...m,
              user_state: {
                ...m.user_state,
                status: null,
                progress_percent: 0,
                position_seconds: 0,
              },
            }
          : m
      )
    );
  };

  const favorites = useMemo(
    () => movies.filter((m) => movieStates[m.id]?.is_favorite),
    [movies, movieStates]
  );
  const watchHistory = useMemo(
    () =>
      movies
        .filter((m) => {
          const s = movieStates[m.id];
          return s && ((s.progress_percent ?? 0) > 0 || s.status);
        })
        .sort(
          (a, b) =>
            new Date(movieStates[b.id]?.last_watched_at ?? 0).getTime() -
            new Date(movieStates[a.id]?.last_watched_at ?? 0).getTime()
        ),
    [movies, movieStates]
  );
  const downloads = useMemo(
    () => movies.filter((m) => movieStates[m.id]?.is_downloaded),
    [movies, movieStates]
  );
  const myList = useMemo(
    () => movies.filter((m) => movieStates[m.id]?.in_my_list),
    [movies, movieStates]
  );

  return (
    <AppContext.Provider
      value={{
        theme,
        language,
        subtitles,
        movies,
        movieStates,
        loading,
        toggleTheme,
        setLanguage,
        setSubtitles,
        refreshMovies,
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
        setProgress,
        clearHistory: clearHistoryHandler,
        favorites,
        watchHistory,
        downloads,
        myList,
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