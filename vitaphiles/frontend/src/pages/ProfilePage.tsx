import { EmptyState } from "@/components/ui/empty-state";

export function ProfilePage() {
  return (
    <div className="space-y-8">
      <header>
        <p className="font-display text-3xl italic text-ink/50">@you</p>
        <h1 className="mt-1 font-display text-5xl">Profile</h1>
      </header>
      <EmptyState title="Accounts come next.">
        Register and login are Phase 2. Then stats, favorites, and recent reviews live on this page.
      </EmptyState>
    </div>
  );
}
