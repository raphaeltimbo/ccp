"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { QuantityInput } from "../../lib/types/common";
import { TestPointInputs } from "../../lib/types/straightThrough";
import { UNIT_OPTIONS } from "../../lib/utils/units";

interface RowConfig {
  key: keyof TestPointInputs;
  label: string;
  unitOptions: string[];
  optional?: boolean;
}

const ROWS: RowConfig[] = [
  { key: "flow", label: "Flow", unitOptions: UNIT_OPTIONS.flow },
  {
    key: "suctionPressure",
    label: "Suction Pressure",
    unitOptions: UNIT_OPTIONS.pressure,
  },
  {
    key: "suctionTemperature",
    label: "Suction Temperature",
    unitOptions: UNIT_OPTIONS.temperature,
  },
  {
    key: "dischargePressure",
    label: "Discharge Pressure",
    unitOptions: UNIT_OPTIONS.pressure,
  },
  {
    key: "dischargeTemperature",
    label: "Discharge Temperature",
    unitOptions: UNIT_OPTIONS.temperature,
  },
  { key: "speed", label: "Speed", unitOptions: UNIT_OPTIONS.speed },
  {
    key: "casingDeltaT",
    label: "Casing \u0394T",
    unitOptions: UNIT_OPTIONS.temperature,
    optional: true,
  },
  {
    key: "balanceLineFlowM",
    label: "Balance Line Flow",
    unitOptions: UNIT_OPTIONS.flow_m,
    optional: true,
  },
  {
    key: "sealGasFlowM",
    label: "Seal Gas Flow",
    unitOptions: UNIT_OPTIONS.flow_m,
    optional: true,
  },
  {
    key: "sealGasTemperature",
    label: "Seal Gas Temperature",
    unitOptions: UNIT_OPTIONS.temperature,
    optional: true,
  },
];

export function TestDataSection() {
  const {
    testPoints,
    numTestPoints,
    setNumTestPoints,
    updateTestPoint,
    updateTestPointGas,
    gasCompositions,
  } = useStraightThroughStore();

  const gasNames = gasCompositions.map((g) => g.name);

  function getRowUnit(rowKey: keyof TestPointInputs): string {
    const val = testPoints[0]?.[rowKey] as QuantityInput | undefined;
    return val?.unit ?? "";
  }

  function handleUnitChange(rowKey: keyof TestPointInputs, unit: string) {
    for (let i = 0; i < numTestPoints; i++) {
      const current = testPoints[i]?.[rowKey] as QuantityInput | undefined;
      updateTestPoint(i, rowKey, {
        magnitude: current?.magnitude ?? 0,
        unit,
      });
    }
  }

  function handleValueChange(
    pointIndex: number,
    rowKey: keyof TestPointInputs,
    magnitude: number,
  ) {
    const currentUnit = getRowUnit(rowKey);
    updateTestPoint(pointIndex, rowKey, {
      magnitude,
      unit:
        currentUnit || ROWS.find((r) => r.key === rowKey)?.unitOptions[0] || "",
    });
  }

  return (
    <details className="rounded-xl border border-slate-200 bg-white shadow-sm group">
      <summary className="cursor-pointer select-none px-5 py-4 text-base font-semibold text-slate-800 hover:bg-slate-50 rounded-xl transition-colors">
        Test Data
      </summary>

      <div className="border-t border-slate-100 px-5 py-3 flex items-center gap-2">
        <label className="text-xs font-medium text-slate-500">Points:</label>
        <select
          value={numTestPoints}
          onChange={(e) => setNumTestPoints(parseInt(e.target.value))}
          className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-700"
        >
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto p-5 pt-0">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="pb-3 pr-3 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Parameter
              </th>
              <th className="pb-3 pr-3 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Unit
              </th>
              {Array.from({ length: numTestPoints }, (_, i) => (
                <th
                  key={i}
                  className="pb-3 pr-3 text-center text-[10px] font-semibold uppercase tracking-wider text-slate-400"
                >
                  Point {i + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Gas Selection row */}
            <tr className="bg-white">
              <td className="py-2 pr-3 text-sm font-medium text-slate-600 whitespace-nowrap">
                Gas Selection
              </td>
              <td className="py-2 pr-3" />
              {Array.from({ length: numTestPoints }, (_, pi) => {
                const selectedGas = testPoints[pi]?.gasSelection ?? "";
                return (
                  <td key={pi} className="py-2 pr-3">
                    <select
                      value={selectedGas}
                      onChange={(e) =>
                        updateTestPointGas(pi, e.target.value)
                      }
                      className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-700"
                    >
                      <option value="">--</option>
                      {gasNames.map((name) => (
                        <option key={name} value={name}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </td>
                );
              })}
            </tr>

            {/* Quantity rows */}
            {ROWS.map((row, rowIdx) => {
              const unitValue = getRowUnit(row.key) || row.unitOptions[0];
              const isOptional = row.optional;

              return (
                <tr
                  key={row.key}
                  className={
                    (rowIdx + 1) % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                  }
                >
                  <td className="py-2 pr-3 text-sm font-medium text-slate-600 whitespace-nowrap">
                    {row.label}
                    {isOptional && (
                      <span className="ml-1 text-[10px] text-slate-400 font-normal">
                        (opt.)
                      </span>
                    )}
                  </td>
                  <td className="py-2 pr-3">
                    <select
                      value={unitValue}
                      onChange={(e) =>
                        handleUnitChange(row.key, e.target.value)
                      }
                      className="w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-600"
                    >
                      {row.unitOptions.map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                    </select>
                  </td>
                  {Array.from({ length: numTestPoints }, (_, pi) => {
                    const val = testPoints[pi]?.[row.key] as
                      | QuantityInput
                      | undefined;
                    return (
                      <td key={pi} className="py-2 pr-3">
                        <input
                          type="number"
                          value={val?.magnitude || ""}
                          onChange={(e) =>
                            handleValueChange(
                              pi,
                              row.key,
                              parseFloat(e.target.value) || 0,
                            )
                          }
                          className="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-700 text-center"
                          placeholder="--"
                        />
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </details>
  );
}
