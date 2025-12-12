import { useState, useEffect } from "react";
import { Search, Bell, Cast } from "lucide-react";
import { ProfileDropdown } from "./ProfileDropdown";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 right-0 left-0 z-40 h-16 flex items-center justify-end px-6 transition-all duration-300",
        scrolled ? "bg-background/95 backdrop-blur-md shadow-lg" : "bg-gradient-to-b from-background/80 to-transparent"
      )}
      style={{ marginLeft: "var(--sidebar-width, 224px)" }}
    >
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative">
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="p-2 rounded-full hover:bg-secondary transition-colors"
          >
            <Search className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
          </button>
          <div
            className={cn(
              "absolute right-0 top-full mt-2 transition-all duration-300 origin-top-right",
              searchOpen ? "opacity-100 scale-100" : "opacity-0 scale-95 pointer-events-none"
            )}
          >
            <Input
              type="search"
              placeholder="Search titles, genres..."
              className="w-72 bg-card border-border"
              autoFocus={searchOpen}
            />
          </div>
        </div>

        {/* Cast */}
        <button className="p-2 rounded-full hover:bg-secondary transition-colors">
          <Cast className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
        </button>

        {/* Notifications */}
        <button className="p-2 rounded-full hover:bg-secondary transition-colors relative">
          <Bell className="w-5 h-5 text-muted-foreground hover:text-foreground transition-colors" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full" />
        </button>

        {/* Profile */}
        <ProfileDropdown />
      </div>
    </header>
  );
}
