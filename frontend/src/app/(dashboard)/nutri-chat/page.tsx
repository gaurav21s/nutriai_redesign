"use client";

import { KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";
import { Check, ChevronDown, ChevronLeft, ChevronRight, Loader2, MessageSquare, Pencil, Plus, Send, Trash2, X } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useApiClient } from "@/hooks/useApiClient";
import { cn } from "@/lib/cn";
import { captureEvent } from "@/lib/posthog";
import { emitFrontendTelemetry } from "@/lib/telemetry";
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
  const [showSessions, setShowSessions] = useState(false);
  const [sessionItems, setSessionItems] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [sessionTitleDraft, setSessionTitleDraft] = useState("");
  const [sessionBusyId, setSessionBusyId] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!input && textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input]);

  const hasMessages = useMemo(() => messages.length > 0, [messages]);
  const activeSession = useMemo(
    () => sessionItems.find((session) => session.session_id === sessionId) ?? null,
    [sessionId, sessionItems]
  );

  const loadSessions = useCallback(
    async (options: { silent?: boolean } = {}) => {
      const { silent = false } = options;
      if (!silent) {
        setSessionsLoading(true);
      }

      try {
        const nextSessions = await api.listChatSessions(30);
        setSessionItems(nextSessions);
        return nextSessions;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load chat sessions.");
        return [];
      } finally {
        if (!silent) {
          setSessionsLoading(false);
        }
      }
    },
    [api]
  );

  const loadSession = useCallback(async (targetSessionId: string) => {
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
  }, [api]);

  const selectSession = useCallback(async (targetSessionId: string) => {
    setEditingSessionId(null);
    setSessionId(targetSessionId);
    await loadSession(targetSessionId);
  }, [loadSession]);

  useEffect(() => {
    async function bootstrap() {
      if (!user?.id) return;
      try {
        const existing = await loadSessions();
        const selected = existing[0] ?? (await api.createChatSession("Nutri Agent"));
        if (!existing.length) {
          setSessionItems([selected]);
        }
        await selectSession(selected.session_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load your chat sessions.");
        setSessionsLoading(false);
      }
    }

    void bootstrap();
  }, [api, loadSessions, selectSession, user?.id]);

  useEffect(() => {
    if (!user?.id) return;

    const timer = window.setInterval(() => {
      void loadSessions({ silent: true });
    }, 12000);

    return () => window.clearInterval(timer);
  }, [loadSessions, user?.id]);

  async function handleCreateSession() {
    try {
      const created = await api.createChatSession("Nutri Agent");
      setSessionItems((prev) => [created, ...prev.filter((session) => session.session_id !== created.session_id)]);
      setEditingSessionId(null);
      await selectSession(created.session_id);
      await loadSessions({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create a new chat session.");
    }
  }

  function beginRenameSession(session: ChatSession) {
    setEditingSessionId(session.session_id);
    setSessionTitleDraft(session.title);
    setError(null);
  }

  function cancelRenameSession() {
    setEditingSessionId(null);
    setSessionTitleDraft("");
  }

  async function handleRenameSession(targetSessionId: string) {
    const nextTitle = sessionTitleDraft.trim();
    if (!nextTitle) {
      setError("Session title cannot be empty.");
      return;
    }

    setSessionBusyId(targetSessionId);
    setError(null);
    try {
      const updated = await api.renameChatSession(targetSessionId, nextTitle);
      setSessionItems((prev) =>
        prev.map((session) => (session.session_id === targetSessionId ? updated : session))
      );
      captureEvent("chat_session_renamed", {
        feature: "nutri_chat",
        session_id: targetSessionId,
        title_length: nextTitle.length,
      });
      void emitFrontendTelemetry(
        {
          event_type: "chat_session_renamed",
          category: "workflow",
          feature: "nutri_chat",
          status: "completed",
          properties: {
            session_id: targetSessionId,
            title_length: nextTitle.length,
          },
        },
        {
          clerk_user_id: user?.id,
          email: user?.primaryEmailAddress?.emailAddress,
        }
      );
      cancelRenameSession();
      await loadSessions({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to rename this session.");
    } finally {
      setSessionBusyId(null);
    }
  }

  async function handleDeleteSession(targetSessionId: string) {
    if (!window.confirm("Delete this chat session? This removes that conversation history for good.")) {
      return;
    }

    const deletingCurrentSession = targetSessionId === sessionId;
    setSessionBusyId(targetSessionId);
    setError(null);

    try {
      await api.deleteChatSession(targetSessionId);
      setSessionItems((prev) => prev.filter((session) => session.session_id !== targetSessionId));
      captureEvent("chat_session_deleted", {
        feature: "nutri_chat",
        session_id: targetSessionId,
      });
      void emitFrontendTelemetry(
        {
          event_type: "chat_session_deleted",
          category: "workflow",
          feature: "nutri_chat",
          status: "completed",
          properties: {
            session_id: targetSessionId,
          },
        },
        {
          clerk_user_id: user?.id,
          email: user?.primaryEmailAddress?.emailAddress,
        }
      );
      if (editingSessionId === targetSessionId) {
        cancelRenameSession();
      }

      const remaining = await loadSessions({ silent: true });

      if (!deletingCurrentSession) {
        return;
      }

      const replacement = remaining[0] ?? null;
      if (replacement) {
        await selectSession(replacement.session_id);
        return;
      }

      const created = await api.createChatSession("Nutri Agent");
      setMessages([]);
      setSessionItems([created]);
      await selectSession(created.session_id);
      await loadSessions({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete this session.");
    } finally {
      setSessionBusyId(null);
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
              upsertStreamingAssistant(prev, tempAssistantId, (message) => {
                const existing = message.metadata?.reasoning_steps ?? [];
                const idx = existing.findIndex((s) => s.id === event.data.id);
                const updatedSteps = idx >= 0
                  ? existing.map((s, i) => (i === idx ? event.data : s))
                  : [...existing, event.data];
                return {
                  ...message,
                  metadata: {
                    reasoning_steps: updatedSteps,
                    source_references: message.metadata?.source_references ?? [],
                    pending_action: message.metadata?.pending_action ?? null,
                  },
                };
              })
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
      await loadSessions({ silent: true });
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
      await loadSessions({ silent: true });
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

      <div className={cn("grid gap-4", showSessions ? "xl:grid-cols-[300px_minmax(0,1fr)]" : "grid-cols-1")}>
        {showSessions ? (
          <aside className="rounded-[14px] border border-stone-200 bg-white">
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
              ) : sessionItems.length ? (
                sessionItems.map((session) => (
                  <div
                    key={session.session_id}
                    className={cn(
                      "group rounded-[10px] border transition-colors",
                      sessionId === session.session_id
                        ? "border-stone-900 bg-stone-900 text-white"
                        : "border-transparent text-stone-700 hover:border-stone-200 hover:bg-stone-50"
                    )}
                  >
                    {editingSessionId === session.session_id ? (
                      <div className="space-y-3 p-3">
                        <input
                          autoFocus
                          value={sessionTitleDraft}
                          onChange={(event) => setSessionTitleDraft(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter") {
                              event.preventDefault();
                              void handleRenameSession(session.session_id);
                            }
                            if (event.key === "Escape") {
                              cancelRenameSession();
                            }
                          }}
                          className="w-full rounded-[8px] border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 outline-none ring-0 focus:border-stone-500"
                          placeholder="Session title"
                        />
                        <div className="flex gap-2">
                          <Button
                            type="button"
                            size="sm"
                            className="rounded-[8px]"
                            disabled={sessionBusyId === session.session_id}
                            onClick={() => void handleRenameSession(session.session_id)}
                          >
                            {sessionBusyId === session.session_id ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            Save
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            className="rounded-[8px]"
                            disabled={sessionBusyId === session.session_id}
                            onClick={cancelRenameSession}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start gap-2 p-3">
                        <button
                          type="button"
                          className="min-w-0 flex-1 text-left"
                          onClick={() => void selectSession(session.session_id)}
                        >
                          <p className="truncate text-sm font-medium">{session.title}</p>
                          <p
                            className={cn(
                              "mt-1 text-xs",
                              sessionId === session.session_id ? "text-stone-300" : "text-stone-500"
                            )}
                          >
                            {formatWhen(session.last_message_at ?? session.created_at)}
                          </p>
                        </button>
                        <div className="flex shrink-0 gap-1 opacity-100 transition-opacity xl:opacity-0 xl:group-hover:opacity-100 xl:group-focus-within:opacity-100">
                          <button
                            type="button"
                            aria-label={`Rename ${session.title}`}
                            className={cn(
                              "inline-flex h-8 w-8 items-center justify-center rounded-[8px] transition-colors",
                              sessionId === session.session_id
                                ? "text-stone-300 hover:bg-white/10 hover:text-white"
                                : "text-stone-500 hover:bg-stone-100 hover:text-stone-900"
                            )}
                            onClick={(event) => {
                              event.stopPropagation();
                              beginRenameSession(session);
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            aria-label={`Delete ${session.title}`}
                            disabled={sessionBusyId === session.session_id}
                            className={cn(
                              "inline-flex h-8 w-8 items-center justify-center rounded-[8px] transition-colors disabled:opacity-50",
                              sessionId === session.session_id
                                ? "text-stone-300 hover:bg-white/10 hover:text-white"
                                : "text-stone-500 hover:bg-red-50 hover:text-red-600"
                            )}
                            onClick={(event) => {
                              event.stopPropagation();
                              void handleDeleteSession(session.session_id);
                            }}
                          >
                            {sessionBusyId === session.session_id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Trash2 className="h-3.5 w-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="px-3 py-4 text-sm text-stone-500">No sessions yet.</div>
              )}
            </div>
          </aside>
        ) : null}

        <section className="relative overflow-hidden rounded-[16px] border border-stone-200 bg-white shadow-[0_18px_45px_rgba(15,23,42,0.05)]">
          <div className="flex h-[calc(100vh-260px)] min-h-[520px] flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5 pb-36">
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

            {/* Floating pill input bar — anchored to bottom of chat section */}
            <div className="absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-white from-80% to-transparent px-5 pb-3 pt-8">
              <div className="mx-auto w-full max-w-3xl">
                <div className="flex items-center gap-3 rounded-full border border-stone-200 bg-white py-2 pl-5 pr-2 shadow-[0_4px_24px_rgba(0,0,0,0.08)]">
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
                    className="flex-1 resize-none overflow-y-auto bg-transparent text-sm leading-6 text-stone-900 outline-none placeholder:text-stone-400"
                    style={{ minHeight: "24px", maxHeight: "192px" }}
                  />
                  <button
                    type="button"
                    onClick={() => void handleSend()}
                    disabled={sending || !input.trim() || !sessionId}
                    className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-vibrant text-white transition-colors hover:bg-vibrant/90 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </button>
                </div>
                <p className="mt-2 text-center text-xs text-stone-400">
                  NutriAI can make mistakes. Consult a professional for better and accurate results.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {error ? <Alert variant="error">{error}</Alert> : null}
    </div>
  );
}
