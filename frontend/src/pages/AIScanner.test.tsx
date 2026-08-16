import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AIScanner } from "@/pages/AIScanner";
import { analyzeFoodImage, recordAiCorrections } from "@/api/ai";
import { createMeal } from "@/api/meals";
import type { Meal } from "@/types/meal";

vi.mock("@/api/ai", () => ({
  analyzeFoodImage: vi.fn(),
  recordAiCorrections: vi.fn(),
}));

vi.mock("@/api/meals", () => ({
  createMeal: vi.fn(),
  listMeals: vi.fn(),
  getMeal: vi.fn(),
  replaceMeal: vi.fn(),
  deleteMeal: vi.fn(),
}));

beforeAll(() => {
  URL.createObjectURL = URL.createObjectURL ?? (() => "blob:preview");
  URL.revokeObjectURL = URL.revokeObjectURL ?? (() => undefined);
});

function renderScanner() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AIScanner />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AI scanner", () => {
  it("rejects unsupported files client-side", async () => {
    renderScanner();
    const input = await screen.findByLabelText("Image");
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(await screen.findByText("Use a JPEG, PNG, or WEBP image.")).toBeInTheDocument();
    expect(analyzeFoodImage).not.toHaveBeenCalled();
  });

  it("shows review before any meal is created", async () => {
    vi.mocked(analyzeFoodImage).mockResolvedValue({
      analysis_type: "food",
      food_items: [
        {
          name: "rice",
          quantity: 1,
          unit: "cup",
          calories: 205,
          protein: 4.3,
          carbohydrates: 44.5,
          fat: 0.4,
          fiber: 0.6,
          sugar: 0,
          nutrition_source: "llm",
          confidence: 0.87,
          confidence_level: "HIGH",
          estimated_weight_g: 158,
          micronutrients: [],
        },
      ],
      confidence: 0.87,
      notes: "Estimated from visible portion size.",
      warnings: ["AI nutrition values are estimates and must be reviewed before saving."],
    });
    const user = userEvent.setup();
    renderScanner();
    const input = await screen.findByLabelText("Image");
    const file = new File(["png"], "food.png", { type: "image/png" });
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Analyze Food" }));
    expect(await screen.findByRole("heading", { name: "Review and confirm" })).toBeInTheDocument();
    expect(screen.getByText(/Estimated nutrition \(AI\)/)).toBeInTheDocument();
    expect(screen.getByDisplayValue("rice")).toBeInTheDocument();
    expect(createMeal).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Confirm and save meal" })).toBeInTheDocument();
    vi.mocked(createMeal).mockResolvedValue({
      id: 1,
      user_id: 1,
      meal_type: "SNACK",
      consumed_at: "2026-08-15T12:00:00.000Z",
      notes: null,
      food_entries: [],
      totals: { calories: 205, protein: 4.3, carbohydrates: 44.5, fat: 0.4, fiber: 0.6, sugar: 0 },
      created_at: "2026-08-15T12:00:00.000Z",
      updated_at: "2026-08-15T12:00:00.000Z",
    } satisfies Meal);
    await user.click(screen.getByRole("button", { name: "Confirm and save meal" }));
    await waitFor(() => expect(createMeal).toHaveBeenCalledTimes(1));
    expect(recordAiCorrections).toHaveBeenCalled();
  });
});
