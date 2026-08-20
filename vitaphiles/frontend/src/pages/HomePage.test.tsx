import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "./HomePage";
import { AuthProvider } from "@/contexts/AuthContext";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    api: {
      get: vi.fn().mockRejectedValue(new Error("offline")),
    },
    refreshAccessToken: vi.fn().mockResolvedValue(null),
  };
});

function renderHome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AuthProvider>
          <HomePage />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  it("shows the product promise", async () => {
    renderHome();
    expect(await screen.findByRole("heading", { name: /stories worth remembering/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore books/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore movies/i })).toBeInTheDocument();
  });
});
