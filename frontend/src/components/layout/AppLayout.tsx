import { Link, NavLink, Outlet } from "react-router-dom";
import { Apple, FileUp, LayoutDashboard, MessageCircle, ScanLine, Settings, Target, Utensils } from "lucide-react";
import { cn } from "@/utils/cn";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const links = [
  { to: "/dashboard", label: "Dashboard", short: "Home", icon: LayoutDashboard, end: true },
  { to: "/meals", label: "Meals", short: "Meals", icon: Utensils, end: false },
  { to: "/goals", label: "Goals", short: "Goals", icon: Target, end: true },
  { to: "/reports", label: "Reports", short: "Reports", icon: Apple, end: true },
  { to: "/ai-scan", label: "AI Scan", short: "Scan", icon: ScanLine, end: true },
  { to: "/chat", label: "Chat", short: "Chat", icon: MessageCircle, end: true },
  { to: "/import", label: "Import", short: "Import", icon: FileUp, end: true },
  { to: "/settings", label: "Settings", short: "More", icon: Settings, end: true },
];

const navClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "inline-flex items-center gap-1.5 rounded-[10px] px-3 py-2 text-sm text-muted-foreground transition-colors duration-200 ease-out hover:bg-[#F0F4F1] hover:text-forest",
    isActive && "bg-primary-soft font-medium text-forest hover:bg-primary-soft",
  );

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-border bg-card">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <Link to="/dashboard" className="shrink-0 text-lg font-semibold tracking-tight text-forest">
            CalTrack
          </Link>
          <nav className="hidden min-w-0 flex-1 justify-center gap-0.5 lg:flex" aria-label="Primary">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} end={link.end} className={navClass}>
                <link.icon className="hidden h-4 w-4 xl:block" aria-hidden />
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex shrink-0 items-center gap-2">
            <span className="hidden max-w-[10rem] truncate text-sm text-muted-foreground xl:inline">{user?.name}</span>
            <Button type="button" variant="ghost" size="sm" onClick={() => void logout()}>
              Sign out
            </Button>
          </div>
        </div>
        <nav className="grid grid-cols-4 gap-1 px-2 pb-2 lg:hidden" aria-label="Mobile">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "flex min-w-0 flex-col items-center gap-0.5 rounded-[10px] px-1 py-2 text-[11px] text-muted-foreground transition-colors duration-200 ease-out hover:bg-[#F0F4F1]",
                  isActive && "bg-primary-soft font-medium text-forest",
                )
              }
            >
              <link.icon className="h-4 w-4" aria-hidden />
              <span className="truncate">{link.short}</span>
            </NavLink>
          ))}
        </nav>
      </header>
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-6xl px-4 py-6 outline-none sm:py-8">
        <Outlet />
      </main>
    </div>
  );
}
