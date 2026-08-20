import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "./HomePage";

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn().mockRejectedValue(new Error("offline")),
  },
}));

function renderHome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  it("shows the product promise", () => {
    renderHome();
    expect(screen.getByRole("heading", { name: /stories worth remembering/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore books/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore movies/i })).toBeInTheDocument();
  });
});
