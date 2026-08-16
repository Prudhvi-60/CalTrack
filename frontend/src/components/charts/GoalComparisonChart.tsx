import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { GoalComparisonItem } from "@/types/nutrition";

export function GoalComparisonChart({ items }: { items: GoalComparisonItem[] }) {
  const data = items.map((item) => ({
    name: item.label,
    Actual: Math.round(item.actual),
    Target: item.target == null ? 0 : Math.round(item.target),
  }));

  return (
    <div className="h-64 min-h-[16rem] w-full min-w-[1px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#68766F" }} />
          <YAxis tick={{ fontSize: 12, fill: "#68766F" }} width={40} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Actual" fill="#245C4A" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Target" fill="#8FB5A5" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
