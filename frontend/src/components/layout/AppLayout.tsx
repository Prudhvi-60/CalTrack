import { Link, NavLink, Outlet } from "react-router-dom";
import { Apple, FileUp, LayoutDashboard, MessageCircle, ScanLine, Settings, Target, Utensils } from "lucide-react";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/meals", label: "Meals", icon: Utensils, end: false },
  { to: "/goals", label: "Goals", icon: Target, end: true },
  { to: "/reports", label: "Reports", icon: Apple, end: true },
  { to: "/ai-scan", label: "AI Scan", icon: ScanLine, end: true },
  { to: "/chat", label: "Chat", icon: MessageCircle, end: true },
  { to: "/import", label: "Import", icon: FileUp, end: true },
  { to: "/settings", label: "Settings", icon: Settings, end: true },
];

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/dashboard" className="text-lg font-semibold tracking-tight text-primary">
            CalTrack
          </Link>
          <nav className="hidden gap-1 md:flex" aria-label="Primary">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    isActive && "bg-accent font-medium text-foreground",
                  )
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">{user?.name}</span>
            <Button type="button" variant="ghost" size="sm" onClick={() => void logout()}>
              Sign out
            </Button>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-2 pb-2 md:hidden" aria-label="Mobile">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-1 whitespace-nowrap rounded-md px-3 py-2 text-sm text-muted-foreground",
                  isActive && "bg-accent font-medium text-foreground",
                )
              }
            >
              <link.icon className="h-4 w-4" aria-hidden />
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-6xl px-4 py-6 outline-none">
        <Outlet />
      </main>
    </div>
  );
}
