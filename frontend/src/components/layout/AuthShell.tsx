import type { ReactNode } from "react";

export function AuthShell({ title, description, children, footer }: { title: string; description: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="surface-card w-full max-w-md p-6 sm:p-8">
        <p className="text-sm font-semibold tracking-tight text-forest">CalTrack</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
        {children}
        <div className="mt-4 text-center text-sm text-muted-foreground">{footer}</div>
      </div>
    </div>
  );
}
