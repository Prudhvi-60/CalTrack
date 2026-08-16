import { FormEvent, useState } from "react";
import { sendChatMessage, type ChatHistoryItem, type ToolTrace } from "@/api/chat";
import { getApiErrorMessage } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { usePageTitle } from "@/hooks/usePageTitle";
import { cn } from "@/utils/cn";

type Bubble = ChatHistoryItem & { tools?: ToolTrace[] };

export function Chat() {
  usePageTitle("Chat");
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || pending) {
      return;
    }
    setDraft("");
    setError(null);
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: "user", content: text }]);
    setPending(true);
    try {
      const result = await sendChatMessage(text, history);
      setMessages((current) => [...current, { role: "assistant", content: result.reply, tools: result.tools_used }]);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not send message"));
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="mx-auto flex max-w-3xl flex-col space-y-6">
      <PageHeader
        title="Nutrition assistant"
        description="A personal nutrition companion for today’s meals, remaining calories, and weekly totals. Photos belong on AI Scan."
      />
      {messages.length === 0 && (
        <EmptyState title="Ask your nutrition assistant">
          Try “What did I eat today?”, “How many calories do I have left?”, or “Log 2 eggs for breakfast.”
        </EmptyState>
      )}
      <div className="space-y-3" aria-live="polite">
        {messages.map((item, index) => (
          <article
            key={`${item.role}-${index}`}
            className={cn(
              "max-w-[92%] rounded-[16px] border border-border p-4 text-sm leading-relaxed",
              item.role === "user" ? "ml-auto bg-primary-soft" : "mr-auto bg-card shadow-[0_4px_18px_rgba(36,92,74,0.06)]",
            )}
          >
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {item.role === "user" ? "You" : "Assistant"}
            </p>
            <p className="mt-1 whitespace-pre-wrap text-foreground">{item.content}</p>
            {item.tools && item.tools.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-xs text-muted-foreground">
                {item.tools.map((tool) => (
                  <li key={`${tool.name}-${tool.summary}`}>{tool.summary}</li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
      {error && <ErrorAlert message={error} />}
      <form className="surface-card flex flex-col gap-3 p-3 sm:flex-row sm:items-end" onSubmit={onSubmit}>
        <label className="sr-only" htmlFor="chat-message">
          Message
        </label>
        <textarea
          id="chat-message"
          rows={2}
          className="w-full rounded-[11px] border border-input bg-card px-3 py-2 text-sm transition-colors duration-200 ease-out focus-visible:border-sage focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about your nutrition…"
        />
        <Button type="submit" disabled={pending || !draft.trim()} aria-busy={pending} className="sm:self-stretch">
          {pending ? "Thinking…" : "Send"}
        </Button>
      </form>
    </section>
  );
}
