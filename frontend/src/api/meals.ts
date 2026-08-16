import { apiClient } from "./client";
import type { PaginatedResponse } from "@/types/pagination";
import type { Meal, MealListParams, MealPayload } from "@/types/meal";

export async function listMeals(params: MealListParams = {}): Promise<PaginatedResponse<Meal>> {
  const cleaned = Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== ""),
  );
  const { data } = await apiClient.get<PaginatedResponse<Meal>>("/api/v1/meals", { params: cleaned });
  return data;
}

export async function getMeal(mealId: number): Promise<Meal> {
  const { data } = await apiClient.get<Meal>(`/api/v1/meals/${mealId}`);
  return data;
}

export async function createMeal(payload: MealPayload): Promise<Meal> {
  const { data } = await apiClient.post<Meal>("/api/v1/meals", payload);
  return data;
}

export async function replaceMeal(mealId: number, payload: MealPayload): Promise<Meal> {
  const { data } = await apiClient.put<Meal>(`/api/v1/meals/${mealId}`, payload);
  return data;
}

export async function deleteMeal(mealId: number): Promise<void> {
  await apiClient.delete(`/api/v1/meals/${mealId}`);
}
