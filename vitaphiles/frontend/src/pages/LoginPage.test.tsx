import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "@/App";
import { AuthProvider } from "@/contexts/AuthContext";

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    refreshAccessToken: vi.fn().mockResolvedValue(null),
  };
});

function renderAt(path: string) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Login", () => {
  it("shows validation errors for empty fields", async () => {
    const user = userEvent.setup();
    renderAt("/login");
    await user.click(await screen.findByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Enter a valid email")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
  });
});

describe("Register", () => {
  it("shows validation errors for short passwords", async () => {
    const user = userEvent.setup();
    renderAt("/register");
    await user.type(await screen.findByLabelText("Display name"), "Ada");
    await user.type(screen.getByLabelText("Username"), "ada_lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@vitaphiles.test");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText("Password must be at least 8 characters")).toBeInTheDocument();
  });
});
