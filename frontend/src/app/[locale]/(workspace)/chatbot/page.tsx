"use client";

import { useState, useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { post, get } from "@/lib/api";
import { useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/lib/utils";

interface Citation {
  source: string;
  year: number | null;
}

interface ChatMessage {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  was_refused: boolean;
  language: string;
  created_at: string;
}

export default function ChatbotPage() {
  const t = useTranslations("chatbot");
  const { workspace } = useWorkspaceStore();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const qc = useQueryClient();

  // Fetch session messages
  const { data: messages = [] } = useQuery({
    queryKey: ["chat", sessionId],
    queryFn: () =>
      sessionId ? get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`) : [],
    enabled: !!sessionId,
    refetchInterval: false,
  });

  // Create session
  const createSession = useMutation({
    mutationFn: () =>
      post<{ session_id: string }>("/chat/sessions", {
        language: "en",
        workspace_id: workspace?.id,
      }),
    onSuccess: (data) => setSessionId(data.session_id),
  });

  // Send message
  const sendMessage = useMutation({
    mutationFn: (content: string) =>
      post<ChatMessage>(`/chat/sessions/${sessionId}/messages`, { content }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chat", sessionId] });
      setInput("");
    },
  });

  // Auto-start chat session on mount
  useEffect(() => {
    createSession.mutate();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;
    sendMessage.mutate(input.trim());
  }

  // Loading state while session is being created
  if (!sessionId && createSession.isPending) {
    return (
      <div className="max-w-2xl mx-auto p-6 flex items-center justify-center h-64">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent mx-auto" />
          <p className="text-sm text-muted-foreground">Starting Ask FamPath…</p>
        </div>
      </div>
    );
  }

  // Error state - retry button
  if (!sessionId && createSession.isError) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">{t("title")}</h1>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-4">
          <p className="text-red-700 text-sm">Could not start a chat session. Please make sure you are signed in.</p>
          <button
            onClick={() => createSession.mutate()}
            className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm font-medium hover:bg-brand-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }


  // ── Chat interface ─────────────────────────────────────────────────────────
  return (
    <div className="max-w-2xl mx-auto flex flex-col h-[calc(100vh-120px)] p-6">
      <h1 className="text-2xl font-bold mb-4">{t("title")}</h1>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 rounded-xl border bg-gray-50 p-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <p className="text-2xl mb-2">🤖</p>
            <p className="text-sm">Ask me anything about engineering colleges, branches, or counselling rules.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.message_id}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-br-sm"
                  : "bg-white border border-gray-200 rounded-bl-sm"
              )}
            >
              <p>{msg.content}</p>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200 space-y-0.5">
                  <p className="text-xs text-muted-foreground font-medium">{t("citedFrom")}:</p>
                  {msg.citations.map((c, i) => (
                    <p key={i} className="text-xs text-muted-foreground">
                      📄 {c.source}{c.year ? ` (${c.year})` : ""}
                    </p>
                  ))}
                </div>
              )}

              {/* Refused indicator */}
              {msg.was_refused && (
                <p className="mt-1 text-xs text-amber-600 italic">{t("refusedMessage")}</p>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {sendMessage.isPending && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm text-muted-foreground">
              {t("typingIndicator")}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("placeholder")}
          className="flex-1 rounded-xl border border-input px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          disabled={sendMessage.isPending || !sessionId}
          aria-label={t("placeholder")}
        />
        <button
          type="submit"
          disabled={!input.trim() || sendMessage.isPending || !sessionId}
          className="rounded-xl bg-brand-600 text-white px-4 py-2.5 text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
        >
          {t("sendButton")}
        </button>
      </form>
    </div>
  );
}
