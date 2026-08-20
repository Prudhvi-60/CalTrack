import type { ReactNode } from "react";

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="border border-ink/10 bg-ivory/70 px-6 py-12 text-center">
      <p className="font-display text-2xl text-ink">{title}</p>
      {children ? <div className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-ink/60">{children}</div> : null}
    </div>
  );
}
