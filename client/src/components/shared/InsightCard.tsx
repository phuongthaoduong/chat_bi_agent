interface InsightCardProps {
  text: string;
}

export function InsightCard({ text }: InsightCardProps) {
  return (
    <div
      style={{
        padding: "12px 16px",
        backgroundColor: "#f0f9ff",
        border: "1px solid #bae6fd",
        borderRadius: "8px",
        fontSize: "14px",
        color: "#0c4a6e",
      }}
    >
      {text}
    </div>
  );
}
