import movie1 from "@/assets/movies/movie-1.jpg";
import movie2 from "@/assets/movies/movie-2.jpg";
import movie3 from "@/assets/movies/movie-3.jpg";
import movie4 from "@/assets/movies/movie-4.jpg";
import movie5 from "@/assets/movies/movie-5.jpg";
import movie6 from "@/assets/movies/movie-6.jpg";
import heroFeatured from "@/assets/hero-featured.jpg";

export interface Movie {
  id: string;
  title: string;
  image: string;
  rating: string;
  year: number;
  duration: string;
  genre: string[];
  description: string;
  match?: number;
  isNew?: boolean;
  isTrending?: boolean;
}

export const movies: Movie[] = [
  {
    id: "1",
    title: "City Inferno",
    image: movie1,
    rating: "TV-MA",
    year: 2024,
    duration: "2h 15m",
    genre: ["Action", "Thriller"],
    description: "A city under siege faces its darkest hour as explosions rock the skyline.",
    match: 97,
    isTrending: true,
  },
  {
    id: "2",
    title: "Sunset Hearts",
    image: movie2,
    rating: "PG-13",
    year: 2024,
    duration: "1h 52m",
    genre: ["Romance", "Drama"],
    description: "Two souls find love against the backdrop of a beautiful sunset.",
    match: 94,
    isNew: true,
  },
  {
    id: "3",
    title: "Cosmic Drift",
    image: movie3,
    rating: "PG-13",
    year: 2024,
    duration: "2h 30m",
    genre: ["Sci-Fi", "Adventure"],
    description: "An astronaut lost in the cosmos discovers the true meaning of humanity.",
    match: 91,
    isTrending: true,
  },
  {
    id: "4",
    title: "Shadow Manor",
    image: movie4,
    rating: "R",
    year: 2024,
    duration: "1h 48m",
    genre: ["Horror", "Mystery"],
    description: "A haunted mansion holds secrets that refuse to stay buried.",
    match: 88,
    isNew: true,
  },
  {
    id: "5",
    title: "Family Fun",
    image: movie5,
    rating: "G",
    year: 2024,
    duration: "1h 35m",
    genre: ["Animation", "Comedy"],
    description: "A quirky family embarks on a hilarious adventure.",
    match: 95,
    isTrending: true,
  },
  {
    id: "6",
    title: "Dark Files",
    image: movie6,
    rating: "TV-MA",
    year: 2024,
    duration: "1h 45m",
    genre: ["Documentary", "Crime"],
    description: "Uncover the truth behind unsolved mysteries.",
    match: 89,
  },
];

export const featuredMovie = {
  id: "featured",
  title: "The Portal",
  image: heroFeatured,
  rating: "TV-14",
  year: 2024,
  duration: "2h 45m",
  genre: ["Sci-Fi", "Thriller"],
  description: "When a mysterious portal opens, humanity faces its greatest challenge. A group of unlikely heroes must venture into the unknown to save everything they love.",
  match: 98,
  rank: 1,
};

export const categories = [
  { name: "Trending Now", movies: movies.filter(m => m.isTrending) },
  { name: "New Releases", movies: movies.filter(m => m.isNew) },
  { name: "Popular on StreamFlix", movies: [...movies].reverse() },
  { name: "Action & Adventure", movies: movies.filter(m => m.genre.includes("Action") || m.genre.includes("Adventure")) },
  { name: "Comedies", movies: movies.filter(m => m.genre.includes("Comedy")) },
  { name: "Horror", movies: movies.filter(m => m.genre.includes("Horror")) },
  { name: "Documentaries", movies: movies.filter(m => m.genre.includes("Documentary")) },
  { name: "Romantic Movies", movies: movies.filter(m => m.genre.includes("Romance")) },
];

export const languages = [
  { code: "en", name: "English" },
  { code: "es", name: "Español" },
  { code: "fr", name: "Français" },
  { code: "de", name: "Deutsch" },
  { code: "ja", name: "日本語" },
  { code: "ko", name: "한국어" },
  { code: "zh", name: "中文" },
  { code: "hi", name: "हिन्दी" },
];

export const subtitleLanguages = [
  { code: "off", name: "Off" },
  ...languages,
];
