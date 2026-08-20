import { EmptyState } from "@/components/ui/empty-state";

export function MoviesPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.28em] text-wine">The archive</p>
        <h1 className="mt-2 font-display text-5xl">Movies</h1>
        <p className="mt-3 max-w-2xl text-ink/65">
          Cinematic detail pages with backdrops come next. TMDB stays on the server.
        </p>
      </header>
      <EmptyState title="The screen is dark.">Movie search and watchlists ship in Phase 4.</EmptyState>
    </div>
  );
}
