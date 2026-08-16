import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Chat } from "@/pages/Chat";
import { sendChatMessage } from "@/api/chat";

vi.mock("@/api/chat", () => ({
  sendChatMessage: vi.fn(),
}));

describe("Chat", () => {
  it("shows the assistant reply and does not send an empty message", async () => {
    vi.mocked(sendChatMessage).mockResolvedValue({
      reply: "You have 350 kcal left today.",
      tools_used: [{ name: "get_today_nutrition", ok: true, summary: "get_today_nutrition: 1850 kcal" }],
    });
    const user = userEvent.setup();
    render(<Chat />);
    expect(screen.getByRole("heading", { name: "Nutrition assistant" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(sendChatMessage).not.toHaveBeenCalled();
    await user.type(screen.getByLabelText("Message"), "How many calories do I have left?");
    await user.click(screen.getByRole("button", { name: "Send" }));
    expect(await screen.findByText("You have 350 kcal left today.")).toBeInTheDocument();
    await waitFor(() => expect(sendChatMessage).toHaveBeenCalledTimes(1));
  });
});
