import type { LucideIcon } from "lucide-react";
import { Droplets, Flame, Leaf, Wheat } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/utils/cn";

type MacroProgressProps = {
  label: string;
  actual: number;
  target: number;
  remaining: number;
  unit: string;
};

type Accent = {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  bar: string;
};

const ACCENTS: Record<string, Accent> = {
  Calories: { icon: Flame, iconBg: "bg-terracotta/15", iconColor: "text-terracotta", bar: "bg-terracotta" },
  Protein: { icon: Droplets, iconBg: "bg-sage/20", iconColor: "text-forest", bar: "bg-sage" },
  Carbohydrates: { icon: Wheat, iconBg: "bg-gold/20", iconColor: "text-[#9a7c3a]", bar: "bg-gold" },
  Fat: { icon: Droplets, iconBg: "bg-forest/10", iconColor: "text-forest", bar: "bg-forest" },
  Fiber: { icon: Leaf, iconBg: "bg-sage/20", iconColor: "text-sage", bar: "bg-sage" },
};

function format(value: number) {
  return Math.round(value).toLocaleString();
}

export function MacroProgress({ label, actual, target, remaining, unit }: MacroProgressProps) {
  const percent = target > 0 ? (actual / target) * 100 : 0;
  const over = remaining < 0;
  const accent = ACCENTS[label] ?? ACCENTS.Calories;
  const Icon = accent.icon;
  const displayPercent = target > 0 ? Math.round(percent) : null;

  return (
    <div className="surface-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl", accent.iconBg)}>
            <Icon className={cn("h-4 w-4", accent.iconColor)} aria-hidden />
          </span>
          <div className="min-w-0">
            <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</h3>
            <p className="mt-0.5 text-xl font-semibold tabular-nums tracking-tight text-foreground">
              {format(actual)} / {format(target)} {unit}
            </p>
          </div>
        </div>
        {displayPercent != null && (
          <p className="shrink-0 text-sm tabular-nums text-muted-foreground">{displayPercent}%</p>
        )}
      </div>
      <Progress
        className="mt-3"
        value={percent}
        aria-label={`${label} progress`}
        indicatorClassName={over ? "bg-gold" : accent.bar}
      />
      <p className={`mt-2 text-sm ${over ? "text-destructive" : "text-muted-foreground"}`}>
        {over
          ? `Over by ${format(Math.abs(remaining))} ${unit}`
          : `${format(remaining)} ${unit} remaining`}
      </p>
    </div>
  );
}
