import { apiGet, apiPost, apiPatch } from "./client";
import { Movie, StreamingMovie, UserMovieState } from "@/types/api";

export async function fetchMovies(): Promise<Movie[]> {
  return apiGet<Movie[]>("/movies/");
}

export async function fetchMovie(id: string | number): Promise<Movie> {
  return apiGet<Movie>(`/movies/${id}/`);
}

export async function fetchRecommendations(id: string | number): Promise<Movie[]> {
  return apiGet<Movie[]>(`/movies/${id}/recommendations/`);
}

export async function upsertUserMovieState(payload: Partial<UserMovieState> & { movie_id: number }): Promise<UserMovieState> {
  return apiPost<UserMovieState>("/user-states/set_state/", payload);
}

export async function updateUserMovieState(id: number, payload: Partial<UserMovieState>): Promise<UserMovieState> {
  return apiPatch<UserMovieState>(`/user-states/${id}/`, payload);
}

export async function clearHistory(): Promise<{ detail: string; count: number }> {
  return apiPost("/user-states/clear_history/", {});
}

export async function fetchStreamingMovies(): Promise<StreamingMovie[]> {
  return apiGet<StreamingMovie[]>("/streaming/movies/");
}

export async function fetchStreamingMoviesByType(type: "movie" | "show"): Promise<StreamingMovie[]> {
  return apiGet<StreamingMovie[]>(`/streaming/movies/?type=${type}`);
}

export async function fetchStreamingMovie(id: string | number): Promise<StreamingMovie> {
  return apiGet<StreamingMovie>(`/streaming/movies/${id}/`);
}

export async function refreshStreamingMovieLinks(id: string | number): Promise<{ message: string; status: string }> {
  return apiPost<{ message: string; status: string }>(`/streaming/movies/${id}/refresh_links/`, {});
}

export async function validateStreamingLinks(id: string | number): Promise<StreamingMovie> {
  return apiGet<StreamingMovie>(`/streaming/movies/${id}/validate_links/`);
}