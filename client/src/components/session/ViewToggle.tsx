interface ViewToggleProps {
  activeView: "dashboard" | "chat";
  onToggle: (view: "dashboard" | "chat") => void;
}

export function ViewToggle({ activeView, onToggle }: ViewToggleProps) {
  return (
    <div style={{ display: "flex", gap: "4px", padding: "8px", backgroundColor: "#f3f4f6", borderRadius: "8px" }}>
      {(["dashboard", "chat"] as const).map((view) => (
        <button
          key={view}
          onClick={() => onToggle(view)}
          style={{
            padding: "6px 16px",
            border: "none",
            borderRadius: "6px",
            fontSize: "14px",
            cursor: "pointer",
            backgroundColor: activeView === view ? "white" : "transparent",
            color: activeView === view ? "#111827" : "#6b7280",
            boxShadow: activeView === view ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
          }}
        >
          {view === "dashboard" ? "Dashboard" : "Chat"}
        </button>
      ))}
    </div>
  );
}
