import type { MealType } from "@/types/meal";
import type { MealSlot } from "@/api/importPdf";

export const MEAL_ACCENT: Record<MealType, string> = {
  BREAKFAST: "bg-gold",
  LUNCH: "bg-sage",
  SNACK: "bg-terracotta",
  DINNER: "bg-forest",
};

export const SLOT_ACCENT: Record<MealSlot, string> = {
  breakfast: "bg-gold",
  morning_snack: "bg-terracotta",
  lunch: "bg-sage",
  evening_snack: "bg-terracotta",
  dinner: "bg-forest",
  other: "bg-sage",
};
