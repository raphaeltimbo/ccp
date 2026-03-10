"use client";

import { PlotlyChart } from "./PlotlyChart";

interface MachReynoldsPanelProps {
  plots: Record<string, unknown>;
}

export function MachReynoldsPanel({ plots }: MachReynoldsPanelProps) {
  const hasMach = !!plots["mach"];
  const hasReynolds = !!plots["reynolds"];

  if (!hasMach && !hasReynolds) return null;

  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-800 mb-4">
        Mach &amp; Reynolds Numbers
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {hasMach && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Mach Number
            </h4>
            <PlotlyChart
              figure={
                plots["mach"] as {
                  data: Plotly.Data[];
                  layout: Partial<Plotly.Layout>;
                }
              }
              className="h-80"
            />
          </div>
        )}
        {hasReynolds && (
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Reynolds Number
            </h4>
            <PlotlyChart
              figure={
                plots["reynolds"] as {
                  data: Plotly.Data[];
                  layout: Partial<Plotly.Layout>;
                }
              }
              className="h-80"
            />
          </div>
        )}
      </div>
    </div>
  );
}
