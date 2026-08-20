import { EmptyState } from "@/components/ui/empty-state";

const tabs = ["All", "Books", "Movies"] as const;

export function DiscoverPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.28em] text-wine">Find the next story</p>
        <h1 className="mt-2 font-display text-5xl">Discover</h1>
        <p className="mt-3 max-w-2xl text-ink/65">
          Filter by medium, genre, year, and rating. Search is debounced in a later phase.
        </p>
      </header>
      <div className="flex gap-2 border-b border-ink/10 pb-3" role="tablist" aria-label="Medium">
        {tabs.map((tab, index) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={index === 0}
            className={`px-3 py-1 text-sm ${index === 0 ? "text-wine" : "text-ink/50"}`}
          >
            {tab}
          </button>
        ))}
      </div>
      <EmptyState title="No titles match yet">
        Connect Google Books and TMDB in Phases 3–4, or load seed data, to fill this shelf.
      </EmptyState>
    </div>
  );
}
