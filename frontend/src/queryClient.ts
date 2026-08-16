import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status === 401 || status === 403 || status === 404 || status === 422) {
          return false;
        }
        return failureCount < 1;
      },
      refetchOnWindowFocus: false,
      staleTime: 30_000,
      gcTime: 5 * 60_000,
    },
    mutations: {
      retry: false,
    },
  },
});

export function clearUserQueries(): void {
  queryClient.removeQueries({ queryKey: ["meals"] });
  queryClient.removeQueries({ queryKey: ["nutrition"] });
  queryClient.removeQueries({ queryKey: ["goals"] });
}

export function invalidateMealRelated(): void {
  void queryClient.invalidateQueries({ queryKey: ["meals"] });
  void queryClient.invalidateQueries({ queryKey: ["nutrition"] });
}

export function invalidateGoalRelated(): void {
  void queryClient.invalidateQueries({ queryKey: ["goals"] });
  void queryClient.invalidateQueries({ queryKey: ["nutrition"] });
}
