"use client";

import { CellHighlight } from "@/lib/types/common";

interface ResultsTableProps {
  results: Record<string, Record<string, string | number>>;
  highlights: CellHighlight[];
}

function getHighlightClass(
  rowIdx: number,
  colIdx: number,
  highlights: CellHighlight[],
): string {
  const match = highlights.find((h) => h.row === rowIdx && h.col === colIdx);
  if (!match) return "";
  return match.color === "green" ? "bg-[#C8E6C9]" : "bg-[#FFCDD2]";
}

export function ResultsTable({ results, highlights }: ResultsTableProps) {
  const rowLabels = Object.keys(results);
  if (rowLabels.length === 0) return null;

  const colLabels = Object.keys(results[rowLabels[0]]);

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-slate-50">
            <th className="sticky left-0 z-10 bg-slate-50 px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-500 border-b border-r border-slate-200">
              &nbsp;
            </th>
            {colLabels.map((col) => (
              <th
                key={col}
                className="whitespace-nowrap px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-wider text-slate-500 border-b border-slate-200"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rowLabels.map((row, rowIdx) => (
            <tr
              key={row}
              className={`${
                rowIdx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
              } hover:bg-slate-50`}
            >
              <td className="sticky left-0 z-10 bg-inherit px-4 py-2.5 font-medium text-slate-700 border-r border-slate-200 whitespace-nowrap">
                {row}
              </td>
              {colLabels.map((col, colIdx) => {
                const highlightClass = getHighlightClass(
                  rowIdx,
                  colIdx,
                  highlights,
                );
                const value = results[row][col];
                return (
                  <td
                    key={col}
                    className={`px-4 py-2.5 text-right whitespace-nowrap tabular-nums ${highlightClass}`}
                  >
                    {value != null ? String(value) : ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
