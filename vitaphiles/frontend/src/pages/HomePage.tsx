import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

async function fetchHealth() {
  const { data } = await api.get<{ status: string }>("/health");
  return data;
}

export function HomePage() {
  const { user, isAuthenticated } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth, retry: false });
  const greeting = isAuthenticated && user ? `Welcome back, ${user.display_name}.` : "Stories worth remembering.";

  return (
    <div className="space-y-16">
      <section className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-wine">A journal for stories</p>
          <h1 className="mt-4 font-display text-5xl leading-[1.05] text-ink md:text-7xl">{greeting}</h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink/70">
            Track the books you read, the films you watch, and the stories that stay with you.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/books">Explore Books</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/movies">Explore Movies</Link>
            </Button>
            {!isAuthenticated ? (
              <Button asChild variant="ghost" size="lg">
                <Link to="/register">Join Vitaphiles</Link>
              </Button>
            ) : null}
          </div>
        </div>
        <aside className="border border-ink/10 bg-ivory p-6 shadow-page">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Tonight on the shelf</p>
          <p className="mt-3 font-display text-3xl italic text-ink">Discover → Track → Review → Share</p>
          <p className="mt-3 text-sm text-ink/60">
            {health.isLoading && "Connecting to the archive…"}
            {health.isError && "Archive API is offline — start the FastAPI server on port 8002."}
            {health.data && "The archive is open."}
          </p>
        </aside>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <EmptyState title="Continue reading">
          {isAuthenticated
            ? "Nothing is on your nightstand yet. Tracking ships in Phase 3."
            : "Sign in to resume in-progress books. Nothing is on your nightstand yet."}
        </EmptyState>
        <EmptyState title="Your watchlist">
          {isAuthenticated
            ? "Films you mean to see will live here after Phase 4."
            : "Films you mean to see will live here — a quiet queue, not a dashboard widget."}
        </EmptyState>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-3xl">Trending on Vitaphiles</h2>
        <EmptyState title="The room is still quiet">
          Trending books and films appear once the catalog and community are seeded.
        </EmptyState>
      </section>
    </div>
  );
}
