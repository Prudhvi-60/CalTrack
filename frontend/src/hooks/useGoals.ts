import { useMutation, useQuery } from "@tanstack/react-query";
import { createGoal, deleteGoal, listGoals, replaceGoal } from "@/api/goals";
import { invalidateGoalRelated } from "@/queryClient";
import type { GoalPayload } from "@/types/goal";

export const goalsQueryKey = ["goals"] as const;

export function useGoals() {
  return useQuery({
    queryKey: goalsQueryKey,
    queryFn: () => listGoals(1, 20),
  });
}

export function useCreateGoal() {
  return useMutation({
    mutationFn: (payload: GoalPayload) => createGoal(payload),
    onSuccess: () => invalidateGoalRelated(),
  });
}

export function useReplaceGoal() {
  return useMutation({
    mutationFn: (payload: GoalPayload) => replaceGoal(payload),
    onSuccess: () => invalidateGoalRelated(),
  });
}

export function useDeleteGoal() {
  return useMutation({
    mutationFn: () => deleteGoal(),
    onSuccess: () => invalidateGoalRelated(),
  });
}
