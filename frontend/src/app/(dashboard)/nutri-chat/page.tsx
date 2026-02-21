"use client";

import { FormEvent, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApiClient } from "@/hooks/useApiClient";
import { useAsyncAction } from "@/hooks/useAsyncAction";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import type { ChatMessage, ChatSession } from "@/types/api";

export default function NutriChatPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const { data: sessions, loading: sessionsLoading, refreshInBackground } = useConvexHistory<ChatSession>({
    functionName: "chat:listSessions",
    clerkUserId: user?.id,
    limit: 30,
    pollIntervalMs: 12000,
  });

  const sendAction = useAsyncAction(async () => {
    if (!sessionId) throw new Error("No active session");
    if (!input.trim()) throw new Error("Please enter a message");
    const response = await api.sendChatMessage(sessionId, input.trim());
    return response;
  });

  useEffect(() => {
    async function bootstrap() {
      const existing = await api.listChatSessions(1);
      const selected = existing[0] ?? (await api.createChatSession("Nutrition Chat"));
      setSessionId(selected.session_id);
      const history = await api.listChatMessages(selected.session_id);
      setMessages(history);
      refreshInBackground();
    }

    void bootstrap();
  }, [api, refreshInBackground]);

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const copy = input;
    setInput("");

    const assistant = await sendAction.execute();
    if (!assistant) {
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id));
      setInput(copy);
      return;
    }

    setMessages((prev) => [...prev.filter((msg) => msg.id !== userMessage.id), userMessage, assistant]);
    refreshInBackground();
  }

  return (
    <FeatureShell
      title="Nutri Chat"
      description="Ask nutrition questions with persistent sessions and contextual responses."
      aside={
        <HistoryPanel title="Recent Sessions" loading={sessionsLoading} empty={!sessions.length} syncing={sendAction.loading}>
          {sessions.map((session) => (
            <button
              key={session.session_id}
              className="w-full rounded-xl border border-surface-200 bg-surface-50 p-3 text-left"
              onClick={async () => {
                setSessionId(session.session_id);
                const history = await api.listChatMessages(session.session_id);
                setMessages(history);
              }}
            >
              <p className="text-sm font-semibold text-accent-800">{session.title}</p>
              <p className="mt-1 text-xs text-accent-600">{new Date(session.created_at).toLocaleString()}</p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-4">
        <div className="max-h-[460px] space-y-3 overflow-y-auto rounded-2xl border border-surface-200 bg-white p-4">
          {messages.length ? (
            messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                  message.role === "assistant"
                    ? "bg-accent-100 text-accent-800"
                    : "ml-auto bg-brand-200 text-accent-900"
                }`}
              >
                {message.content}
              </div>
            ))
          ) : (
            <p className="text-sm text-accent-500">Start a conversation to get personalized nutrition guidance.</p>
          )}
        </div>

        <form className="flex gap-3" onSubmit={handleSend}>
          <Input
            placeholder="Ask a nutrition question"
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />
          <Button type="submit" disabled={sendAction.loading}>
            {sendAction.loading ? "Sending..." : "Send"}
          </Button>
        </form>

        {sendAction.error ? <Alert variant="error">{sendAction.error}</Alert> : null}
      </div>
    </FeatureShell>
  );
}
