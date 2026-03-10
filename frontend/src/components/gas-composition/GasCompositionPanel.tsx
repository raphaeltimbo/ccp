"use client";

import { useState } from "react";
import { useFluids } from "../../hooks/useFluids";
import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { GasComposition } from "../../lib/types/straightThrough";

const MAX_GASES = 6;

interface GasRow {
  component: string;
  molarFraction: number;
}

interface GasColumn {
  name: string;
  rows: GasRow[];
}

function createDefaultGasColumn(index: number): GasColumn {
  return {
    name: `gas_${index}`,
    rows: [{ component: "", molarFraction: 0 }],
  };
}

export function GasCompositionPanel() {
  const { data: fluidList, isLoading } = useFluids();
  const {
    setGasCompositions,
    guaranteeGasName,
    setGuaranteeGasName,
    testGasName,
    setTestGasName,
  } = useStraightThroughStore();

  const [gases, setGases] = useState<GasColumn[]>(() =>
    Array.from({ length: MAX_GASES }, (_, i) => createDefaultGasColumn(i)),
  );

  function syncToStore(updatedGases: GasColumn[]) {
    const compositions: GasComposition[] = updatedGases.map((g) => ({
      name: g.name,
      fluid: {
        components: Object.fromEntries(
          g.rows
            .filter((r) => r.component && r.molarFraction > 0)
            .map((r) => [r.component, r.molarFraction]),
        ),
      },
    }));
    setGasCompositions(compositions);
  }

  function updateGas(
    gasIndex: number,
    updater: (g: GasColumn) => GasColumn,
  ) {
    setGases((prev) => {
      const next = [...prev];
      next[gasIndex] = updater({ ...next[gasIndex] });
      syncToStore(next);
      return next;
    });
  }

  function addRow(gasIndex: number) {
    updateGas(gasIndex, (g) => ({
      ...g,
      rows: [...g.rows, { component: "", molarFraction: 0 }],
    }));
  }

  function removeRow(gasIndex: number, rowIndex: number) {
    updateGas(gasIndex, (g) => ({
      ...g,
      rows: g.rows.filter((_, i) => i !== rowIndex),
    }));
  }

  function updateRow(
    gasIndex: number,
    rowIndex: number,
    field: keyof GasRow,
    value: string | number,
  ) {
    updateGas(gasIndex, (g) => ({
      ...g,
      rows: g.rows.map((r, i) =>
        i === rowIndex ? { ...r, [field]: value } : r,
      ),
    }));
  }

  function updateGasName(gasIndex: number, name: string) {
    updateGas(gasIndex, (g) => ({ ...g, name }));
  }

  const gasNames = gases.map((g) => g.name);

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-800">
          Gas Composition
        </h2>
      </div>

      <div className="p-5">
        {/* Gas selectors */}
        <div className="mb-5 flex gap-6">
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
              Guarantee Gas
            </label>
            <select
              value={guaranteeGasName}
              onChange={(e) => setGuaranteeGasName(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">Select...</option>
              {gasNames.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
              Test Gas
            </label>
            <select
              value={testGasName}
              onChange={(e) => setTestGasName(e.target.value)}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">Select...</option>
              {gasNames.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Gas columns grid */}
        <div className="overflow-x-auto -mx-5 px-5 pb-2">
          <div className="inline-flex gap-3">
            {gases.map((gas, gi) => {
              const total = gas.rows.reduce(
                (sum, r) => sum + (r.molarFraction || 0),
                0,
              );
              const totalOk = Math.abs(total - 1) < 0.001;
              const hasComponents = gas.rows.some(
                (r) => r.component && r.molarFraction > 0,
              );

              return (
                <div
                  key={gi}
                  className={`w-56 shrink-0 rounded-lg border p-3 ${
                    hasComponents
                      ? "border-primary-200 bg-primary-50/30"
                      : "border-slate-200 bg-slate-50/50"
                  }`}
                >
                  {/* Gas name */}
                  <input
                    type="text"
                    value={gas.name}
                    onChange={(e) => updateGasName(gi, e.target.value)}
                    className="mb-3 w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm font-semibold text-slate-700"
                  />

                  {/* Header */}
                  <div className="mb-1.5 grid grid-cols-[1fr_4.5rem_1.25rem] gap-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    <span>Component</span>
                    <span className="text-right">Mol. frac.</span>
                    <span />
                  </div>

                  {/* Rows */}
                  <div className="space-y-1.5">
                    {gas.rows.map((row, ri) => (
                      <div
                        key={ri}
                        className="grid grid-cols-[1fr_4.5rem_1.25rem] items-center gap-1"
                      >
                        <select
                          value={row.component}
                          onChange={(e) =>
                            updateRow(gi, ri, "component", e.target.value)
                          }
                          className="w-full rounded-md border border-slate-300 bg-white px-1.5 py-1.5 text-xs text-slate-700"
                        >
                          <option value="">--</option>
                          {isLoading ? (
                            <option>Loading...</option>
                          ) : (
                            fluidList?.map((f) => (
                              <option key={f} value={f}>
                                {f}
                              </option>
                            ))
                          )}
                        </select>
                        <input
                          type="number"
                          step="0.001"
                          min="0"
                          max="1"
                          value={row.molarFraction || ""}
                          onChange={(e) =>
                            updateRow(
                              gi,
                              ri,
                              "molarFraction",
                              parseFloat(e.target.value) || 0,
                            )
                          }
                          className="w-full rounded-md border border-slate-300 bg-white px-1.5 py-1.5 text-xs text-right text-slate-700"
                          placeholder="0.000"
                        />
                        <button
                          onClick={() => removeRow(gi, ri)}
                          className="flex h-5 w-5 items-center justify-center rounded text-slate-400 hover:bg-red-50 hover:text-red-500"
                          title="Remove"
                        >
                          <svg
                            className="h-3 w-3"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Total */}
                  <div
                    className={`mt-2 flex items-center justify-between border-t pt-2 text-xs font-semibold ${
                      totalOk
                        ? "border-green-200 text-green-600"
                        : "border-red-200 text-red-500"
                    }`}
                  >
                    <span>Total</span>
                    <span>{total.toFixed(3)}</span>
                  </div>

                  {/* Add row */}
                  <button
                    onClick={() => addRow(gi)}
                    className="mt-2 w-full rounded-md border border-dashed border-slate-300 py-1.5 text-xs font-medium text-slate-500 hover:border-primary-400 hover:bg-primary-50 hover:text-primary-600 transition-colors"
                  >
                    + Add Component
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
