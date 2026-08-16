import { cn } from "@/utils/cn";

type ProgressProps = {
  value: number;
  className?: string;
  indicatorClassName?: string;
  "aria-label"?: string;
};

export function Progress({ value, className, indicatorClassName, "aria-label": ariaLabel }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div
      className={cn("h-2 w-full overflow-hidden rounded-full bg-[#E5EBE7]", className)}
      role="progressbar"
      aria-label={ariaLabel}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
    >
      <div
        className={cn("h-full rounded-full bg-forest transition-[width] duration-200 ease-out", indicatorClassName)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
