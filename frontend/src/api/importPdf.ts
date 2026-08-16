import { apiClient } from "./client";
import type { Meal } from "@/types/meal";

export type MealSlot = "breakfast" | "morning_snack" | "lunch" | "evening_snack" | "dinner" | "other";

export type MealPlanFood = {
  food: string;
  quantity: number | null;
  quantity_text: string | null;
  unit: string | null;
  notes: string;
  original_label: string | null;
  meal_name: string | null;
  alternative: string | null;
  nutrition_status: "matched" | "unknown";
  matched_food: string | null;
  calories: number | null;
  protein: number | null;
  carbohydrates: number | null;
  fat: number | null;
  fiber: number | null;
  sugar: number | null;
};

export type MealPlanMeals = Record<MealSlot, MealPlanFood[]>;

export type MealPlanDay = {
  day: number | null;
  date: string | null;
  label: string | null;
  meals: MealPlanMeals;
};

export type MealPlanPreview = {
  success: boolean;
  document_type: string;
  title: string | null;
  extraction_method: string;
  days_detected: number;
  meals_detected: number;
  foods_detected: number;
  warnings: string[];
  days: MealPlanDay[];
};

export type MealPlanConfirmFood = {
  food: string;
  quantity: number | null;
  unit: string | null;
  notes: string;
  original_label: string | null;
  meal_name: string | null;
  alternative: string | null;
  nutrition_status: "matched" | "unknown";
  calories: number | null;
  protein: number | null;
  carbohydrates: number | null;
  fat: number | null;
  fiber: number | null;
  sugar: number | null;
  slot: MealSlot;
  include: boolean;
};

export type MealPlanConfirmResult = {
  imported_meals: number;
  imported_foods: number;
  meals: Meal[];
};

export const MEAL_SLOTS: { id: MealSlot; label: string }[] = [
  { id: "breakfast", label: "Breakfast" },
  { id: "morning_snack", label: "Morning snack" },
  { id: "lunch", label: "Lunch" },
  { id: "evening_snack", label: "Evening snack" },
  { id: "dinner", label: "Dinner" },
  { id: "other", label: "Other" },
];

export async function previewMealPlan(file: File): Promise<MealPlanPreview> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<MealPlanPreview>("/api/v1/import/meal-plan", form, { timeout: 120000 });
  return data;
}

export async function confirmMealPlan(days: Array<{
  day: number | null;
  date: string;
  label: string | null;
  include: boolean;
  foods: MealPlanConfirmFood[];
}>): Promise<MealPlanConfirmResult> {
  const { data } = await apiClient.post<MealPlanConfirmResult>("/api/v1/import/meal-plan/confirm", { days });
  return data;
}

export type PdfPreviewRow = {
  index: number;
  valid: boolean;
  errors: string[];
  date: string | null;
  meal_type: string | null;
  food_name: string | null;
  quantity: number | null;
  unit: string | null;
  calories: number | null;
  protein: number | null;
  carbohydrates: number | null;
  fat: number | null;
  fiber: number | null;
  sugar: number | null;
};

export type PdfPreview = {
  rows: PdfPreviewRow[];
  valid_count: number;
  invalid_count: number;
  warnings: string[];
};

export type PdfImportRow = {
  date: string;
  meal_type: string;
  food_name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
};

export type PdfConfirmResult = {
  imported_meals: number;
  imported_foods: number;
  meals: Meal[];
};

export async function previewPdf(file: File): Promise<PdfPreview> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<PdfPreview>("/api/v1/import/pdf", form, { timeout: 60000 });
  return data;
}

export async function confirmPdfImport(rows: PdfImportRow[]): Promise<PdfConfirmResult> {
  const { data } = await apiClient.post<PdfConfirmResult>("/api/v1/import/pdf/confirm", { rows });
  return data;
}
