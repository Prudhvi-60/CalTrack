import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function AuthShell({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="flex min-h-svh items-center justify-center px-4 py-10">
      <div className="w-full max-w-md border border-ink/10 bg-ivory p-8 shadow-page">
        <Link to="/" className="logo-mark text-lg">
          VITAPHILES
        </Link>
        <h1 className="mt-6 font-display text-4xl text-ink">{title}</h1>
        <p className="mt-3 text-sm leading-relaxed text-ink/60">{description}</p>
        {children}
        <div className="mt-6 text-center text-sm text-ink/55">{footer}</div>
      </div>
    </div>
  );
}
