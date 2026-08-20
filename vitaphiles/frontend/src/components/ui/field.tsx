import { cloneElement, isValidElement, type ReactElement, type ReactNode } from "react";

export function Field({
  label,
  id,
  error,
  hint,
  children,
}: {
  label: string;
  id: string;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<{ id?: string; "aria-invalid"?: boolean; "aria-describedby"?: string }>, {
        id,
        "aria-invalid": Boolean(error) || undefined,
        "aria-describedby": describedBy,
      })
    : children;

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-xs uppercase tracking-[0.16em] text-ink/50">
        {label}
      </label>
      {control}
      {hint && !error ? (
        <p id={`${id}-hint`} className="text-xs text-ink/45">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} className="text-sm text-wine" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
