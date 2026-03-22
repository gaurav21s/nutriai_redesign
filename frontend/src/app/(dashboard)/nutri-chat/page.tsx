"use client";

import { FormEvent, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Send, MessageSquare, Clock } from "lucide-react";

import { FeatureShell } from "@/components/features/feature-shell";
import { HistoryPanel } from "@/components/features/history-panel";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
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
      description="Ask nutrition questions and get clear answers in real time."
      aside={
        <HistoryPanel title="Active Sessions" loading={sessionsLoading} empty={!sessions.length} syncing={sendAction.loading}>
          {sessions.map((session) => (
            <button
              key={session.session_id}
              className={`w-full rounded-editorial border p-4 text-left transition-all shadow-soft-glow group mb-3 last:mb-0 ${sessionId === session.session_id ? "border-vibrant/30 bg-vibrant/5 text-vibrant" : "border-black/[0.03] bg-white/40 text-foreground/60 hover:border-vibrant/20"
                }`}
              onClick={async () => {
                setSessionId(session.session_id);
                const history = await api.listChatMessages(session.session_id);
                setMessages(history);
              }}
            >
              <div className="flex items-center gap-3 mb-2">
                <MessageSquare className={`h-3.5 w-3.5 ${sessionId === session.session_id ? "text-vibrant" : "text-foreground/20 group-hover:text-vibrant transition-colors"}`} />
                <p className="text-sm font-semibold truncate transition-colors">{session.title}</p>
              </div>
              <p className={`text-[10px] font-bold uppercase tracking-widest ${sessionId === session.session_id ? "text-vibrant/60" : "text-foreground/20 italic"}`}>
                {new Date(session.created_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </HistoryPanel>
      }
    >
      <div className="space-y-6">
        <div className="h-[500px] flex flex-col rounded-editorial border border-black/[0.03] bg-black/[0.01] overflow-hidden shadow-elegant">
          <div className="flex-1 space-y-4 overflow-y-auto p-8 scrollbar-elegant">
            {messages.length ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`max-w-[80%] rounded-editorial px-6 py-4 text-sm font-medium leading-relaxed relative group animate-reveal ${message.role === "assistant"
                      ? "bg-white/80 border border-black/[0.02] text-foreground/80 shadow-soft-glow self-start"
                      : "ml-auto bg-vibrant text-white shadow-soft-glow self-end"
                    }`}
                >
                  {message.role === "assistant" && (
                    <div className="absolute -left-2 top-4 w-1 h-8 bg-vibrant/40 opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                  {message.content}
                </div>
              ))
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-12 opacity-30 italic">
                <MessageSquare className="h-12 w-12 mb-6 text-vibrant" />
                <p className="text-lg">Start a chat to get nutrition guidance.</p>
              </div>
            )}
          </div>

          <div className="p-6 bg-white/40 border-t border-black/[0.03]">
            <form className="flex gap-4 items-end" onSubmit={handleSend}>
              <div className="flex-1 space-y-2">
                <FieldLabel htmlFor="chat-question" className="sr-only">Inquire</FieldLabel>
                <Input
                  id="chat-question"
                  placeholder="Ask a nutrition question..."
                  className="h-14 bg-white/60 border-black/[0.05] focus:border-vibrant rounded-full px-8 transition-all shadow-sm"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                />
              </div>
              <Button
                type="submit"
                size="icon"
                className="h-14 w-14 rounded-full bg-vibrant hover:bg-vibrant/90 text-white shadow-soft-glow transition-all active:scale-95"
                disabled={sendAction.loading || !input.trim()}
              >
                {sendAction.loading ? (
                  <Clock className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </form>
          </div>
        </div>

        {sendAction.error ? <Alert variant="error" className="rounded-2xl border-vibrant/20 bg-vibrant/5 text-vibrant">{sendAction.error}</Alert> : null}
      </div>
    </FeatureShell>
  );
}
