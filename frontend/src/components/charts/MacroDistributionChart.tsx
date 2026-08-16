import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { MacroSnapshot } from "@/types/nutrition";

const COLORS = ["hsl(210 50% 40%)", "hsl(32 80% 50%)", "hsl(350 55% 45%)"];

export function MacroDistributionChart({
  totals,
  emptyMessage = "No macros logged today.",
}: {
  totals: MacroSnapshot;
  emptyMessage?: string;
}) {
  const data = [
    { name: "Protein", value: totals.protein },
    { name: "Carbs", value: totals.carbohydrates },
    { name: "Fat", value: totals.fat },
  ].filter((item) => item.value > 0);

  if (data.length === 0) {
    return <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <div className="h-64 min-h-[16rem] w-full min-w-[1px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={COLORS[["Protein", "Carbs", "Fat"].indexOf(entry.name)]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => `${Math.round(value)} g`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
