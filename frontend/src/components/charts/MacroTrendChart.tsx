import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DayPoint } from "@/types/nutrition";
import { chartColors } from "@/theme/palette";

export function MacroTrendChart({ days }: { days: DayPoint[] }) {
  const compact = days.length > 7;
  const data = days.map((day) => ({
    ...day,
    label: new Date(`${day.date}T00:00:00Z`).toLocaleDateString(undefined, compact
      ? { month: "short", day: "numeric" }
      : { weekday: "short" }),
  }));
  const interval = compact ? Math.ceil(days.length / 7) - 1 : 0;

  return (
    <div className="h-64 min-h-[16rem] w-full min-w-[1px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#68766F" }} interval={interval} />
          <YAxis tick={{ fontSize: 12, fill: "#68766F" }} width={48} />
          <Tooltip formatter={(value: number, name: string) => [`${Math.round(value)} g`, name]} />
          <Legend />
          <Line type="monotone" dataKey="protein" name="Protein" stroke={chartColors.protein} strokeWidth={2} dot={compact ? false : { r: 3 }} />
          <Line
            type="monotone"
            dataKey="carbohydrates"
            name="Carbs"
            stroke={chartColors.carbs}
            strokeWidth={2}
            dot={compact ? false : { r: 3 }}
          />
          <Line type="monotone" dataKey="fat" name="Fat" stroke={chartColors.fat} strokeWidth={2} dot={compact ? false : { r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
