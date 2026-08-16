import { z } from "zod";
import { MEAL_TYPES, NUTRIENT_NAMES } from "@/types/meal";

const nonNegative = z.coerce
  .number({ invalid_type_error: "Enter a number" })
  .refine((value) => Number.isFinite(value), "Enter a number")
  .refine((value) => value >= 0, "Must be 0 or greater");

export const micronutrientSchema = z.object({
  nutrient_name: z.enum(NUTRIENT_NAMES),
  amount: nonNegative,
  unit: z.string().trim().min(1, "Unit is required").max(20),
});

export const foodEntrySchema = z.object({
  food_name: z.string().trim().min(1, "Food name is required").max(255),
  quantity: nonNegative,
  unit: z.string().trim().min(1, "Unit is required").max(40),
  calories: nonNegative,
  protein: nonNegative,
  carbohydrates: nonNegative,
  fat: nonNegative,
  fiber: nonNegative,
  sugar: nonNegative,
  micronutrients: z.array(micronutrientSchema),
});

export const mealSchema = z.object({
  meal_type: z.enum(MEAL_TYPES),
  consumed_at: z.string().min(1, "Date and time are required"),
  notes: z.string().max(2000).optional().or(z.literal("")),
  food_entries: z.array(foodEntrySchema).min(1, "Add at least one food"),
});

export type MealFormValues = z.infer<typeof mealSchema>;
