import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "@/contexts/AppContext";
import { Layout } from "@/components/Layout";
import Index from "./pages/Index";
import Profile from "./pages/Profile";
import Favorites from "./pages/Favorites";
import History from "./pages/History";
import Downloads from "./pages/Downloads";
import MyList from "./pages/MyList";
import Search from "./pages/Search";
import Movies from "./pages/Movies";
import TvShows from "./pages/TvShows";
import Trending from "./pages/Trending";
import Categories from "./pages/Categories";
import Kids from "./pages/Kids";
import Shuffle from "./pages/Shuffle";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AppProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/favorites" element={<Favorites />} />
              <Route path="/history" element={<History />} />
              <Route path="/downloads" element={<Downloads />} />
              <Route path="/my-list" element={<MyList />} />
              <Route path="/search" element={<Search />} />
              <Route path="/movies" element={<Movies />} />
              <Route path="/tv-shows" element={<TvShows />} />
              <Route path="/trending" element={<Trending />} />
              <Route path="/categories" element={<Categories />} />
              <Route path="/kids" element={<Kids />} />
              <Route path="/shuffle" element={<Shuffle />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </TooltipProvider>
    </AppProvider>
  </QueryClientProvider>
);

export default App;
