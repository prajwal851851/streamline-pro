export function navigateToMovie(movieId: number, isStreaming: boolean, navigate: any) {
  if (isStreaming) {
    navigate(`/watch/${movieId}`);
  } else {
    navigate(`/movies/${movieId}`);
  }
}