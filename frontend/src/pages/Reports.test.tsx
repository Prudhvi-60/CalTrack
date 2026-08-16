import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Reports } from "@/pages/Reports";

vi.mock("@/hooks/useNutrition", () => ({
  useNutritionTrends: () => ({
    isLoading: false,
    error: null,
    data: {
      items: [{ date: "2026-08-15", calories: 1875, protein: 116, carbohydrates: 183, fat: 72 }],
      page: 1,
      page_size: 7,
      total: 7,
      total_pages: 1,
      start_date: "2026-08-09",
      end_date: "2026-08-15",
      totals: { calories: 12375, protein: 800, carbohydrates: 1200, fat: 400, fiber: 0, sugar: 0 },
    },
  }),
  useGoalComparison: () => ({
    isLoading: false,
    error: null,
    data: {
      date: "2026-08-15",
      start_date: "2026-08-09",
      end_date: "2026-08-15",
      days: 7,
      has_goals: true,
      items: [
        { name: "calories", label: "Calories", unit: "kcal", actual: 12375, target: 15400, remaining: 3025, percent: 80 },
      ],
    },
  }),
  useMicronutrients: () => ({
    isLoading: false,
    error: null,
    data: {
      items: [{ nutrient_name: "Iron", amount: 12, unit: "mg" }],
      page: 1,
      page_size: 50,
      total: 1,
      total_pages: 1,
      start_date: "2026-08-09",
      end_date: "2026-08-15",
    },
  }),
}));

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

vi.stubGlobal("ResizeObserver", ResizeObserverMock);

function renderReports() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Reports />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Reports", () => {
  it("renders report charts and range controls", async () => {
    const user = userEvent.setup();
    renderReports();
    expect(await screen.findByRole("heading", { name: "Reports" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Calories" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Protein, carbs, and fat" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Macronutrients" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Macro distribution" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Goal vs actual" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Micronutrients" })).toBeInTheDocument();
    expect(screen.getByText("Iron")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "30 days" }));
    expect(screen.getByRole("button", { name: "30 days" })).toBeInTheDocument();
  });
});
