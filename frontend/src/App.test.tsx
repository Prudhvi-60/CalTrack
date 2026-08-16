import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "@/App";
import { AuthProvider } from "@/contexts/AuthContext";

function renderApp(path = "/") {
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

describe("App shell", () => {
  it("redirects unauthenticated users to login", async () => {
    renderApp("/dashboard");
    expect(await screen.findByRole("heading", { name: "Sign in to CalTrack" })).toBeInTheDocument();
  });

  it("sends unknown routes through login when signed out", async () => {
    renderApp("/not-a-page");
    expect(await screen.findByRole("heading", { name: "Sign in to CalTrack" })).toBeInTheDocument();
  });
});
