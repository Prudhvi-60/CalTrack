import type { ReactNode } from "react";

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="surface-card p-8 text-center">
      <p className="font-medium text-foreground">{title}</p>
      {children && <div className="mt-2 text-sm leading-relaxed text-muted-foreground">{children}</div>}
    </div>
  );
}
