import type { Message } from "../../types";
import { ChartCard } from "./ChartCard";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          padding: "12px 16px",
          borderRadius: "12px",
          backgroundColor: isUser ? "#4f46e5" : "#f3f4f6",
          color: isUser ? "white" : "#111827",
          fontSize: "14px",
          lineHeight: "1.5",
        }}
      >
        <p style={{ margin: 0 }}>{message.content}</p>
        {message.chart && (
          <div style={{ marginTop: "12px" }}>
            <ChartCard data={message.chart} />
          </div>
        )}
      </div>
    </div>
  );
}
