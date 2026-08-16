import { cloneElement, isValidElement, type ReactElement, type ReactNode } from "react";

export function Field({
  label,
  id,
  error,
  children,
}: {
  label: string;
  id: string;
  error?: string;
  children: ReactNode;
}) {
  const describedBy = error ? `${id}-error` : undefined;
  const control = isValidElement(children)
    ? cloneElement(children as ReactElement<{ id?: string; "aria-invalid"?: boolean; "aria-describedby"?: string }>, {
        id,
        "aria-invalid": Boolean(error) || undefined,
        "aria-describedby": describedBy,
      })
    : children;

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </label>
      {control}
      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
