import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Goals } from "@/pages/Goals";
import { listGoals } from "@/api/goals";

vi.mock("@/api/goals", () => ({
  listGoals: vi.fn(),
  createGoal: vi.fn(),
  replaceGoal: vi.fn(),
  patchGoal: vi.fn(),
  deleteGoal: vi.fn(),
}));

function renderGoals() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <Goals />
    </QueryClientProvider>,
  );
}

describe("Goals form", () => {
  it("rejects negative calorie targets", async () => {
    vi.mocked(listGoals).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
    const user = userEvent.setup();
    renderGoals();
    expect(await screen.findByRole("heading", { name: "Goals" })).toBeInTheDocument();
    const calories = screen.getByLabelText("Daily calories (kcal)");
    await user.clear(calories);
    await user.type(calories, "-10");
    await user.click(screen.getByRole("button", { name: "Save goals" }));
    expect(await screen.findByText("Must be 0 or greater")).toBeInTheDocument();
  });
});
