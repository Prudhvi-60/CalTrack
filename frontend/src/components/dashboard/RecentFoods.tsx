import { Link } from "react-router-dom";
import type { RecentFood } from "@/types/nutrition";
import { formatGrams } from "@/utils/meals";

export function RecentFoods({ foods }: { foods: RecentFood[] }) {
  if (foods.length === 0) {
    return <p className="text-sm text-muted-foreground">No foods logged today.</p>;
  }

  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-muted-foreground">
              <th className="pb-2 font-medium">Food</th>
              <th className="pb-2 font-medium">Qty</th>
              <th className="pb-2 font-medium">kcal</th>
              <th className="pb-2 font-medium">P</th>
              <th className="pb-2 font-medium">C</th>
              <th className="pb-2 font-medium">F</th>
            </tr>
          </thead>
          <tbody>
            {foods.map((food, index) => (
              <tr key={`${food.meal_id}-${food.food_name}-${index}`} className="border-t">
                <td className="py-2">
                  <Link className="text-primary underline" to={`/meals/${food.meal_id}`}>
                    {food.food_name}
                  </Link>
                </td>
                <td className="py-2">
                  {formatGrams(food.quantity)} {food.unit}
                </td>
                <td className="py-2">{formatGrams(food.calories)}</td>
                <td className="py-2">{formatGrams(food.protein)}</td>
                <td className="py-2">{formatGrams(food.carbohydrates)}</td>
                <td className="py-2">{formatGrams(food.fat)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="space-y-2 md:hidden">
        {foods.map((food, index) => (
          <li key={`${food.meal_id}-${index}`} className="rounded-md border px-3 py-2 text-sm">
            <Link className="font-medium text-primary underline" to={`/meals/${food.meal_id}`}>
              {food.food_name}
            </Link>
            <p className="text-muted-foreground">
              {formatGrams(food.quantity)} {food.unit} · {formatGrams(food.calories)} kcal
            </p>
          </li>
        ))}
      </ul>
    </>
  );
}
