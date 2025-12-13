import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Play, Link2 } from "lucide-react";
import { fetchStreamingMovie } from "@/api/movies";
import { StreamingLink, StreamingMovie } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const StreamingDetail = () => {
  const { id } = useParams<{ id: string }>();
  const movieId = Number(id);

  const { data: movie, isLoading, isError } = useQuery<StreamingMovie>({
    queryKey: ["streaming-movie", movieId],
    queryFn: () => fetchStreamingMovie(movieId),
    enabled: !!movieId,
  });

  const [selectedLink, setSelectedLink] = useState<StreamingLink | null>(null);

  const links = useMemo(() => movie?.links || [], [movie]);

  const activeLink = selectedLink || links[0] || null;

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (isError || !movie) return <div className="p-6 text-destructive">Could not load streaming item.</div>;

  return (
    <div className="min-h-screen pt-20 px-6 pb-12">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-4">
            <div className="relative aspect-video bg-black rounded-xl overflow-hidden shadow-2xl border border-border/60">
              {activeLink ? (
                (() => {
                  const url = activeLink.source_url;
                  
                  // Check if URL is from 1flix.to (which blocks iframe embedding)
                  const is1FlixUrl = url.includes('1flix.to');
                  
                  // Check if URL is a direct video file
                  const isDirectVideo = url.match(/\.(mp4|m3u8|webm|ogg|mkv|avi|mov)$/i);
                  
                  // Check if URL is an embeddable iframe (not 1flix.to)
                  const isIframeEmbed = (url.includes('embed') || url.includes('player')) && !is1FlixUrl;
                  
                  if (is1FlixUrl) {
                    // 1flix.to blocks iframe embedding, so show a button to open in new tab
                    return (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-8">
                        <div className="text-center space-y-2">
                          <p className="text-lg text-white">This video cannot be embedded</p>
                          <p className="text-sm text-muted-foreground">
                            Click the button below to watch on the source website
                          </p>
                        </div>
                        <a
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          Watch on 1flix.to
                        </a>
                      </div>
                    );
                  } else if (isDirectVideo) {
                    // Direct video file - use video tag
                    return (
                      <video
                        key={activeLink.id}
                        controls
                        className="w-full h-full bg-black"
                        poster={movie.poster_url || undefined}
                        src={url}
                      />
                    );
                  } else if (isIframeEmbed) {
                    // Embeddable iframe (from other video hosts)
                    return (
                      <iframe
                        key={activeLink.id}
                        src={url}
                        className="w-full h-full bg-black"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                        title={movie.title}
                      />
                    );
                  } else {
                    // Unknown URL type - offer to open in new tab
                    return (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-4 p-8">
                        <div className="text-center space-y-2">
                          <p className="text-lg text-white">Stream Link Available</p>
                          <p className="text-sm text-muted-foreground">
                            Click the button below to open the stream
                          </p>
                        </div>
                        <a
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors inline-flex items-center gap-2"
                        >
                          <Play className="w-5 h-5" />
                          Open Stream
                        </a>
                      </div>
                    );
                  }
                })()
              ) : (
                <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                  No stream link available
                </div>
              )}
              <div className="absolute top-3 left-3 flex gap-2">
                {movie.year && <Badge variant="secondary">{movie.year}</Badge>}
                <Badge variant="secondary" className="capitalize">
                  {movie.type}
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button size="lg" className="gap-2" disabled={!activeLink}>
                <Play className="w-4 h-4" />
                {activeLink ? "Play" : "No link"}
              </Button>
              {activeLink && (
                <a
                  href={activeLink.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-primary underline inline-flex items-center gap-1"
                >
                  <Link2 className="w-4 h-4" />
                  Open Source URL
                </a>
              )}
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-bold">{movie.title}</h1>
              <p className="text-sm text-muted-foreground">{movie.synopsis || "No synopsis available."}</p>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Available Links</h3>
            <div className="space-y-2">
              {links.length === 0 && <p className="text-muted-foreground text-sm">No links found.</p>}
              {links.map((link) => {
                const isActive = activeLink?.id === link.id;
                return (
                  <button
                    key={link.id}
                    onClick={() => setSelectedLink(link)}
                    className={`w-full text-left border rounded-lg p-3 transition-colors ${
                      isActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/60"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{link.quality}</Badge>
                        <Badge variant="outline">{link.language}</Badge>
                      </div>
                      <span className="text-xs text-muted-foreground">{link.is_active ? "Active" : "Inactive"}</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground truncate">{link.source_url}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamingDetail;

