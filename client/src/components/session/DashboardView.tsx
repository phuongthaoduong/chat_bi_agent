import type { ChartData } from "../../types";
import { ChartCard } from "../shared/ChartCard";
import { InsightCard } from "../shared/InsightCard";

interface DashboardViewProps {
  insights: string[];
  charts: ChartData[];
}

export function DashboardView({ insights, charts }: DashboardViewProps) {
  if (charts.length === 0 && insights.length === 0) {
    return (
      <div style={{ padding: "48px", textAlign: "center", color: "#9ca3af" }}>
        <p>No charts generated. Make sure DEEPSEEK_API_KEY is set on the server.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px" }}>
      {insights.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginBottom: "24px",
          }}
        >
          {insights.map((text, i) => (
            <InsightCard key={i} text={text} />
          ))}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "16px",
        }}
      >
        {charts.map((chart, i) => (
          <ChartCard key={i} data={chart} />
        ))}
      </div>
    </div>
  );
}
