import ReactECharts from "echarts-for-react";
import type { ChartData } from "../../types";

interface ChartProps {
  data: ChartData;
  height?: number;
}

export function Chart({ data, height = 300 }: ChartProps) {
  const option = buildOption(data);
  return <ReactECharts option={option} style={{ height }} />;
}

function buildOption(data: ChartData): Record<string, unknown> {
  const { chart_type, title, labels, datasets } = data;

  if (chart_type === "pie") {
    return {
      title: { text: title, left: "center" },
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: "60%",
          data: labels.map((label, i) => ({
            name: label,
            value: datasets[0]?.data[i] ?? 0,
          })),
        },
      ],
    };
  }

  if (chart_type === "scatter") {
    return {
      title: { text: title },
      tooltip: { trigger: "axis" },
      xAxis: { type: "value", name: data.x_axis || "" },
      yAxis: { type: "value", name: data.y_axis || "" },
      series: datasets.map((ds) => ({
        type: "scatter",
        name: ds.label,
        data: ds.data.map((v, i) => [labels[i], v]),
      })),
    };
  }

  // bar, line
  return {
    title: { text: title },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: labels,
      name: data.x_axis || "",
      axisLabel: { rotate: labels.length > 6 ? 30 : 0 },
    },
    yAxis: { type: "value", name: data.y_axis || "" },
    series: datasets.map((ds) => ({
      type: chart_type === "line" ? "line" : "bar",
      name: ds.label,
      data: ds.data,
    })),
  };
}
