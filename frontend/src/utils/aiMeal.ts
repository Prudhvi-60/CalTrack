import { NUTRIENT_NAMES } from "@/types/meal";
import type { AiCorrectionItem, FoodAnalysis } from "@/types/ai";
import type { MealFormValues } from "@/schemas/meal";
import type { MealPayload } from "@/types/meal";
import { toDateTimeLocal } from "@/utils/datetime";
import { emptyFoodEntry } from "@/components/meals/emptyFoodEntry";

export function analysisToFormValues(analysis: FoodAnalysis): MealFormValues {
  const notes = [
    analysis.notes,
    analysis.serving_size ? `Serving size: ${analysis.serving_size}` : "",
    analysis.servings_per_container != null ? `Servings per container: ${analysis.servings_per_container}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return {
    meal_type: analysis.meal_type ?? "SNACK",
    consumed_at: toDateTimeLocal(new Date().toISOString()),
    notes,
    food_entries:
      analysis.food_items.length === 0
        ? [emptyFoodEntry]
        : analysis.food_items.map((item) => ({
            food_name: item.name,
            quantity: Number(item.quantity),
            unit: item.unit,
            calories: Number(item.calories),
            protein: Number(item.protein),
            carbohydrates: Number(item.carbohydrates),
            fat: Number(item.fat),
            fiber: Number(item.fiber ?? 0),
            sugar: Number(item.sugar ?? 0),
            micronutrients: (item.micronutrients ?? [])
              .filter((micro) => (NUTRIENT_NAMES as readonly string[]).includes(micro.nutrient_name))
              .map((micro) => ({
                nutrient_name: micro.nutrient_name as (typeof NUTRIENT_NAMES)[number],
                amount: Number(micro.amount),
                unit: micro.unit,
              })),
          })),
  };
}

export function correctionsFromConfirm(analysis: FoodAnalysis, payload: MealPayload): AiCorrectionItem[] {
  const items: AiCorrectionItem[] = [];
  const count = Math.min(analysis.food_items.length, payload.food_entries.length);
  for (let index = 0; index < count; index += 1) {
    const predicted = analysis.food_items[index];
    const corrected = payload.food_entries[index];
    const nameChanged = predicted.name.trim().toLowerCase() !== corrected.food_name.trim().toLowerCase();
    const qtyChanged = Number(predicted.quantity) !== Number(corrected.quantity);
    const unitChanged = predicted.unit.trim().toLowerCase() !== corrected.unit.trim().toLowerCase();
    items.push({
      predicted_name: predicted.name,
      predicted_quantity: Number(predicted.quantity),
      predicted_unit: predicted.unit,
      corrected_name: corrected.food_name,
      corrected_quantity: Number(corrected.quantity),
      corrected_unit: corrected.unit,
      predicted_confidence: predicted.confidence ?? null,
      confirmed: !nameChanged && !qtyChanged && !unitChanged,
    });
  }
  return items;
}
