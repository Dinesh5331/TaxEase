"use client";

import { useState, useRef, useEffect } from "react";
import { Bot, Send, User, Sparkles, Paperclip, Mic, Loader2, AlertCircle } from "lucide-react";
import { clsx } from "clsx";

type Message = {
  role: "assistant" | "user";
  content: string;
};

type BackendStatus = "checking" | "online" | "offline";

const SUGGESTIONS = [
  "Which ITR form should I file?",
  "Who can file ITR-1?",
  "Explain HRA deduction",
  "Old vs New tax regime differences",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm TaxEase AI, powered by your TaxAssist RAG engine. Ask me anything about Indian income tax — ITR forms, eligibility, deductions, or filing rules.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check backend health on mount
  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setBackendStatus(d.status === "ok" ? "online" : "offline"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error ?? "Unknown error");
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${message}\n\nMake sure the TaxAssist backend server is running:\n\`cd backend/fastapi && ..\\myenv\\Scripts\\python.exe -m uvicorn app:app --reload --port 8000 --reload-dir ..\``,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggest = (text: string) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const formatAnswer = (content: string): React.ReactNode => {
    // Strip any residual ** bold markers and * italic from LLM output
    const cleaned = content
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#{1,6}\s/g, ""); // strip # headers

    const lines = cleaned.split("\n");

    return (
      <div className="space-y-1">
        {lines.map((line, i) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={i} className="h-2" />;

          // Numbered list item (1. 2. etc.)
          if (/^\d+\.\s/.test(trimmed)) {
            return (
              <div key={i} className="flex gap-2">
                <span className="text-primary font-semibold shrink-0 w-5">
                  {trimmed.match(/^\d+/)?.[0]}.
                </span>
                <span>{trimmed.replace(/^\d+\.\s*/, "")}</span>
              </div>
            );
          }

          // Bullet item (- or *)
          if (/^[-*•]\s/.test(trimmed)) {
            return (
              <div key={i} className="flex gap-2 pl-2">
                <span className="text-slate-400 shrink-0">–</span>
                <span>{trimmed.replace(/^[-*•]\s*/, "")}</span>
              </div>
            );
          }

          // Normal paragraph line
          return <p key={i}>{trimmed}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-primary-dark">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-800">TaxEase AI Assistant</h2>
            <p className="text-xs text-slate-500">Trained on Indian Income Tax Act — RAG powered</p>
          </div>
        </div>
        {/* Backend status indicator */}
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              "w-2 h-2 rounded-full",
              backendStatus === "online"
                ? "bg-emerald-500"
                : backendStatus === "offline"
                ? "bg-red-400"
                : "bg-amber-400 animate-pulse"
            )}
          />
          <span className="text-xs text-slate-400">
            {backendStatus === "online"
              ? "Backend online"
              : backendStatus === "offline"
              ? "Backend offline"
              : "Connecting..."}
          </span>
          <button className="ml-2 text-slate-400 hover:text-slate-600">
            <Sparkles className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Backend offline banner */}
      {backendStatus === "offline" && (
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border-b border-amber-100 text-amber-800 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>
            Backend is offline. Start it with:{" "}
            <code className="bg-amber-100 px-1 rounded font-mono">
              cd backend/fastapi &amp;&amp; ..\myenv\Scripts\python.exe -m uvicorn app:app --reload --port 8000 --reload-dir ..
            </code>
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={clsx(
              "flex gap-4 max-w-[85%]",
              msg.role === "user" ? "ml-auto flex-row-reverse" : ""
            )}
          >
            <div
              className={clsx(
                "w-8 h-8 rounded-full flex shrink-0 items-center justify-center mt-1",
                msg.role === "assistant"
                  ? "bg-primary text-white"
                  : "bg-slate-800 text-white"
              )}
            >
              {msg.role === "assistant" ? (
                <Bot className="w-4 h-4" />
              ) : (
                <User className="w-4 h-4" />
              )}
            </div>

            <div
              className={clsx(
                "p-4 rounded-2xl text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-slate-900 text-white rounded-tr-none shadow-sm"
                  : "bg-white text-slate-700 border border-slate-100 rounded-tl-none shadow-sm"
              )}
            >
              {formatAnswer(msg.content)}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex gap-4 max-w-[85%]">
            <div className="w-8 h-8 rounded-full flex shrink-0 items-center justify-center mt-1 bg-primary text-white">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-100 rounded-tl-none shadow-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-primary animate-spin" />
              <span className="text-sm text-slate-500">Searching tax knowledge base...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="p-4 bg-white border-t border-slate-100">
        {messages.length === 1 && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSuggest(s)}
                className="px-4 py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full text-xs font-medium text-slate-600 whitespace-nowrap transition-smooth"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={handleSend}
          className="relative flex items-end gap-2 bg-slate-50 border border-slate-200 rounded-2xl p-2 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-smooth"
        >
          <button type="button" className="p-2 text-slate-400 hover:text-slate-600 transition-smooth">
            <Paperclip className="w-5 h-5" />
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about taxes..."
            className="w-full max-h-32 bg-transparent border-none focus:ring-0 resize-none py-2.5 text-sm text-slate-800 placeholder-slate-400 min-h-[44px] outline-none"
            rows={1}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />

          <div className="flex gap-1 pb-1 pr-1">
            <button
              type="button"
              className="p-2 text-slate-400 hover:text-slate-600 transition-smooth"
            >
              <Mic className="w-5 h-5" />
            </button>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-2 bg-primary hover:bg-primary-dark disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl transition-smooth"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </form>

        <div className="text-center mt-3">
          <span className="text-[10px] text-slate-400">
            AI answers are grounded in your indexed tax documents. Always verify critical decisions.
          </span>
        </div>
      </div>
    </div>
  );
}
