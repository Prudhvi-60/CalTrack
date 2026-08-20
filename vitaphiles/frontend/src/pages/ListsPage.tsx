import { EmptyState } from "@/components/ui/empty-state";

export function ListsPage() {
  return (
    <div className="space-y-8">
      <h1 className="font-display text-5xl">Lists</h1>
      <EmptyState title="No lists yet.">
        Public, private, and followers-only collections ship in Phase 7.
      </EmptyState>
    </div>
  );
}
