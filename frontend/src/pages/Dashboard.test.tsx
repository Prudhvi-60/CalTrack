import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "@/pages/Dashboard";

vi.mock("@/hooks/useNutrition", () => ({
  useDailyNutrition: () => ({
    isLoading: false,
    error: null,
    data: {
      date: "2026-08-15",
      totals: { calories: 1850, protein: 105, carbohydrates: 210, fat: 52, fiber: 20, sugar: 40 },
      remaining: { calories: 350, protein: 25, carbohydrates: 40, fat: 18 },
      goals: { daily_calorie_target: 2200, protein_target: 130, carb_target: 250, fat_target: 70 },
      meals: [],
      recent_foods: [],
    },
  }),
  useWeeklyNutrition: () => ({
    isLoading: false,
    error: null,
    data: {
      start_date: "2026-08-09",
      end_date: "2026-08-15",
      totals: { calories: 1850, protein: 105, carbohydrates: 210, fat: 52, fiber: 0, sugar: 0 },
      days: [{ date: "2026-08-15", calories: 1850, protein: 105, carbohydrates: 210, fat: 52 }],
    },
  }),
  useGoalComparison: () => ({
    isLoading: false,
    error: null,
    data: {
      date: "2026-08-15",
      has_goals: true,
      items: [
        { name: "calories", label: "Calories", unit: "kcal", actual: 1850, target: 2200, remaining: 350, percent: 84 },
      ],
    },
  }),
}));

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

vi.stubGlobal("ResizeObserver", ResizeObserverMock);

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Dashboard", () => {
  it("shows calorie progress from the nutrition API", async () => {
    renderDashboard();
    expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("1,850 / 2,200 kcal")).toBeInTheDocument();
    expect(screen.getByText("350 kcal remaining")).toBeInTheDocument();
  });
});
