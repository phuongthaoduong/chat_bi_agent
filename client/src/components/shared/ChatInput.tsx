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
    <div className="chat-input-bar">
      <div className="chat-input-inner">
        <input
          className="chat-input-field"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? "Ask a question about your data…"}
          disabled={isLoading}
          autoFocus
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? (
            <div className="loading-dots" style={{ margin: 0, gap: 4 }}>
              <div className="loading-dot" style={{ width: 5, height: 5, background: "var(--text-3)" }} />
              <div className="loading-dot" style={{ width: 5, height: 5, background: "var(--text-3)" }} />
              <div className="loading-dot" style={{ width: 5, height: 5, background: "var(--text-3)" }} />
            </div>
          ) : (
            "Send →"
          )}
        </button>
      </div>
    </div>
  );
}
