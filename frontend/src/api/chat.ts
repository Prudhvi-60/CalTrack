import { apiClient } from "./client";

export type ChatRole = "user" | "assistant";

export type ChatHistoryItem = {
  role: ChatRole;
  content: string;
};

export type ToolTrace = {
  name: string;
  ok: boolean;
  summary: string;
};

export type ChatResponse = {
  reply: string;
  tools_used: ToolTrace[];
};

export async function sendChatMessage(message: string, history: ChatHistoryItem[]): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>(
    "/api/v1/chat",
    { message, history },
    { timeout: 60000 },
  );
  return data;
}
