import { NavLink, Outlet } from "react-router-dom";
import { BookOpen, Compass, Home, Library, UserRound } from "lucide-react";
import { cn } from "@/utils/cn";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

const desktopNav = [
  { to: "/", label: "Home" },
  { to: "/discover", label: "Discover" },
  { to: "/books", label: "Books" },
  { to: "/movies", label: "Movies" },
  { to: "/library", label: "My Library" },
  { to: "/lists", label: "Lists" },
  { to: "/community", label: "Community" },
];

const mobileNav = [
  { to: "/", label: "Home", icon: Home },
  { to: "/discover", label: "Discover", icon: Compass },
  { to: "/library", label: "Library", icon: Library },
  { to: "/activity", label: "Activity", icon: BookOpen },
  { to: "/profile", label: "Profile", icon: UserRound },
];

export function AppLayout() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="min-h-svh">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-ivory focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="border-b border-ink/10 bg-ivory/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4">
          <NavLink to="/" className="logo-mark" aria-label="Vitaphiles home">
            VITAPHILES
          </NavLink>
          <nav className="hidden items-center gap-5 lg:flex" aria-label="Primary">
            {desktopNav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn("text-sm tracking-wide text-ink/70 transition-colors hover:text-wine", isActive && "text-wine")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="hidden items-center gap-3 lg:flex">
            <label className="sr-only" htmlFor="global-search">
              Search Vitaphiles
            </label>
            <input
              id="global-search"
              type="search"
              placeholder="Search Vitaphiles..."
              className="w-56 border border-ink/15 bg-paper/60 px-3 py-2 text-sm text-ink placeholder:text-ink/40"
              disabled
            />
            {isAuthenticated && user ? (
              <>
                <NavLink to="/profile" className="text-sm text-ink/70 hover:text-wine">
                  @{user.username}
                </NavLink>
                <Button type="button" variant="ghost" size="sm" onClick={() => void logout()}>
                  Sign out
                </Button>
              </>
            ) : (
              <NavLink to="/login" className="text-sm text-wine hover:underline">
                Sign in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-6xl px-4 pb-24 pt-8 lg:pb-16">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-ink/10 bg-ivory/95 lg:hidden" aria-label="Mobile">
        <ul className="grid grid-cols-5">
          {mobileNav.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn("flex flex-col items-center gap-1 py-2 text-[11px] text-ink/55", isActive && "text-wine")
                }
              >
                <item.icon className="h-5 w-5" aria-hidden />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
