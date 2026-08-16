export const MEAL_TYPES = ["BREAKFAST", "LUNCH", "DINNER", "SNACK"] as const;
export type MealType = (typeof MEAL_TYPES)[number];

export const NUTRIENT_NAMES = [
  "Vitamin A",
  "Vitamin B1",
  "Vitamin B2",
  "Vitamin B3",
  "Vitamin B6",
  "Vitamin B12",
  "Vitamin C",
  "Vitamin D",
  "Vitamin E",
  "Vitamin K",
  "Calcium",
  "Iron",
  "Magnesium",
  "Potassium",
  "Zinc",
  "Sodium",
] as const;

export type NutrientName = (typeof NUTRIENT_NAMES)[number];

export type Micronutrient = {
  id?: number;
  nutrient_name: string;
  amount: number;
  unit: string;
};

export type FoodEntry = {
  id?: number;
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
  micronutrients: Micronutrient[];
};

export type MealTotals = {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
};

export type Meal = {
  id: number;
  user_id: number;
  meal_type: MealType;
  consumed_at: string;
  notes: string | null;
  food_entries: FoodEntry[];
  totals: MealTotals;
  created_at: string;
  updated_at: string;
};

export type MealPayload = {
  meal_type: MealType;
  consumed_at: string;
  notes: string | null;
  food_entries: Array<Omit<FoodEntry, "id">>;
};

export type MealListParams = {
  page?: number;
  page_size?: number;
  date?: string;
  start_date?: string;
  end_date?: string;
  meal_type?: MealType | "";
  q?: string;
};
