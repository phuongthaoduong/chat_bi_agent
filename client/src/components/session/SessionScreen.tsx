import { useState } from "react";
import type { UploadResponse, Message } from "../../types";
import { askQuestion } from "../../api";
import { DashboardView } from "./DashboardView";
import { FileInfoBar } from "./FileInfoBar";
import { ViewToggle } from "./ViewToggle";
import { ChatView } from "./ChatView";

interface SessionScreenProps {
  data: UploadResponse;
  onReset: () => void;
}

export function SessionScreen({ data, onReset }: SessionScreenProps) {
  const [activeView, setActiveView] = useState<"dashboard" | "chat">("dashboard");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (question: string) => {
    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await askQuestion(data.session_id, question);
      const assistantMessage: Message = {
        role: "assistant",
        content: response.answer,
        chart: response.chart,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content: err instanceof Error ? err.message : "Something went wrong.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          borderBottom: "1px solid #e5e7eb",
        }}
      >
        <h1 style={{ fontSize: "20px", margin: 0 }}>ChatBI</h1>
        <ViewToggle activeView={activeView} onToggle={setActiveView} />
        <button
          onClick={onReset}
          style={{
            padding: "6px 16px",
            border: "1px solid #d1d5db",
            borderRadius: "6px",
            background: "white",
            cursor: "pointer",
          }}
        >
          New Upload
        </button>
      </div>
      <FileInfoBar profiles={data.profiles} warnings={data.warnings} />
      {activeView === "dashboard" ? (
        <DashboardView insights={data.insights} charts={data.charts} />
      ) : (
        <ChatView messages={messages} onSend={handleSendMessage} isLoading={isLoading} />
      )}
    </div>
  );
}
