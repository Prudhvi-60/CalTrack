import { useQuery } from "@tanstack/react-query";
import {
  getDailyNutrition,
  getGoalComparison,
  getMicronutrients,
  getNutritionTrends,
  getWeeklyNutrition,
  type ReportRange,
} from "@/api/nutrition";

export function useDailyNutrition() {
  return useQuery({
    queryKey: ["nutrition", "daily"],
    queryFn: () => getDailyNutrition(),
  });
}

export function useWeeklyNutrition() {
  return useQuery({
    queryKey: ["nutrition", "weekly"],
    queryFn: getWeeklyNutrition,
  });
}

export function useGoalComparison(days?: ReportRange) {
  return useQuery({
    queryKey: ["nutrition", "goal-comparison", days ?? "today"],
    queryFn: () => getGoalComparison(days ? { days } : undefined),
  });
}

export function useNutritionTrends(days: ReportRange) {
  return useQuery({
    queryKey: ["nutrition", "trends", days],
    queryFn: () => getNutritionTrends(days),
  });
}

export function useMicronutrients(days: ReportRange) {
  return useQuery({
    queryKey: ["nutrition", "micronutrients", days],
    queryFn: () => getMicronutrients(days),
  });
}
