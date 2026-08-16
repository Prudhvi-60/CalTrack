import { Link } from "react-router-dom";
import type { DailyMealSummary } from "@/types/nutrition";
import { MEAL_TYPE_LABELS, formatGrams } from "@/utils/meals";
import { formatDateTime } from "@/utils/datetime";

export function TodayMeals({ meals }: { meals: DailyMealSummary[] }) {
  if (meals.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No meals logged today.{" "}
        <Link className="text-primary underline" to="/meals/new">
          Add a meal
        </Link>
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {meals.map((meal) => (
        <li key={meal.id}>
          <Link to={`/meals/${meal.id}`} className="flex items-center justify-between rounded-md border px-3 py-2 hover:bg-accent">
            <div>
              <p className="text-sm font-medium">{MEAL_TYPE_LABELS[meal.meal_type]}</p>
              <p className="text-xs text-muted-foreground">{formatDateTime(meal.consumed_at)}</p>
            </div>
            <p className="text-sm">{formatGrams(meal.calories)} kcal</p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
