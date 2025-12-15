import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "@/contexts/AppContext";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
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
import MovieDetail from "./pages/MovieDetail";
import StreamingDetail from "./pages/StreamingDetail";
import Categories from "./pages/Categories";
import Kids from "./pages/Kids";
import Shuffle from "./pages/Shuffle";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import Watch from "./pages/Watch";
import Login from "./pages/auth/Login";
import Signup from "./pages/auth/Signup";
import VerifyOtp from "./pages/auth/VerifyOtp";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";

const queryClient = new QueryClient();

const ProtectedApp = () => {
  const { token } = useAuth();
  return (
    <AppProvider authToken={token}>
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
          <Route path="/movies/:id" element={<MovieDetail />} />
          <Route path="/watch/:id" element={<Watch />} />
          <Route path="/streaming/:id" element={<StreamingDetail />} />
          <Route path="/tv-shows" element={<TvShows />} />
          <Route path="/trending" element={<Trending />} />
          <Route path="/categories" element={<Categories />} />
          <Route path="/kids" element={<Kids />} />
          <Route path="/shuffle" element={<Shuffle />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </AppProvider>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/auth/login" element={<Login />} />
            <Route path="/auth/signup" element={<Signup />} />
            <Route path="/auth/verify" element={<VerifyOtp />} />
            <Route path="/auth/forgot" element={<ForgotPassword />} />
            <Route path="/auth/reset" element={<ResetPassword />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <ProtectedApp />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
