import { describe, expect, it } from "vitest";
import { correctionsFromConfirm } from "@/utils/aiMeal";
import type { FoodAnalysis } from "@/types/ai";
import type { MealPayload } from "@/types/meal";

const analysis: FoodAnalysis = {
  analysis_type: "food",
  analysis_id: "analysis-1",
  food_items: [
    {
      name: "rice",
      quantity: 1,
      unit: "cup",
      calories: 205,
      protein: 4,
      carbohydrates: 45,
      fat: 0.4,
      fiber: 0.6,
      sugar: 0,
      micronutrients: [],
      confidence: 0.9,
    },
  ],
  confidence: 0.9,
  notes: "",
  warnings: [],
};

describe("correctionsFromConfirm", () => {
  it("records confirmations and quantity corrections", () => {
    const confirmed = correctionsFromConfirm(analysis, {
      meal_type: "LUNCH",
      consumed_at: "2026-08-16T12:00:00.000Z",
      notes: "",
      food_entries: [
        {
          food_name: "rice",
          quantity: 1,
          unit: "cup",
          calories: 205,
          protein: 4,
          carbohydrates: 45,
          fat: 0.4,
          fiber: 0.6,
          sugar: 0,
          micronutrients: [],
        },
      ],
    } satisfies MealPayload);
    expect(confirmed).toHaveLength(1);
    expect(confirmed[0].confirmed).toBe(true);

    const corrected = correctionsFromConfirm(analysis, {
      meal_type: "LUNCH",
      consumed_at: "2026-08-16T12:00:00.000Z",
      notes: "",
      food_entries: [
        {
          food_name: "rice",
          quantity: 1.5,
          unit: "cup",
          calories: 205,
          protein: 4,
          carbohydrates: 45,
          fat: 0.4,
          fiber: 0.6,
          sugar: 0,
          micronutrients: [],
        },
      ],
    } satisfies MealPayload);
    expect(corrected[0].confirmed).toBe(false);
    expect(corrected[0].predicted_quantity).toBe(1);
    expect(corrected[0].corrected_quantity).toBe(1.5);
  });
});
