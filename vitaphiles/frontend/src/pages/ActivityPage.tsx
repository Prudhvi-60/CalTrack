import { EmptyState } from "@/components/ui/empty-state";

export function ActivityPage() {
  return (
    <div className="space-y-8">
      <h1 className="font-display text-5xl">Activity</h1>
      <EmptyState title="Your feed is waiting.">
        Followed readers and cinephiles will appear here, paginated — never dumped all at once.
      </EmptyState>
    </div>
  );
}
