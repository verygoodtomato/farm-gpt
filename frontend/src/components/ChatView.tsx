"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage, sendChatMessage } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface MessageWithMeta extends ChatMessage {
  sources?: string[];
}

export default function ChatView() {
  const [messages, setMessages] = useState<MessageWithMeta[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [currentSources, setCurrentSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: MessageWithMeta = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);
    setCurrentSources([]);

    // Add empty assistant message for streaming
    setMessages([...newMessages, { role: "assistant", content: "" }]);

    const apiMessages: ChatMessage[] = newMessages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    let sources: string[] = [];

    await sendChatMessage(
      apiMessages,
      (chunk) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: last.content + chunk,
            };
          }
          return updated;
        });
      },
      () => {
        // 완료 시 출처 정보 추가
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = { ...last, sources };
          }
          return updated;
        });
        setIsLoading(false);
      },
      (error) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: `오류가 발생했습니다: ${error}`,
          };
          return updated;
        });
        setIsLoading(false);
      },
      (s) => {
        sources = s;
        setCurrentSources(s);
      },
      useRag
    );
  };

  const SOURCE_LABELS: Record<string, string> = {
    strawberry: "딸기 재배",
    tomato: "토마토 재배",
    paprika: "파프리카 재배",
    smartfarm_basics: "스마트팜 기초",
    pest_management: "병해충 관리",
    climate_farming: "기후변화 농업",
  };

  const quickQuestions = [
    "딸기 재배 시 적정 온도와 습도는?",
    "토마토 잎곰팡이병 대처법은?",
    "스마트팜 CO2 공급 최적 시기는?",
    "점박이응애 천적 방제법 알려줘",
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-800">💬 AI 농업 컨설팅</h2>
          <p className="text-sm text-gray-500">
            작물 재배, 병해충, 스마트팜 등 농업 전반에 대해 질문하세요
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              className="w-4 h-4 text-farm-600 rounded focus:ring-farm-500"
            />
            <span className="text-gray-600">지식베이스 활용</span>
          </label>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-6xl mb-4">🌾</div>
            <h3 className="text-2xl font-bold text-gray-700 mb-2">
              FarmGPT에 오신 것을 환영합니다
            </h3>
            <p className="text-gray-500 mb-2 max-w-md">
              농업에 관한 모든 궁금한 점을 물어보세요.
            </p>
            <p className="text-xs text-farm-600 mb-8">
              {useRag
                ? "📚 지식베이스 기반 정확한 답변을 제공합니다"
                : "💡 일반 AI 지식 기반으로 답변합니다"}
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-lg">
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setInput(q)}
                  className="text-left p-3 rounded-lg border border-gray-200 hover:border-farm-400 hover:bg-farm-50 transition-colors text-sm text-gray-600"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            <div
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-farm-600 text-white"
                    : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div className="message-content">
                    <ReactMarkdown>{msg.content || "..."}</ReactMarkdown>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
            {/* 출처 표시 */}
            {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
              <div className="flex justify-start mt-1 ml-1">
                <div className="flex items-center gap-1 flex-wrap">
                  <span className="text-xs text-gray-400">📚 참고:</span>
                  {msg.sources.map((source, j) => (
                    <span
                      key={j}
                      className="text-xs bg-farm-50 text-farm-700 px-2 py-0.5 rounded-full border border-farm-200"
                    >
                      {SOURCE_LABELS[source] || source}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t bg-white p-4">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="농업에 대해 질문하세요..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-farm-500 focus:border-transparent disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-farm-600 text-white rounded-xl hover:bg-farm-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            전송
          </button>
        </div>
      </form>
    </div>
  );
}
