import { useState } from "react";
import { NavLink } from "@/components/NavLink";
import {
  Search,
  Home,
  Film,
  Tv,
  Shuffle,
  TrendingUp,
  Layers,
  Users,
  PlayCircle,
  Plus,
  Clock,
  Heart,
  Download,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const mainNavItems = [
  { icon: Search, label: "Search", path: "/search" },
  { icon: Home, label: "Home", path: "/" },
  { icon: Film, label: "Movies", path: "/movies" },
  { icon: PlayCircle, label: "Streaming", path: "/streaming" },
  { icon: Tv, label: "TV Shows", path: "/tv-shows" },
  { icon: Shuffle, label: "Shuffle", path: "/shuffle" },
  { icon: TrendingUp, label: "Trending", path: "/trending" },
  { icon: Layers, label: "Categories", path: "/categories" },
  { icon: Users, label: "For Kids", path: "/kids" },
];

const libraryItems = [
  { icon: Plus, label: "My List", path: "/my-list" },
  { icon: Clock, label: "History", path: "/history" },
  { icon: Heart, label: "Favorites", path: "/favorites" },
  { icon: Download, label: "Downloads", path: "/downloads" },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-full bg-sidebar z-50 flex flex-col transition-all duration-300 ease-out border-r border-sidebar-border",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 gap-3">
        <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg">
          S
        </div>
        <span
          className={cn(
            "font-bold text-lg text-foreground transition-opacity duration-200",
            collapsed ? "opacity-0 w-0" : "opacity-100"
          )}
        >
          StreamFlix
        </span>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto scrollbar-hide">
        <div className="space-y-1 px-2">
          {mainNavItems.map((item) => (
            <Tooltip key={item.path} delayDuration={0}>
              <TooltipTrigger asChild>
                <NavLink
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent transition-all duration-200 group"
                  )}
                  activeClassName="bg-sidebar-accent text-foreground"
                >
                  <item.icon className="w-5 h-5 shrink-0 group-hover:scale-110 transition-transform" />
                  <span
                    className={cn(
                      "text-sm font-medium transition-all duration-200",
                      collapsed ? "opacity-0 w-0 overflow-hidden" : "opacity-100"
                    )}
                  >
                    {item.label}
                  </span>
                </NavLink>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right" sideOffset={10}>
                  {item.label}
                </TooltipContent>
              )}
            </Tooltip>
          ))}
        </div>

        {/* Divider */}
        <div className="my-4 mx-4 border-t border-sidebar-border" />

        {/* Library */}
        <div className="space-y-1 px-2">
          {!collapsed && (
            <span className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              My Library
            </span>
          )}
          {libraryItems.map((item) => (
            <Tooltip key={item.path} delayDuration={0}>
              <TooltipTrigger asChild>
                <NavLink
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent transition-all duration-200 group"
                  )}
                  activeClassName="bg-sidebar-accent text-foreground"
                >
                  <item.icon className="w-5 h-5 shrink-0 group-hover:scale-110 transition-transform" />
                  <span
                    className={cn(
                      "text-sm font-medium transition-all duration-200",
                      collapsed ? "opacity-0 w-0 overflow-hidden" : "opacity-100"
                    )}
                  >
                    {item.label}
                  </span>
                </NavLink>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right" sideOffset={10}>
                  {item.label}
                </TooltipContent>
              )}
            </Tooltip>
          ))}
        </div>
      </nav>

      {/* Settings & Collapse */}
      <div className="p-2 border-t border-sidebar-border">
        <Tooltip delayDuration={0}>
          <TooltipTrigger asChild>
            <NavLink
              to="/settings"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent transition-all duration-200"
              activeClassName="bg-sidebar-accent text-foreground"
            >
              <Settings className="w-5 h-5 shrink-0" />
              <span
                className={cn(
                  "text-sm font-medium transition-all duration-200",
                  collapsed ? "opacity-0 w-0 overflow-hidden" : "opacity-100"
                )}
              >
                Settings
              </span>
            </NavLink>
          </TooltipTrigger>
          {collapsed && (
            <TooltipContent side="right" sideOffset={10}>
              Settings
            </TooltipContent>
          )}
        </Tooltip>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sidebar-foreground hover:text-foreground hover:bg-sidebar-accent transition-all duration-200 mt-1"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5 shrink-0" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5 shrink-0" />
              <span className="text-sm font-medium">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
