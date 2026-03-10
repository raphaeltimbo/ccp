"use client";

import { useStraightThroughStore } from "@/stores/straightThroughStore";
import { ResultsTable } from "./ResultsTable";
import { ResultsDownload } from "./ResultsDownload";
import { ChartsPanel } from "../charts/ChartsPanel";
import { MachReynoldsPanel } from "../charts/MachReynoldsPanel";

export function ResultsPanel() {
  const results = useStraightThroughStore((s) => s.results);

  if (!results) return null;

  return (
    <div className="space-y-8 border-t border-slate-200 pt-8">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900">Results</h2>
          <ResultsDownload results={results.results} />
        </div>
        <ResultsTable
          results={results.results}
          highlights={results.highlights}
        />
      </div>
      <ChartsPanel plots={results.plots as Record<string, unknown>} />
      <MachReynoldsPanel plots={results.plots as Record<string, unknown>} />
    </div>
  );
}
