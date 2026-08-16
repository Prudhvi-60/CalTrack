import { apiClient } from "./client";
import type { PaginatedResponse } from "@/types/pagination";
import type { Goal, GoalPayload } from "@/types/goal";

export async function listGoals(page = 1, pageSize = 20): Promise<PaginatedResponse<Goal>> {
  const { data } = await apiClient.get<PaginatedResponse<Goal>>("/api/v1/goals", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function createGoal(payload: GoalPayload): Promise<Goal> {
  const { data } = await apiClient.post<Goal>("/api/v1/goals", payload);
  return data;
}

export async function replaceGoal(payload: GoalPayload): Promise<Goal> {
  const { data } = await apiClient.put<Goal>("/api/v1/goals", payload);
  return data;
}

export async function patchGoal(payload: Partial<GoalPayload>): Promise<Goal> {
  const { data } = await apiClient.patch<Goal>("/api/v1/goals", payload);
  return data;
}

export async function deleteGoal(): Promise<void> {
  await apiClient.delete("/api/v1/goals");
}
