import { Link } from "react-router-dom";
import type { DailyMealSummary } from "@/types/nutrition";
import { MEAL_TYPE_LABELS, formatGrams } from "@/utils/meals";
import { MEAL_ACCENT } from "@/utils/accents";
import { formatDateTime } from "@/utils/datetime";

export function TodayMeals({ meals }: { meals: DailyMealSummary[] }) {
  if (meals.length === 0) {
    return (
      <p className="text-sm leading-relaxed text-muted-foreground">
        No meals logged yet. Start by adding your first meal to see your nutrition summary.{" "}
        <Link className="text-forest underline underline-offset-2" to="/meals/new">
          Add a meal
        </Link>
      </p>
    );
  }

  return (
    <ul className="space-y-2.5">
      {meals.map((meal) => (
        <li key={meal.id}>
          <Link
            to={`/meals/${meal.id}`}
            className="flex items-center justify-between gap-3 rounded-[14px] border border-border bg-card px-3 py-2.5 transition-colors duration-200 ease-out hover:bg-[#F0F4F1]"
          >
            <div className="flex min-w-0 items-center gap-3">
              <span className={`h-8 w-1 shrink-0 rounded-full ${MEAL_ACCENT[meal.meal_type]}`} aria-hidden />
              <div className="min-w-0">
                <p className="text-sm font-medium">{MEAL_TYPE_LABELS[meal.meal_type]}</p>
                <p className="text-xs text-muted-foreground">
                  {formatDateTime(meal.consumed_at)} · {meal.food_count} item{meal.food_count === 1 ? "" : "s"}
                </p>
              </div>
            </div>
            <div className="shrink-0 text-right">
              <p className="text-sm font-semibold tabular-nums">{formatGrams(meal.calories)} kcal</p>
              <p className="text-[11px] text-muted-foreground">
                P {formatGrams(meal.protein)} · C {formatGrams(meal.carbohydrates)} · F {formatGrams(meal.fat)}
              </p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
