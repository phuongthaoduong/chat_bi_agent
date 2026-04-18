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
    <div className="chat-view">
      <div className="chat-messages">
        {messages.length === 0 && !isLoading && (
          <div className="chat-empty">
            <div className="chat-empty-title">Ask your data</div>
            <p className="chat-empty-hint">Type a question below to get started.</p>
            <div className="chat-empty-examples">
              <span className="chat-empty-example">"Which product sold the most?"</span>
              <span className="chat-empty-example">"Show me monthly revenue trends"</span>
              <span className="chat-empty-example">"Sales breakdown by region?"</span>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}

        {isLoading && (
          <div className="message message--assistant">
            <div className="chat-thinking">
              <div className="loading-dots" style={{ margin: 0 }}>
                <div className="loading-dot" style={{ width: 6, height: 6 }} />
                <div className="loading-dot" style={{ width: 6, height: 6 }} />
                <div className="loading-dot" style={{ width: 6, height: 6 }} />
              </div>
              <span className="chat-thinking-label">thinking</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
