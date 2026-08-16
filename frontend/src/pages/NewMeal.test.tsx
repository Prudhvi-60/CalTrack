import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NewMeal } from "@/pages/NewMeal";

vi.mock("@/api/meals", () => ({
  createMeal: vi.fn(),
  listMeals: vi.fn(),
  getMeal: vi.fn(),
  replaceMeal: vi.fn(),
  deleteMeal: vi.fn(),
}));

function renderNewMeal() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <NewMeal />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("New meal form", () => {
  it("requires a food name and rejects negative calories", async () => {
    const user = userEvent.setup();
    renderNewMeal();
    expect(await screen.findByRole("heading", { name: "New meal" })).toBeInTheDocument();
    const calories = screen.getByLabelText("Calories");
    await user.clear(calories);
    await user.type(calories, "-20");
    await user.click(screen.getByRole("button", { name: "Save meal" }));
    expect(await screen.findByText("Food name is required")).toBeInTheDocument();
    expect(screen.getByText("Must be 0 or greater")).toBeInTheDocument();
  });
});
