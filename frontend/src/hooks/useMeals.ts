import { useMutation, useQuery } from "@tanstack/react-query";
import { createMeal, deleteMeal, getMeal, listMeals, replaceMeal } from "@/api/meals";
import { invalidateMealRelated } from "@/queryClient";
import type { MealListParams, MealPayload } from "@/types/meal";

export const mealsQueryKey = ["meals"] as const;

export function useMeals(params: MealListParams) {
  return useQuery({
    queryKey: [...mealsQueryKey, params],
    queryFn: () => listMeals(params),
  });
}

export function useMeal(mealId: number) {
  return useQuery({
    queryKey: [...mealsQueryKey, mealId],
    queryFn: () => getMeal(mealId),
    enabled: Number.isFinite(mealId) && mealId > 0,
  });
}

export function useCreateMeal() {
  return useMutation({
    mutationFn: (payload: MealPayload) => createMeal(payload),
    onSuccess: () => invalidateMealRelated(),
  });
}

export function useReplaceMeal(mealId: number) {
  return useMutation({
    mutationFn: (payload: MealPayload) => replaceMeal(mealId, payload),
    onSuccess: () => invalidateMealRelated(),
  });
}

export function useDeleteMeal() {
  return useMutation({
    mutationFn: (mealId: number) => deleteMeal(mealId),
    onSuccess: () => invalidateMealRelated(),
  });
}
