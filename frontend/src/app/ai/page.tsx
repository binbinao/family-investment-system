"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, StopCircle, History, Zap, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { AIConversation, ChatMessage } from "@/types";
import ReactMarkdown from "react-markdown";

export default function AIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<"quick" | "deep">("quick");
  const [streaming, setStreaming] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<AIConversation[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchHistory = useCallback(async () => {
    try {
      const data = await api.ai.history(50);
      setHistory(data);
    } catch {
      // ignore
    }
  }, []);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || streaming) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question, mode },
    ]);

    const assistantMsg: ChatMessage = {
      role: "assistant",
      content: "",
      mode,
      isStreaming: true,
    };
    setMessages((prev) => [...prev, assistantMsg]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(api.ai.chatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question, mode }),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.error) {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === "assistant") {
                  last.content = data.error;
                  last.isStreaming = false;
                }
                return updated;
              });
              setStreaming(false);
              return;
            }

            if (data.progress) {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === "assistant") {
                  last.progress = data.progress;
                }
                return [...updated];
              });
            }

            if (data.content) {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === "assistant") {
                  last.content += data.content;
                  last.progress = undefined;
                }
                return [...updated];
              });
            }

            if (data.done) {
              setMessages((prev) => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last.role === "assistant") {
                  last.isStreaming = false;
                }
                return [...updated];
              });
            }
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content += "\n\n*[对话已取消]*";
            last.isStreaming = false;
          }
          return updated;
        });
      } else {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content = "AI 财务顾问暂时不可用，请稍后再试";
            last.isStreaming = false;
          }
          return updated;
        });
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  };

  const handleCancel = () => {
    abortRef.current?.abort();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const loadHistory = () => {
    setShowHistory(!showHistory);
    if (!showHistory) fetchHistory();
  };

  const restoreConversation = (conv: AIConversation) => {
    setMessages([
      { role: "user", content: conv.question, mode: conv.mode },
      { role: "assistant", content: conv.answer || "", mode: conv.mode },
    ]);
    setShowHistory(false);
  };

  return (
    <div className="flex h-[calc(100vh-5rem)] flex-col">
      <div className="flex items-center justify-between border-b px-1 pb-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI 财务顾问</h1>
          <p className="text-sm text-muted-foreground">
            咨询家庭投资问题：快问秒回，深聊多角度分析
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border p-0.5">
            <button
              className={`flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === "quick"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent"
              }`}
              onClick={() => setMode("quick")}
            >
              <Zap className="h-3.5 w-3.5" />
              快问
            </button>
            <button
              className={`flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === "deep"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent"
              }`}
              onClick={() => setMode("deep")}
            >
              <Brain className="h-3.5 w-3.5" />
              深聊
            </button>
          </div>
          <Button variant="outline" size="sm" onClick={loadHistory}>
            <History className="mr-1 h-4 w-4" />
            历史
          </Button>
        </div>
      </div>

      {showHistory ? (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {history.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-8">
                暂无对话历史
              </p>
            ) : (
              history.map((conv) => (
                <Card
                  key={conv.id}
                  className="cursor-pointer transition-colors hover:bg-accent/50"
                  onClick={() => restoreConversation(conv)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">
                        {conv.mode === "quick" ? "快问" : "深聊"} ·{" "}
                        {formatDateTime(conv.created_at)}
                      </span>
                    </div>
                    <p className="mt-1 text-sm line-clamp-2">{conv.question}</p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      ) : (
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 text-4xl">🤖</div>
              <h2 className="text-lg font-medium">
                你好，我是你的 AI 财务顾问，有什么想聊聊？
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {mode === "quick"
                  ? "快问模式：即时回复，适合日常小问题"
                  : "深聊模式：多角度深入分析，适合重大决策"}
              </p>
              <div className="mt-6 grid gap-2 sm:grid-cols-2">
                {[
                  "我的持仓整体表现怎么样？",
                  "现在的仓位配置合理吗？",
                  "帮我分析一下风险敞口",
                  "有哪些值得关注的市场信号？",
                ].map((q) => (
                  <button
                    key={q}
                    className="rounded-lg border px-4 py-2 text-left text-sm transition-colors hover:bg-accent"
                    onClick={() => {
                      setInput(q);
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="text-sm">
                        {msg.progress && (
                          <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                            <div className="h-3 w-3 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                            {msg.progress}
                          </div>
                        )}
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                        {msg.isStreaming && !msg.progress && (
                          <span className="inline-block h-4 w-1 animate-pulse bg-foreground" />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="border-t p-4">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              mode === "quick"
                ? "输入你的投资问题...（Enter 发送，Shift+Enter 换行）"
                : "输入需要深入分析的问题...（Enter 发送）"
            }
            className="min-h-[44px] max-h-[120px] resize-none"
            rows={1}
          />
          {streaming ? (
            <Button
              variant="destructive"
              size="icon"
              onClick={handleCancel}
              className="shrink-0"
            >
              <StopCircle className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim()}
              className="shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
        <p className="mt-1 text-center text-xs text-muted-foreground">
          当前模式：{mode === "quick" ? "⚡ 快问" : "🧠 深聊"} ·
          AI 财务顾问回复仅供参考，不构成投资建议
        </p>
      </div>
    </div>
  );
}
