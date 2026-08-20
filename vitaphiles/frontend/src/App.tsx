import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { GuestRoute, ProtectedRoute } from "@/layouts/ProtectedRoute";
import { Skeleton } from "@/components/ui/skeleton";

const HomePage = lazy(() => import("@/pages/HomePage").then((m) => ({ default: m.HomePage })));
const DiscoverPage = lazy(() => import("@/pages/DiscoverPage").then((m) => ({ default: m.DiscoverPage })));
const BooksPage = lazy(() => import("@/pages/BooksPage").then((m) => ({ default: m.BooksPage })));
const MoviesPage = lazy(() => import("@/pages/MoviesPage").then((m) => ({ default: m.MoviesPage })));
const LibraryPage = lazy(() => import("@/pages/LibraryPage").then((m) => ({ default: m.LibraryPage })));
const ListsPage = lazy(() => import("@/pages/ListsPage").then((m) => ({ default: m.ListsPage })));
const CommunityPage = lazy(() => import("@/pages/CommunityPage").then((m) => ({ default: m.CommunityPage })));
const ActivityPage = lazy(() => import("@/pages/ActivityPage").then((m) => ({ default: m.ActivityPage })));
const ProfilePage = lazy(() => import("@/pages/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const LoginPage = lazy(() => import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/pages/RegisterPage").then((m) => ({ default: m.RegisterPage })));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));

function RouteFallback() {
  return (
    <div className="space-y-4" aria-busy="true" aria-live="polite">
      <Skeleton className="h-10 w-48" />
      <Skeleton className="h-40 w-full" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/discover" element={<DiscoverPage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route path="/movies" element={<MoviesPage />} />
          <Route path="/community" element={<CommunityPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/lists" element={<ListsPage />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
