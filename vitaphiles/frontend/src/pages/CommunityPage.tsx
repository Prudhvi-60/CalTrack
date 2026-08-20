import { EmptyState } from "@/components/ui/empty-state";

export function CommunityPage() {
  return (
    <div className="space-y-8">
      <h1 className="font-display text-5xl">Community</h1>
      <EmptyState title="No reviewers to follow yet.">
        Profiles, follows, and the activity feed arrive in Phase 6.
      </EmptyState>
    </div>
  );
}
