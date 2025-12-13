export interface UserMovieState {
  id: number;
  status: "watching" | "watched";
  progress_percent: number;
  position_seconds: number;
  in_my_list: boolean;
  is_favorite: boolean;
  is_downloaded: boolean;
  last_watched_at: string;
}

export interface Movie {
  id: number;
  title: string;
  description: string;
  year: number;
  duration_minutes: number;
  rating: string;
  genre: string[];
  image_url: string;
  video_url: string;
  match_score: number;
  is_new: boolean;
  is_trending: boolean;
  rank?: number | null;
  user_state?: UserMovieState | null;
}

export interface StreamingLink {
  id: number;
  quality: string;
  language: string;
  source_url: string;
  is_active: boolean;
  last_checked: string | null;
}

export interface StreamingMovie {
  id: number;
  imdb_id: string;
  title: string;
  year: number | null;
  type: string;
  poster_url: string | null;
  synopsis: string | null;
  created_at: string;
  updated_at: string;
  links: StreamingLink[];
}

