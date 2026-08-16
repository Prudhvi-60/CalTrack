import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DayPoint } from "@/types/nutrition";

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
          <XAxis dataKey="label" tick={{ fontSize: 12 }} interval={interval} />
          <YAxis tick={{ fontSize: 12 }} width={48} />
          <Tooltip formatter={(value: number, name: string) => [`${Math.round(value)} g`, name]} />
          <Legend />
          <Line type="monotone" dataKey="protein" name="Protein" stroke="#2563eb" strokeWidth={2} dot={compact ? false : { r: 3 }} />
          <Line
            type="monotone"
            dataKey="carbohydrates"
            name="Carbs"
            stroke="#16a34a"
            strokeWidth={2}
            dot={compact ? false : { r: 3 }}
          />
          <Line type="monotone" dataKey="fat" name="Fat" stroke="#d97706" strokeWidth={2} dot={compact ? false : { r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
