import { useState, type KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (trimmed && !isLoading) {
      onSend(trimmed);
      setValue("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: "flex", gap: "8px", padding: "16px 24px", borderTop: "1px solid #e5e7eb" }}>
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || "Ask a question about your data..."}
        disabled={isLoading}
        style={{
          flex: 1,
          padding: "10px 16px",
          border: "1px solid #d1d5db",
          borderRadius: "8px",
          fontSize: "14px",
          outline: "none",
        }}
      />
      <button
        onClick={handleSend}
        disabled={isLoading || !value.trim()}
        style={{
          padding: "10px 20px",
          backgroundColor: isLoading ? "#9ca3af" : "#4f46e5",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: isLoading ? "wait" : "pointer",
          fontSize: "14px",
        }}
      >
        {isLoading ? "..." : "Send"}
      </button>
    </div>
  );
}
