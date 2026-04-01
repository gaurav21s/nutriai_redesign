"use client";

import { KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Check, ChevronDown, ChevronLeft, ChevronRight, Loader2, MessageSquare, Plus, Send, X } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useApiClient } from "@/hooks/useApiClient";
import { useConvexHistory } from "@/hooks/useConvexHistory";
import { cn } from "@/lib/cn";
import type {
  ChatMessage,
  ChatPendingAction,
  ChatReasoningStep,
  ChatSession,
  ChatStreamEvent,
} from "@/types/api";

function formatWhen(value: string): string {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function normalizeMessage(message: ChatMessage): ChatMessage {
  return {
    ...message,
    metadata: {
      reasoning_steps: message.metadata?.reasoning_steps ?? [],
      source_references: message.metadata?.source_references ?? [],
      pending_action: message.metadata?.pending_action ?? null,
    },
  };
}

function upsertStreamingAssistant(
  rows: ChatMessage[],
  assistantId: string,
  updater: (message: ChatMessage) => ChatMessage
): ChatMessage[] {
  return rows.map((row) => (row.id === assistantId ? updater(normalizeMessage(row)) : row));
}

function ReasoningPanel({
  steps,
  isStreaming,
}: {
  steps: ChatReasoningStep[];
  isStreaming: boolean;
}) {
  const [open, setOpen] = useState(isStreaming);

  useEffect(() => {
    if (isStreaming) setOpen(true);
    else setOpen(false);
  }, [isStreaming]);

  const latestLabel = steps[steps.length - 1]?.label;
  const summary = isStreaming
    ? latestLabel
      ? `Thinking · ${latestLabel}`
      : "Thinking..."
    : `Thought for ${steps.length} step${steps.length === 1 ? "" : "s"}`;

  return (
    <div className="rounded-[10px] border border-stone-200 bg-stone-50">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-sm text-stone-700"
      >
        <span className="flex items-center gap-2">
          {isStreaming ? (
            <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-stone-400" />
          ) : (
            <Check className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
          )}
          {summary}
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-stone-500 transition-transform duration-200", open && "rotate-180")} />
      </button>

      {open ? (
        <div className="border-t border-stone-200 px-3 py-3">
          {steps.length ? (
            <ol className="space-y-2">
              {steps.map((step) => (
                <li key={step.id} className="rounded-[8px] border border-stone-200 bg-white px-3 py-2">
                  <div className="flex items-center gap-2">
                    {step.status === "running" ? (
                      <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-stone-400" />
                    ) : step.status === "completed" ? (
                      <Check className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
                    ) : (
                      <span className="h-3.5 w-3.5 shrink-0" />
                    )}
                    <p className="text-sm font-medium text-stone-900">{step.label}</p>
                  </div>
                  <p className="mt-1 pl-[22px] text-sm leading-6 text-stone-600">{step.detail}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-stone-500">No visible reasoning steps for this message.</p>
          )}
        </div>
      ) : null}
    </div>
  );
}

function PendingActionCard({
  action,
  disabled,
  onConfirm,
  onReject,
}: {
  action: ChatPendingAction;
  disabled: boolean;
  onConfirm: () => void;
  onReject: () => void;
}) {
  const statusTone =
    action.status === "confirmed"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : action.status === "rejected"
        ? "border-rose-200 bg-rose-50 text-rose-700"
        : "border-amber-200 bg-amber-50 text-amber-800";

  return (
    <div className="rounded-[10px] border border-stone-200 bg-stone-50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-stone-900">{action.title}</p>
          <p className="mt-1 text-sm leading-6 text-stone-600">{action.summary}</p>
        </div>
        <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", statusTone)}>
          {action.status}
        </span>
      </div>

      {action.status === "pending" ? (
        <div className="mt-3 flex gap-2">
          <Button
            type="button"
            size="sm"
            className="rounded-[8px]"
            disabled={disabled}
            onClick={onConfirm}
          >
            <Check className="mr-2 h-4 w-4" />
            Save
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="rounded-[8px]"
            disabled={disabled}
            onClick={onReject}
          >
            <X className="mr-2 h-4 w-4" />
            Dismiss
          </Button>
        </div>
      ) : null}
    </div>
  );
}

function MessageItem({
  message,
  isStreaming,
  actionBusyId,
  onConfirmAction,
  onRejectAction,
}: {
  message: ChatMessage;
  isStreaming: boolean;
  actionBusyId: string | null;
  onConfirmAction: (action: ChatPendingAction) => void;
  onRejectAction: (action: ChatPendingAction) => void;
}) {
  const isAssistant = message.role === "assistant";
  const pendingAction = message.metadata?.pending_action;

  return (
    <div className={cn("flex", isAssistant ? "justify-start" : "justify-end")}>
      <article
        className={cn(
          "max-w-[780px] rounded-[12px] border px-4 py-3",
          isAssistant ? "border-stone-200 bg-white text-stone-900" : "border-stone-900 bg-stone-900 text-white"
        )}
      >
        <div className="flex items-center justify-between gap-3">
          <p className={cn("text-sm font-medium", isAssistant ? "text-stone-700" : "text-stone-200")}>
            {isAssistant ? "Nutri Agent" : "You"}
          </p>
          <span className={cn("text-xs", isAssistant ? "text-stone-500" : "text-stone-300")}>
            {formatWhen(message.created_at)}
          </span>
        </div>

        {isAssistant && ((message.metadata?.reasoning_steps?.length ?? 0) > 0 || isStreaming) ? (
          <div className="mt-3">
            <ReasoningPanel
              steps={message.metadata?.reasoning_steps ?? []}
              isStreaming={isStreaming}
            />
          </div>
        ) : null}

        {message.content ? (
          <div className="mt-3 whitespace-pre-wrap text-sm leading-7">{message.content}</div>
        ) : null}

        {isAssistant && message.metadata?.source_references?.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.metadata.source_references.map((source) => (
              <span
                key={`${source.feature}-${source.label}-${source.record_id ?? "none"}`}
                className="rounded-md border border-stone-200 bg-stone-50 px-2 py-1 text-xs text-stone-600"
              >
                {source.label}
              </span>
            ))}
          </div>
        ) : null}

        {isAssistant && pendingAction ? (
          <div className="mt-3">
            <PendingActionCard
              action={pendingAction}
              disabled={actionBusyId === pendingAction.action_id}
              onConfirm={() => onConfirmAction(pendingAction)}
              onReject={() => onRejectAction(pendingAction)}
            />
          </div>
        ) : null}
      </article>
    </div>
  );
}

export default function NutriChatPage() {
  const api = useApiClient();
  const { user } = useUser();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionBusyId, setActionBusyId] = useState<string | null>(null);
  const [streamingAssistantId, setStreamingAssistantId] = useState<string | null>(null);
  const [showSessions, setShowSessions] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!input && textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input]);

  const { data: sessions, loading: sessionsLoading, refreshInBackground } = useConvexHistory<ChatSession>({
    functionName: "chat:listSessions",
    clerkUserId: user?.id,
    limit: 30,
    pollIntervalMs: 12000,
  });

  const hasMessages = useMemo(() => messages.length > 0, [messages]);

  async function loadSession(targetSessionId: string) {
    setLoadingMessages(true);
    setError(null);
    try {
      const history = await api.listChatMessages(targetSessionId);
      setMessages(history.map(normalizeMessage));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load the chat session.");
    } finally {
      setLoadingMessages(false);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      if (!user?.id) return;
      const existing = await api.listChatSessions(1);
      const selected = existing[0] ?? (await api.createChatSession("Nutri Agent"));
      setSessionId(selected.session_id);
      await loadSession(selected.session_id);
      refreshInBackground();
    }

    void bootstrap();
  }, [api, refreshInBackground, user?.id]);

  async function handleCreateSession() {
    try {
      const created = await api.createChatSession("Nutri Agent");
      setSessionId(created.session_id);
      setMessages([]);
      refreshInBackground();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create a new chat session.");
    }
  }

  async function handleSend() {
    if (!sessionId || sending || !input.trim()) return;

    const outgoing = input.trim();
    const tempUserId = `temp-user-${Date.now()}`;
    const tempAssistantId = `temp-assistant-${Date.now()}`;
    let streamError: string | null = null;

    setSending(true);
    setError(null);
    setInput("");
    setStreamingAssistantId(tempAssistantId);

    setMessages((prev) => [
      ...prev,
      {
        id: tempUserId,
        role: "user",
        content: outgoing,
        created_at: new Date().toISOString(),
      },
      {
        id: tempAssistantId,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        metadata: {
          reasoning_steps: [],
          source_references: [],
          pending_action: null,
        },
      },
    ]);

    try {
      await api.streamChatTurn(sessionId, outgoing, {
        onEvent: (event: ChatStreamEvent) => {
          if (event.type === "context") return;

          if (event.type === "reasoning_step") {
            setMessages((prev) =>
              upsertStreamingAssistant(prev, tempAssistantId, (message) => ({
                ...message,
                metadata: {
                  reasoning_steps: [...(message.metadata?.reasoning_steps ?? []), event.data],
                  source_references: message.metadata?.source_references ?? [],
                  pending_action: message.metadata?.pending_action ?? null,
                },
              }))
            );
            return;
          }

          if (event.type === "assistant_delta") {
            setMessages((prev) =>
              upsertStreamingAssistant(prev, tempAssistantId, (message) => ({
                ...message,
                content: `${message.content}${event.data.delta}`,
              }))
            );
            return;
          }

          if (event.type === "pending_action") {
            setMessages((prev) =>
              upsertStreamingAssistant(prev, tempAssistantId, (message) => ({
                ...message,
                metadata: {
                  reasoning_steps: message.metadata?.reasoning_steps ?? [],
                  source_references: message.metadata?.source_references ?? [],
                  pending_action: event.data,
                },
              }))
            );
            return;
          }

          if (event.type === "message") {
            setMessages((prev) => prev.map((row) => (row.id === tempAssistantId ? normalizeMessage(event.data) : row)));
            return;
          }

          if (event.type === "error") {
            streamError = event.data.message;
          }
        },
      });

      if (streamError) {
        throw new Error(streamError);
      }

      await loadSession(sessionId);
      refreshInBackground();
    } catch (err) {
      setMessages((prev) => prev.filter((message) => message.id !== tempAssistantId && message.id !== tempUserId));
      setInput(outgoing);
      setError(err instanceof Error ? err.message : "Unable to send the message.");
    } finally {
      setStreamingAssistantId(null);
      setSending(false);
    }
  }

  async function handleConfirmAction(action: ChatPendingAction) {
    if (!sessionId) return;
    setActionBusyId(action.action_id);
    try {
      await api.confirmChatAction(sessionId, action.action_id);
      await loadSession(sessionId);
      refreshInBackground();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save that result.");
    } finally {
      setActionBusyId(null);
    }
  }

  async function handleRejectAction(action: ChatPendingAction) {
    if (!sessionId) return;
    setActionBusyId(action.action_id);
    try {
      await api.rejectChatAction(sessionId, action.action_id);
      await loadSession(sessionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to dismiss that action.");
    } finally {
      setActionBusyId(null);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  }

  return (
    <div className="space-y-6 pt-6">
      <header className="border-b border-stone-200 pb-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-display"><span className="text-foreground">Nutri</span> <span className="text-vibrant">Agent</span></h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-stone-600">
              Ask nutrition questions using NutriAI history as context; expand reasoning when needed.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            className="rounded-[8px]"
            onClick={() => setShowSessions((current) => !current)}
          >
            {showSessions ? <ChevronLeft className="mr-2 h-4 w-4" /> : <ChevronRight className="mr-2 h-4 w-4" />}
            {showSessions ? "Hide sessions" : "Show sessions"}
          </Button>
        </div>
      </header>

      <div className={cn("grid gap-4", showSessions ? "xl:grid-cols-[260px_minmax(0,1fr)]" : "grid-cols-1")}>
        {showSessions ? (
          <aside className="rounded-[12px] border border-stone-200 bg-white">
            <div className="flex items-center justify-between border-b border-stone-200 px-4 py-4">
              <div>
                <h2 className="text-base font-medium text-stone-900">Sessions</h2>
                <p className="text-sm text-stone-500">Recent chats</p>
              </div>
              <Button
                type="button"
                size="icon"
                variant="outline"
                className="h-9 w-9 rounded-[8px]"
                onClick={() => void handleCreateSession()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="max-h-[720px] space-y-1 overflow-y-auto p-2">
              {sessionsLoading ? (
                <div className="px-3 py-4 text-sm text-stone-500">Loading sessions...</div>
              ) : sessions.length ? (
                sessions.map((session) => (
                  <button
                    key={session.session_id}
                    type="button"
                    onClick={() => {
                      setSessionId(session.session_id);
                      void loadSession(session.session_id);
                    }}
                    className={cn(
                      "w-full rounded-[10px] border px-3 py-3 text-left transition-colors",
                      sessionId === session.session_id
                        ? "border-stone-900 bg-stone-900 text-white"
                        : "border-transparent text-stone-700 hover:border-stone-200 hover:bg-stone-50"
                    )}
                  >
                    <p className="truncate text-sm font-medium">{session.title}</p>
                    <p className={cn("mt-1 text-xs", sessionId === session.session_id ? "text-stone-300" : "text-stone-500")}>
                      {formatWhen(session.last_message_at ?? session.created_at)}
                    </p>
                  </button>
                ))
              ) : (
                <div className="px-3 py-4 text-sm text-stone-500">No sessions yet.</div>
              )}
            </div>
          </aside>
        ) : null}

        <section className="relative overflow-hidden rounded-[20px] border border-stone-200 bg-white shadow-[0_18px_45px_rgba(15,23,42,0.05)]">
          <div className="flex h-[calc(100vh-260px)] min-h-[520px] flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5 pb-28">
              {loadingMessages ? (
                <div className="text-sm text-stone-500">Loading messages...</div>
              ) : hasMessages ? (
                messages.map((message) => (
                  <MessageItem
                    key={message.id}
                    message={normalizeMessage(message)}
                    isStreaming={streamingAssistantId === message.id}
                    actionBusyId={actionBusyId}
                    onConfirmAction={(action) => void handleConfirmAction(action)}
                    onRejectAction={(action) => void handleRejectAction(action)}
                  />
                ))
              ) : (
                <div className="flex h-full min-h-[360px] flex-col items-center justify-center rounded-[10px] border border-dashed border-stone-200 bg-stone-50 px-6 text-center">
                  <MessageSquare className="h-10 w-10 text-stone-400" />
                  <p className="mt-4 text-base font-medium text-stone-800">Start a conversation</p>
                  <p className="mt-2 max-w-md text-sm leading-6 text-stone-500">
                    Ask a question, request a calculator preview, or let the agent use your saved NutriAI history to answer with more context.
                  </p>
                </div>
              )}
            </div>

            <div className="pointer-events-none absolute inset-x-0 bottom-5 flex justify-center px-6">
              <div className="pointer-events-auto flex w-full max-w-2xl items-center gap-2 rounded-[28px] border border-stone-200 bg-white/96 px-4 py-3 shadow-[0_8px_32px_rgba(15,23,42,0.10)] backdrop-blur">
                <textarea
                  ref={textareaRef}
                  id="chat-input"
                  rows={1}
                  value={input}
                  onChange={(event) => {
                    setInput(event.target.value);
                    event.target.style.height = "auto";
                    event.target.style.height = Math.min(event.target.scrollHeight, 192) + "px";
                  }}
                  onKeyDown={handleComposerKeyDown}
                  placeholder="Ask about meals, habits, BMI, calories..."
                  className="flex-1 resize-none bg-transparent text-sm leading-6 text-stone-900 outline-none placeholder:text-stone-400 overflow-y-auto"
                  style={{ minHeight: "24px", maxHeight: "192px" }}
                />
                <Button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={sending || !input.trim() || !sessionId}
                  size="icon"
                  className="h-8 w-8 flex-shrink-0 rounded-full"
                >
                  {sending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>
          </div>
        </section>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}
    </div>
  );
}
