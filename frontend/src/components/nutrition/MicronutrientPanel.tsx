import type { MicronutrientTotal } from "@/types/nutrition";
import { formatGrams } from "@/utils/meals";

export const FEATURED_MICRONUTRIENTS = [
  "Vitamin A",
  "Vitamin C",
  "Vitamin D",
  "Calcium",
  "Iron",
  "Magnesium",
  "Potassium",
  "Zinc",
] as const;

export function MicronutrientPanel({ items }: { items: MicronutrientTotal[] }) {
  const byName = new Map(items.map((item) => [item.nutrient_name, item]));
  const featured = FEATURED_MICRONUTRIENTS.map((name) => byName.get(name) ?? { nutrient_name: name, amount: 0, unit: "mg" });
  const extras = items.filter((item) => !FEATURED_MICRONUTRIENTS.includes(item.nutrient_name as (typeof FEATURED_MICRONUTRIENTS)[number]));

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {featured.map((item) => (
          <div key={item.nutrient_name} className="rounded-[14px] border border-border bg-secondary/70 p-3">
            <p className="text-sm text-muted-foreground">{item.nutrient_name}</p>
            <p className="mt-1 font-medium">
              {formatGrams(item.amount)} {item.unit}
            </p>
          </div>
        ))}
      </div>
      {extras.length > 0 && (
        <ul className="grid gap-2 text-sm sm:grid-cols-2">
          {extras.map((item) => (
            <li key={item.nutrient_name} className="flex justify-between rounded-md border px-3 py-2">
              <span>{item.nutrient_name}</span>
              <span>
                {formatGrams(item.amount)} {item.unit}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
