import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { api } from "../../hooks/useLifeOSAPI";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  contextUsed?: boolean;
}

const STARTER_PROMPTS = [
  "最近我在思考什么？",
  "本周我做了哪些代码工作？",
  "最近有哪些未完成的事项？",
  "我最近开了哪些会议？",
];

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const content = text || input.trim();
    if (!content || loading) return;

    setInput("");
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const { response, context_used } = await api.chat(content);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
        contextUsed: context_used,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "⚠️ 请求失败，请检查 LLM 配置是否正确。",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-gray-800 px-6 py-4">
        <h2 className="text-lg font-semibold text-white">上下文对话</h2>
        <p className="text-xs text-gray-500">基于你的个人知识库回答问题</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div className="text-center">
              <div className="mb-3 text-4xl">🧠</div>
              <p className="text-gray-500 text-sm">
                基于你积累的上下文，随时提问
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full max-w-md">
              {STARTER_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => sendMessage(p)}
                  className="rounded-lg border border-gray-800 p-3 text-left text-xs text-gray-500 transition hover:border-purple-700 hover:text-gray-300 hover:bg-purple-900/10"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  msg.role === "user" ? "bg-purple-600" : "bg-gray-800"
                }`}
              >
                {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
              </div>
              <div className={`max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-purple-600 text-white rounded-tr-sm"
                      : "bg-gray-900 text-gray-200 rounded-tl-sm border border-gray-800"
                  }`}
                >
                  {msg.content}
                </div>
                {msg.contextUsed && (
                  <span className="text-xs text-gray-700 px-1">
                    ✦ 基于个人上下文
                  </span>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800">
              <Bot size={14} />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-gray-800 bg-gray-900 px-4 py-3">
              <Loader2 size={16} className="animate-spin text-gray-500" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-4">
        <div className="flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="问问你的第二大脑... (Enter 发送，Shift+Enter 换行)"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-700 bg-gray-900 px-4 py-3 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-purple-600 transition"
            style={{ maxHeight: "120px", overflowY: "auto" }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-600 text-white transition hover:bg-purple-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
