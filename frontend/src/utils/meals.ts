import type { MealType } from "@/types/meal";

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  BREAKFAST: "Breakfast",
  LUNCH: "Lunch",
  DINNER: "Dinner",
  SNACK: "Snack",
};

export function formatGrams(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}
