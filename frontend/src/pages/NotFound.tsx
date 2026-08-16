import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { usePageTitle } from "@/hooks/usePageTitle";

export function NotFound() {
  usePageTitle("Page not found");

  return (
    <section className="space-y-6">
      <PageHeader title="Page not found" description="That URL is not part of CalTrack." />
      <Button asChild>
        <Link to="/dashboard">Back to dashboard</Link>
      </Button>
    </section>
  );
}
