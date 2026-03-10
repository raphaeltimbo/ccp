"use client";

import * as XLSX from "xlsx";

interface ResultsDownloadProps {
  results: Record<string, Record<string, string | number>>;
}

export function ResultsDownload({ results }: ResultsDownloadProps) {
  const handleDownload = () => {
    const rowLabels = Object.keys(results);
    if (rowLabels.length === 0) return;

    const colLabels = Object.keys(results[rowLabels[0]]);

    const header = ["", ...colLabels];
    const rows = rowLabels.map((row) => [
      row,
      ...colLabels.map((col) => results[row][col]),
    ]);

    const wsData = [header, ...rows];
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Results");

    XLSX.writeFile(wb, "results.xlsx");
  };

  return (
    <button
      onClick={handleDownload}
      className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
    >
      <svg
        className="h-4 w-4 text-slate-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V3"
        />
      </svg>
      Download Excel
    </button>
  );
}
