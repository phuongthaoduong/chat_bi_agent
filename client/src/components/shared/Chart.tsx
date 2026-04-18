import ReactECharts from "echarts-for-react";
import type { ChartData } from "../../types";

interface ChartProps {
  data: ChartData;
  height?: number;
}

const PALETTE = ["#3EB3E8", "#52B788", "#E05C5C", "#A78BFA", "#FB923C", "#34D399", "#60A5FA"];

const BASE: Record<string, unknown> = {
  backgroundColor: "transparent",
  color: PALETTE,
  textStyle: {
    fontFamily: "'Outfit', sans-serif",
    color: "#6A8FAE",
    fontSize: 11,
  },
  tooltip: {
    backgroundColor: "#111E2E",
    borderColor: "#1D304A",
    borderWidth: 1,
    textStyle: { color: "#E2EEF8", fontSize: 12, fontFamily: "'Outfit', sans-serif" },
    extraCssText: "border-radius:6px;box-shadow:0 6px 20px rgba(0,0,0,0.5);",
  },
};

function fmtAxisValue(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    const n = value / 1_000_000;
    return (Number.isInteger(n) ? n : parseFloat(n.toFixed(1))) + "M";
  }
  if (abs >= 1_000) {
    const n = value / 1_000;
    return (Number.isInteger(n) ? n : parseFloat(n.toFixed(1))) + "K";
  }
  return String(value);
}

const AXIS_COMMON = {
  axisLine:  { lineStyle: { color: "#142030" } },
  axisTick:  { show: false },
  axisLabel: { color: "#6A8FAE", fontSize: 10, formatter: fmtAxisValue },
  splitLine: { lineStyle: { color: "#0C1520", type: "dashed" as const } },
};

export function Chart({ data, height = 258 }: ChartProps) {
  return (
    <ReactECharts
      option={buildOption(data)}
      style={{ height, width: "100%" }}
      opts={{ renderer: "svg" }}
    />
  );
}

function buildOption(data: ChartData): Record<string, unknown> {
  const { chart_type, labels, datasets } = data;

  if (chart_type === "pie") {
    return {
      ...BASE,
      tooltip: { ...(BASE.tooltip as object), trigger: "item" },
      legend: {
        orient: "vertical",
        right: 8,
        top: "middle",
        textStyle: { color: "#6A8FAE", fontSize: 10, fontFamily: "'Outfit', sans-serif" },
        icon: "circle",
        itemWidth: 7,
        itemHeight: 7,
      },
      series: [
        {
          type: "pie",
          radius: ["38%", "64%"],
          center: ["42%", "50%"],
          data: labels.map((label, i) => ({
            name: label,
            value: datasets[0]?.data[i] ?? 0,
          })),
          label: { show: false },
          emphasis: {
            scale: true,
            scaleSize: 5,
            itemStyle: { shadowBlur: 16, shadowColor: "rgba(62,179,232,0.3)" },
          },
        },
      ],
    };
  }

  if (chart_type === "scatter") {
    return {
      ...BASE,
      tooltip: { ...(BASE.tooltip as object), trigger: "item" },
      xAxis: {
        type: "value",
        name: data.x_axis ?? "",
        nameTextStyle: { color: "#6A8FAE", fontSize: 10 },
        ...AXIS_COMMON,
      },
      yAxis: {
        type: "value",
        name: data.y_axis ?? "",
        nameTextStyle: { color: "#6A8FAE", fontSize: 10 },
        ...AXIS_COMMON,
        axisLine: { show: false },
      },
      series: datasets.map((ds) => ({
        type: "scatter",
        name: ds.label,
        data: ds.data.map((v, i) => [labels[i], v]),
        symbolSize: 7,
      })),
    };
  }

  // bar / line
  const isLine = chart_type === "line";
  return {
    ...BASE,
    tooltip: { ...(BASE.tooltip as object), trigger: "axis" },
    grid: {
      left: 12,
      right: 12,
      top: 12,
      bottom: 8,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: labels,
      ...AXIS_COMMON,
      axisLabel: {
        ...AXIS_COMMON.axisLabel,
        rotate: labels.length > 6 ? 30 : 0,
        interval: 0,
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      ...AXIS_COMMON,
      axisLine: { show: false },
    },
    series: datasets.map((ds, i) => ({
      type: isLine ? "line" : "bar",
      name: ds.label,
      data: ds.data,
      ...(isLine
        ? {
            smooth: true,
            symbol: "circle",
            symbolSize: 5,
            lineStyle: { width: 2 },
            areaStyle:
              i === 0
                ? {
                    color: {
                      type: "linear",
                      x: 0, y: 0, x2: 0, y2: 1,
                      colorStops: [
                        { offset: 0, color: "rgba(62,179,232,0.18)" },
                        { offset: 1, color: "rgba(62,179,232,0)" },
                      ],
                    },
                  }
                : undefined,
          }
        : {
            barMaxWidth: 42,
            itemStyle: { borderRadius: [3, 3, 0, 0] },
          }),
    })),
  };
}
