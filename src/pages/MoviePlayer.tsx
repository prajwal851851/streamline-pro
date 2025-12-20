import { useState, useEffect } from 'react';
import { Play, AlertCircle, RefreshCw, Loader2, CheckCircle, ArrowLeft } from 'lucide-react';
import Hls from 'hls.js';

// Mock API functions - replace with your actual API calls
const fetchStreamingMovie = async (id) => {
  // Replace with actual API call
  return fetch(`/api/streaming/movies/${id}/`).then(r => r.json());
};

const refreshStreamingMovieLinks = async (id) => {
  // Replace with actual API call
  return fetch(`/api/streaming/movies/${id}/refresh_links/`, { method: 'POST' }).then(r => r.json());
};

export default function MoviePlayer() {

  // Get movie ID from URL or props
  const movieId = window.location.pathname.split('/').pop() || '1';
  
  const [movie, setMovie] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLink, setSelectedLink] = useState(null);
  const [iframeError, setIframeError] = useState(false);
  const [isLoadingVideo, setIsLoadingVideo] = useState(true);

  const [pollCount, setPollCount] = useState(0);

  // Poll for updated links when refreshing
  useEffect(() => {
    if (refreshing && pollCount < 20) {
      const timer = setTimeout(() => {
        loadMovie(true);
        setPollCount(prev => prev + 1);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [refreshing, pollCount]);

  useEffect(() => {
    loadMovie();
  }, [movieId]);

  useEffect(() => {
    setIframeError(false);
    setIsLoadingVideo(true);
  }, [selectedLink?.id]);

  const handleRefreshLinks = async () => {
    try {
      setRefreshing(true);
      setPollCount(0);
      await refreshStreamingMovieLinks(movieId);
      // Start polling for results
      setTimeout(() => loadMovie(true), 3000);
    } catch (err) {
      setError('Failed to refresh links');
      setRefreshing(false);
    }
  };

  const loadMovie = async (isPolling = false) => {
    try {
      if (!isPolling) setLoading(true);
      const data = await fetchStreamingMovie(movieId);
      setMovie(data);
      
      // Check if we have valid links
      const validLinks = data.links?.filter(link => link.is_active) || [];
      
      if (validLinks.length > 0) {
        setSelectedLink(validLinks[0]);
        setRefreshing(false);
        setPollCount(0);
      } else if (data._refreshing) {
        // Links are being fetched, continue polling
        setRefreshing(true);
      } else {
        // No links and not refreshing - might need manual refresh
        setRefreshing(false);
      }
      
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load movie');
      setRefreshing(false);
    } finally {
      if (!isPolling) setLoading(false);
    }
  };

  const validLinks = movie?.links?.filter(link => link.is_active) || [];
  const activeLink = selectedLink;

  useEffect(() => {
    const url = activeLink?.source_url;
    if (!url) return;

    const isDirectVideo = /\.(mp4|webm|ogg|mkv|avi|mov)(\?|$)/i.test(url);
    const isHlsStream = /\.m3u8(\?|$)/i.test(url);
    if (isDirectVideo || isHlsStream) return;

    const timeout = setTimeout(() => {
      if (isLoadingVideo) {
        setIframeError(true);
        setIsLoadingVideo(false);
      }
    }, 15000);

    return () => clearTimeout(timeout);
  }, [activeLink?.id, isLoadingVideo]);

  useEffect(() => {
    const url = activeLink?.source_url;
    const videoEl: HTMLVideoElement | null = (document.getElementById('streamline-video') as HTMLVideoElement) || null;
    if (!url || !videoEl) return;

    const isHlsStream = /\.m3u8(\?|$)/i.test(url);
    if (!isHlsStream) return;

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(videoEl);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoadingVideo(false);
      });
      hls.on(Hls.Events.ERROR, () => {
        setIsLoadingVideo(false);
        setIframeError(true);
      });
      return () => {
        try {
          hls.destroy();
        } catch {
        }
      };
    }

    if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
      videoEl.src = url;
    }
  }, [activeLink?.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading movie...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div className="max-w-lg w-full border border-destructive rounded-lg p-6 bg-destructive/10">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-destructive mb-2">Error</h3>
              <p className="text-sm text-muted-foreground mb-4">{error}</p>
              <button
                onClick={() => window.history.back()}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <button
          onClick={() => window.history.back()}
          className="flex items-center gap-2 text-foreground hover:text-primary transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back</span>
        </button>
      </div>

      <div className="container mx-auto p-4 max-w-7xl">
        {/* Movie Info */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">{movie?.title}</h1>
          <div className="flex gap-4 text-sm text-muted-foreground">
            {movie?.year && <span>{movie.year}</span>}
            {movie?.type && <span className="capitalize">{movie.type}</span>}
          </div>
          {movie?.synopsis && (
            <p className="mt-4 text-muted-foreground max-w-3xl">
              {movie.synopsis}
            </p>
          )}
        </div>

        {/* Video Player or Status */}
        <div className="aspect-video bg-black rounded-lg overflow-hidden mb-6 relative">

          {refreshing ? (
            <div className="w-full h-full flex flex-col items-center justify-center text-white">
              <Loader2 className="w-16 h-16 animate-spin mb-4 text-primary" />
              <p className="text-xl mb-2">Finding streaming links...</p>
              <p className="text-sm text-gray-400">
                This may take 15-30 seconds
              </p>
              <div className="mt-4 flex gap-2">
                {[...Array(Math.min(pollCount, 10))].map((_, i) => (
                  <div
                    key={i}
                    className="w-2 h-2 rounded-full bg-primary animate-pulse"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                ))}
              </div>
            </div>
          ) : selectedLink ? (
            (() => {
              const url = selectedLink.source_url;
              const is1FlixUrl = url.includes('1flix.to');
              const isHlsStream = /\.m3u8(\?|$)/i.test(url);
              const isDirectVideo = url.match(/\.(mp4|webm|ogg|mkv|avi|mov)(\?|$)/i);
              const isIframeEmbed = (url.includes('embed') || url.includes('player')) && !is1FlixUrl;

              if (is1FlixUrl) {
                return (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-8">
                    <div className="text-center space-y-2">
                      <p className="text-lg text-white">This video cannot be embedded</p>
                      <p className="text-sm text-gray-400">Open it on the source website</p>
                    </div>
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                    >
                      <Play className="w-5 h-5" />
                      Open Source
                    </a>
                  </div>
                );
              }

              if (isDirectVideo || isHlsStream) {
                return (
                  <div className="relative w-full h-full">
                    {isLoadingVideo && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                        <div className="text-center space-y-2">
                          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
                          <p className="text-sm text-gray-400">Loading video...</p>
                        </div>
                      </div>
                    )}
                    <video
                      id="streamline-video"
                      controls
                      className="w-full h-full bg-black"
                      src={isHlsStream ? undefined : url}
                      onLoadedData={() => setIsLoadingVideo(false)}
                      onError={() => {
                        setIsLoadingVideo(false);
                        setIframeError(true);
                      }}
                    />
                  </div>
                );
              }

              if (iframeError) {
                return (
                  <div className="w-full h-full flex flex-col items-center justify-center text-white gap-3 p-6">
                    <AlertCircle className="w-16 h-16 text-yellow-500" />
                    <p className="text-xl">Unable to load stream</p>
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                    >
                      Open in New Tab
                    </a>
                  </div>
                );
              }

              if (isIframeEmbed || true) {
                return (
                  <iframe
                    src={url}
                    className="w-full h-full border-0"
                    allowFullScreen
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    onLoad={() => {
                      setIsLoadingVideo(false);
                      setIframeError(false);
                    }}
                    onError={() => {
                      setIsLoadingVideo(false);
                      setIframeError(true);
                    }}
                  />
                );
              }
            })()
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-white">
              <AlertCircle className="w-16 h-16 mb-4 text-yellow-500" />
              <p className="text-xl mb-2">No streaming links available</p>
              <p className="text-sm text-gray-400 mb-4">
                Click below to search for available links
              </p>
              <button
                onClick={handleRefreshLinks}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Find Streaming Links
              </button>
            </div>
          )}
        </div>

        {/* Available Links */}
        {validLinks.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                Available Servers ({validLinks.length})
              </h2>
              <button
                onClick={handleRefreshLinks}
                disabled={refreshing}
                className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh Links
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {validLinks.map((link, index) => (
                <button
                  key={link.id || index}
                  onClick={() => setSelectedLink(link)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    selectedLink?.source_url === link.source_url
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">Server {index + 1}</span>
                    {selectedLink?.source_url === link.source_url && (
                      <CheckCircle className="w-4 h-4 text-primary" />
                    )}
                  </div>
                  <div className="flex gap-2 text-sm text-muted-foreground">
                    <span className="px-2 py-0.5 bg-secondary rounded text-xs">
                      {link.quality}
                    </span>
                    <span className="px-2 py-0.5 bg-secondary rounded text-xs">
                      {link.language}
                    </span>
                  </div>
                  {link.last_checked && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Checked: {new Date(link.last_checked).toLocaleString()}
                    </p>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Info Message */}
        {movie?._refreshing && (
          <div className="mt-4 border border-border rounded-lg p-4 bg-card">
            <div className="flex items-start gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold mb-1">Searching for links...</h3>
                <p className="text-sm text-muted-foreground">
                  We're currently finding fresh streaming links for this movie.
                  This page will update automatically.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}