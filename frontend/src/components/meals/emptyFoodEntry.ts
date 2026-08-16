import type { MealFormValues } from "@/schemas/meal";

export const emptyFoodEntry: MealFormValues["food_entries"][number] = {
  food_name: "",
  quantity: 1,
  unit: "serving",
  calories: 0,
  protein: 0,
  carbohydrates: 0,
  fat: 0,
  fiber: 0,
  sugar: 0,
  micronutrients: [],
};
