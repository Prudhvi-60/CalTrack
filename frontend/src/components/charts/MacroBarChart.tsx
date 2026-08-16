import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MacroSnapshot } from "@/types/nutrition";

export function MacroBarChart({ totals }: { totals: MacroSnapshot }) {
  const data = [
    { name: "Protein", grams: Math.round(totals.protein) },
    { name: "Carbs", grams: Math.round(totals.carbohydrates) },
    { name: "Fat", grams: Math.round(totals.fat) },
  ];

  return (
    <div className="h-64 min-h-[16rem] w-full min-w-[1px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} width={40} />
          <Tooltip formatter={(value: number) => [`${value} g`, "Total"]} />
          <Legend />
          <Bar dataKey="grams" name="Grams" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
