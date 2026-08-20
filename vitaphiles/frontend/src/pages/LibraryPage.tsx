import { EmptyState } from "@/components/ui/empty-state";

export function LibraryPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.28em] text-wine">Yours</p>
        <h1 className="mt-2 font-display text-5xl">My Library</h1>
      </header>
      <div className="flex flex-wrap gap-3 text-sm text-ink/55">
        {["Books", "Movies", "Reviews", "Lists", "Activity"].map((tab) => (
          <span key={tab} className="border-b border-transparent pb-1">
            {tab}
          </span>
        ))}
      </div>
      <EmptyState title="Your shelves are empty.">
        Want to Read, Currently Reading, Read, Abandoned — plus Watchlist and Watched — appear after you sign in.
      </EmptyState>
    </div>
  );
}
