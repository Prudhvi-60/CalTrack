import { Progress } from "@/components/ui/progress";

type MacroProgressProps = {
  label: string;
  actual: number;
  target: number;
  remaining: number;
  unit: string;
};

function format(value: number) {
  return Math.round(value).toLocaleString();
}

export function MacroProgress({ label, actual, target, remaining, unit }: MacroProgressProps) {
  const percent = target > 0 ? (actual / target) * 100 : 0;
  const over = remaining < 0;

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium">{label}</h3>
        <p className="text-sm text-muted-foreground">
          {format(actual)} / {format(target)} {unit}
        </p>
      </div>
      <Progress className="mt-3" value={percent} aria-label={`${label} progress`} />
      <p className={`mt-2 text-sm ${over ? "text-destructive" : "text-muted-foreground"}`}>
        {over
          ? `Over by ${format(Math.abs(remaining))} ${unit}`
          : `${format(remaining)} ${unit} remaining`}
      </p>
    </div>
  );
}
