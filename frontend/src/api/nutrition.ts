import { apiClient } from "./client";
import type {
  DailyNutrition,
  GoalComparison,
  MicronutrientReport,
  NutritionTrends,
  WeeklyNutrition,
} from "@/types/nutrition";

export type ReportRange = 7 | 30 | 90;

export async function getDailyNutrition(date?: string): Promise<DailyNutrition> {
  const { data } = await apiClient.get<DailyNutrition>("/api/v1/nutrition/daily", {
    params: date ? { date } : undefined,
  });
  return data;
}

export async function getWeeklyNutrition(): Promise<WeeklyNutrition> {
  const { data } = await apiClient.get<WeeklyNutrition>("/api/v1/nutrition/weekly");
  return data;
}

export async function getNutritionTrends(days: ReportRange = 7): Promise<NutritionTrends> {
  const { data } = await apiClient.get<NutritionTrends>("/api/v1/nutrition/trends", {
    params: { days, page: 1, page_size: days },
  });
  return data;
}

export async function getMicronutrients(days: ReportRange): Promise<MicronutrientReport> {
  const { data } = await apiClient.get<MicronutrientReport>("/api/v1/nutrition/micronutrients", {
    params: { days, page: 1, page_size: 50 },
  });
  return data;
}

export async function getGoalComparison(options?: { date?: string; days?: ReportRange }): Promise<GoalComparison> {
  const { data } = await apiClient.get<GoalComparison>("/api/v1/nutrition/goal-comparison", {
    params: {
      ...(options?.date ? { date: options.date } : {}),
      ...(options?.days ? { days: options.days } : {}),
    },
  });
  return data;
}
