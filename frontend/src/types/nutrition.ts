import type { PaginatedResponse } from "@/types/pagination";

export type MacroSnapshot = {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
};

export type RemainingMacros = {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
};

export type GoalTargets = {
  daily_calorie_target: number;
  protein_target: number;
  carb_target: number;
  fat_target: number;
};

export type DailyMealSummary = {
  id: number;
  meal_type: "BREAKFAST" | "LUNCH" | "DINNER" | "SNACK";
  consumed_at: string;
  notes: string | null;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  food_count: number;
};

export type RecentFood = {
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  consumed_at: string;
  meal_id: number;
  meal_type: DailyMealSummary["meal_type"];
};

export type DailyNutrition = {
  date: string;
  totals: MacroSnapshot;
  remaining: RemainingMacros | null;
  goals: GoalTargets | null;
  meals: DailyMealSummary[];
  recent_foods: RecentFood[];
};

export type DayPoint = {
  date: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
};

export type WeeklyNutrition = {
  start_date: string;
  end_date: string;
  totals: MacroSnapshot;
  days: DayPoint[];
};

export type GoalComparisonItem = {
  name: string;
  label: string;
  unit: string;
  actual: number;
  target: number | null;
  remaining: number | null;
  percent: number;
};

export type GoalComparison = {
  date: string;
  start_date: string;
  end_date: string;
  days: number;
  has_goals: boolean;
  items: GoalComparisonItem[];
};

export type MicronutrientTotal = {
  nutrient_name: string;
  amount: number;
  unit: string;
};

export type NutritionTrends = PaginatedResponse<DayPoint> & {
  start_date: string;
  end_date: string;
  totals: MacroSnapshot;
};

export type MicronutrientReport = PaginatedResponse<MicronutrientTotal> & {
  start_date: string;
  end_date: string;
};
