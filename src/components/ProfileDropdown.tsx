import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import {
  User,
  Settings,
  HelpCircle,
  LogOut,
  Globe,
  Subtitles,
  Sun,
  Moon,
  Bell,
  CreditCard,
  Shield,
  UserPlus,
  Download,
  History,
  Heart,
  List,
  ChevronDown,
  Check,
} from "lucide-react";
import { useApp } from "@/contexts/AppContext";
import { languages, subtitleLanguages } from "@/data/mockData";
import { useNavigate } from "react-router-dom";

const profiles = [
  { id: "1", name: "John", avatar: "", color: "bg-primary" },
  { id: "2", name: "Sarah", avatar: "", color: "bg-chart-2" },
  { id: "3", name: "Kids", avatar: "", color: "bg-chart-3" },
];

export function ProfileDropdown() {
  const { theme, toggleTheme, language, setLanguage, subtitles, setSubtitles } = useApp();
  const [activeProfile, setActiveProfile] = useState(profiles[0]);
  const navigate = useNavigate();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 hover:opacity-80 transition-opacity outline-none">
          <Avatar className="w-8 h-8 ring-2 ring-transparent hover:ring-primary transition-all">
            <AvatarImage src={activeProfile.avatar} />
            <AvatarFallback className={activeProfile.color}>
              {activeProfile.name[0]}
            </AvatarFallback>
          </Avatar>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72 animate-scale-in">
        {/* Profile Switcher */}
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{activeProfile.name}</p>
            <p className="text-xs text-muted-foreground">Switch Profile</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <DropdownMenuGroup>
          {profiles.map((profile) => (
            <DropdownMenuItem
              key={profile.id}
              onClick={() => setActiveProfile(profile)}
              className="cursor-pointer"
            >
              <Avatar className="w-8 h-8 mr-3">
                <AvatarFallback className={profile.color}>
                  {profile.name[0]}
                </AvatarFallback>
              </Avatar>
              <span>{profile.name}</span>
              {activeProfile.id === profile.id && (
                <Check className="w-4 h-4 ml-auto text-primary" />
              )}
            </DropdownMenuItem>
          ))}
          <DropdownMenuItem className="cursor-pointer">
            <div className="w-8 h-8 mr-3 rounded-full border-2 border-dashed border-muted-foreground flex items-center justify-center">
              <UserPlus className="w-4 h-4 text-muted-foreground" />
            </div>
            <span>Add Profile</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* Quick Navigation */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer">
            <User className="w-4 h-4 mr-3" />
            <span>Manage Profile</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate("/my-list")} className="cursor-pointer">
            <List className="w-4 h-4 mr-3" />
            <span>My List</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate("/favorites")} className="cursor-pointer">
            <Heart className="w-4 h-4 mr-3" />
            <span>Favorites</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate("/history")} className="cursor-pointer">
            <History className="w-4 h-4 mr-3" />
            <span>Watch History</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate("/downloads")} className="cursor-pointer">
            <Download className="w-4 h-4 mr-3" />
            <span>Downloads</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* Settings */}
        <DropdownMenuGroup>
          {/* Language */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Globe className="w-4 h-4 mr-3" />
              <span>Language</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent className="w-48">
              {languages.map((lang) => (
                <DropdownMenuItem
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className="cursor-pointer"
                >
                  <span>{lang.name}</span>
                  {language === lang.code && (
                    <Check className="w-4 h-4 ml-auto text-primary" />
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          {/* Subtitles */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Subtitles className="w-4 h-4 mr-3" />
              <span>Subtitles</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent className="w-48">
              {subtitleLanguages.map((lang) => (
                <DropdownMenuItem
                  key={lang.code}
                  onClick={() => setSubtitles(lang.code)}
                  className="cursor-pointer"
                >
                  <span>{lang.name}</span>
                  {subtitles === lang.code && (
                    <Check className="w-4 h-4 ml-auto text-primary" />
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          {/* Theme Toggle */}
          <DropdownMenuItem onClick={toggleTheme} className="cursor-pointer">
            {theme === "dark" ? (
              <Moon className="w-4 h-4 mr-3" />
            ) : (
              <Sun className="w-4 h-4 mr-3" />
            )}
            <span>Dark Mode</span>
            <Switch checked={theme === "dark"} className="ml-auto" />
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        {/* Account */}
        <DropdownMenuGroup>
          <DropdownMenuItem onClick={() => navigate("/settings")} className="cursor-pointer">
            <Settings className="w-4 h-4 mr-3" />
            <span>Settings</span>
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer">
            <Bell className="w-4 h-4 mr-3" />
            <span>Notifications</span>
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer">
            <CreditCard className="w-4 h-4 mr-3" />
            <span>Subscription</span>
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer">
            <Shield className="w-4 h-4 mr-3" />
            <span>Privacy</span>
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer">
            <HelpCircle className="w-4 h-4 mr-3" />
            <span>Help Center</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem className="cursor-pointer text-destructive focus:text-destructive">
          <LogOut className="w-4 h-4 mr-3" />
          <span>Sign Out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
