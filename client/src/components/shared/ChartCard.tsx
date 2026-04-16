import type { ChartData } from "../../types";
import { Chart } from "./Chart";

interface ChartCardProps {
  data: ChartData;
}

export function ChartCard({ data }: ChartCardProps) {
  return (
    <div
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        padding: "16px",
        backgroundColor: "white",
      }}
    >
      <Chart data={data} />
    </div>
  );
}
