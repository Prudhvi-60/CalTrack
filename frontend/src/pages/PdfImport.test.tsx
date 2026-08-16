import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PdfImport } from "@/pages/PdfImport";
import { previewMealPlan } from "@/api/importPdf";

vi.mock("@/api/importPdf", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/importPdf")>();
  return {
    ...actual,
    previewMealPlan: vi.fn(),
    confirmMealPlan: vi.fn(),
  };
});

describe("PDF import", () => {
  it("rejects non-PDF files client-side", async () => {
    render(
      <MemoryRouter>
        <PdfImport />
      </MemoryRouter>,
    );
    const input = await screen.findByLabelText("Upload your meal plan or food diary PDF");
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(await screen.findByText("Upload a PDF file.")).toBeInTheDocument();
    expect(previewMealPlan).not.toHaveBeenCalled();
  });
});
