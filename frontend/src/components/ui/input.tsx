import * as React from "react";
import { cn } from "@/utils/cn";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-[11px] border border-input bg-card px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground transition-colors duration-200 ease-out focus-visible:outline-none focus-visible:border-sage focus-visible:ring-2 focus-visible:ring-sage/30 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      ref={ref}
      {...props}
    />
  ),
);
Input.displayName = "Input";
