import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Meals } from "@/pages/Meals";
import { listMeals } from "@/api/meals";

vi.mock("@/api/meals", () => ({
  listMeals: vi.fn(),
  createMeal: vi.fn(),
  getMeal: vi.fn(),
  replaceMeal: vi.fn(),
  deleteMeal: vi.fn(),
}));

function renderMeals() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Meals />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Meals filters", () => {
  it("applies search and meal type to the meals API", async () => {
    vi.mocked(listMeals).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
    const user = userEvent.setup();
    renderMeals();
    expect(await screen.findByRole("heading", { name: "Meals" })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Meal type"), "BREAKFAST");
    await user.type(screen.getByLabelText("Search food"), "oatmeal");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => {
      const last = vi.mocked(listMeals).mock.calls.at(-1)?.[0];
      expect(last).toMatchObject({ meal_type: "BREAKFAST", q: "oatmeal", page: 1 });
    });
  });
});
