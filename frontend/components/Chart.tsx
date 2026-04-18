"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useAppStore } from "@/lib/store";

// Plotly must be client-side only (uses browser APIs)
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export const COLOURS = [
  "#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6",
  "#ef4444", "#ec4899", "#14b8a6", "#f97316", "#84cc16",
];

function getBaseLayout(theme: "dark" | "light") {
  const isDark = theme === "dark";
  return {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: {
      family: "DM Sans, sans-serif",
      color: isDark ? "#94a3b8" : "#334155",
      size: 12,
    },
    xaxis: {
      gridcolor: isDark ? "#1e2d3d" : "#e2e8f0",
      linecolor: isDark ? "#1e2d3d" : "#e2e8f0",
      zerolinecolor: isDark ? "#1e2d3d" : "#e2e8f0",
      tickfont: { color: isDark ? "#64748b" : "#64748b" },
    },
    yaxis: {
      gridcolor: isDark ? "#1e2d3d" : "#e2e8f0",
      linecolor: isDark ? "#1e2d3d" : "#e2e8f0",
      zerolinecolor: isDark ? "#1e2d3d" : "#e2e8f0",
      tickfont: { color: isDark ? "#64748b" : "#64748b" },
    },
    legend: {
      bgcolor: isDark ? "rgba(12,20,32,0.8)" : "rgba(255,255,255,0.85)",
      bordercolor: isDark ? "#1e2d3d" : "#e2e8f0",
      borderwidth: 1,
      font: { color: isDark ? "#94a3b8" : "#334155" },
    },
    margin: { t: 30, b: 40, l: 50, r: 20 },
  };
}

interface ChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  height?: number;
  className?: string;
  config?: Partial<Plotly.Config>;
}

export default function Chart({
  data,
  layout = {},
  height = 420,
  className,
  config = {},
}: ChartProps) {
  const [mounted, setMounted] = useState(false);
  const { theme } = useAppStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        className={`skeleton ${className ?? ""}`}
        style={{ height }}
      />
    );
  }

  const baseLayout = getBaseLayout(theme);
  const mergedLayout: Partial<Plotly.Layout> = {
    ...baseLayout,
    ...layout,
    xaxis: { ...baseLayout.xaxis, ...(layout.xaxis ?? {}) },
    yaxis: { ...baseLayout.yaxis, ...(layout.yaxis ?? {}) },
    legend: { ...baseLayout.legend, ...(layout.legend ?? {}) },
    height,
    autosize: true,
  };

  return (
    <div className={className}>
      <Plot
        data={data}
        layout={mergedLayout}
        config={{
          responsive: true,
          displayModeBar: true,
          scrollZoom: true,
          doubleClick: "reset",
          modeBarButtonsToRemove: ["lasso2d", "select2d"],
          ...config,
        }}
        style={{ width: "100%", height }}
        useResizeHandler
      />
    </div>
  );
}
