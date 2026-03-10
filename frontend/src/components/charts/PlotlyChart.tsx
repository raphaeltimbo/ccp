"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  figure: { data: Plotly.Data[]; layout: Partial<Plotly.Layout> };
  className?: string;
}

export function PlotlyChart({ figure, className }: PlotlyChartProps) {
  return (
    <div className={className}>
      <Plot
        data={figure.data}
        layout={{
          ...figure.layout,
          autosize: true,
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        config={{ responsive: true }}
      />
    </div>
  );
}
