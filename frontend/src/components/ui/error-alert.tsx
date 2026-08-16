import { Button } from "@/components/ui/button";

export function ErrorAlert({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4"
      role="alert"
    >
      <p className="text-sm text-destructive">{message}</p>
      {onRetry && (
        <Button type="button" size="sm" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
