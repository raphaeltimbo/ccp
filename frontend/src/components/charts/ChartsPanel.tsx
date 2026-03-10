"use client";

import { PlotlyChart } from "./PlotlyChart";

interface ChartsPanelProps {
  plots: Record<string, unknown>;
}

const CHART_KEYS = [
  { key: "head", label: "Head vs Flow" },
  { key: "eff", label: "Efficiency vs Flow" },
  { key: "discharge_pressure", label: "Discharge Pressure vs Flow" },
  { key: "power", label: "Power vs Flow" },
];

export function ChartsPanel({ plots }: ChartsPanelProps) {
  const availableCharts = CHART_KEYS.filter((c) => plots[c.key]);
  if (availableCharts.length === 0) return null;

  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-800 mb-4">
        Performance Curves
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {availableCharts.map(({ key, label }) => (
          <div
            key={key}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              {label}
            </h4>
            <PlotlyChart
              figure={
                plots[key] as {
                  data: Plotly.Data[];
                  layout: Partial<Plotly.Layout>;
                }
              }
              className="h-80"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
