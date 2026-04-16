import { useRef, useEffect } from "react";
import type { Message } from "../../types";
import { ChatInput } from "../shared/ChatInput";
import { ChatMessage } from "../shared/ChatMessage";

interface ChatViewProps {
  messages: Message[];
  onSend: (message: string) => void;
  isLoading: boolean;
}

export function ChatView({ messages, onSend, isLoading }: ChatViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" }}>
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#9ca3af", marginTop: "48px" }}>
            <p>Ask a question about your data</p>
            <p style={{ fontSize: "14px" }}>
              Try: "What product sold the most?" or "Show me monthly trends"
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {isLoading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "12px",
                backgroundColor: "#f3f4f6",
                color: "#6b7280",
                fontSize: "14px",
              }}
            >
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
