import { EmptyState } from "@/components/ui/empty-state";

export function BooksPage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="text-xs uppercase tracking-[0.28em] text-wine">The library</p>
        <h1 className="mt-2 font-display text-5xl">Books</h1>
        <p className="mt-3 max-w-2xl text-ink/65">
          Covers, authors, and reading status will live here. Metadata arrives through the backend, never the browser.
        </p>
      </header>
      <EmptyState title="No books in this collection yet.">
        Search and tracking ship in Phase 3.
      </EmptyState>
    </div>
  );
}
