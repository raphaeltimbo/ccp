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
  { key: "suctionPressure", label: "Suction Pressure", unitOptions: UNIT_OPTIONS.pressure },
  { key: "suctionTemperature", label: "Suction Temperature", unitOptions: UNIT_OPTIONS.temperature },
  { key: "dischargePressure", label: "Discharge Pressure", unitOptions: UNIT_OPTIONS.pressure },
  { key: "dischargeTemperature", label: "Discharge Temperature", unitOptions: UNIT_OPTIONS.temperature },
  { key: "speed", label: "Speed", unitOptions: UNIT_OPTIONS.speed },
  { key: "casingDeltaT", label: "Casing \u0394T", unitOptions: UNIT_OPTIONS.temperature, optional: true },
  { key: "balanceLineFlowM", label: "Balance Line Flow", unitOptions: UNIT_OPTIONS.flow_m, optional: true },
  { key: "sealGasFlowM", label: "Seal Gas Flow", unitOptions: UNIT_OPTIONS.flow_m, optional: true },
  { key: "sealGasTemperature", label: "Seal Gas Temperature", unitOptions: UNIT_OPTIONS.temperature, optional: true },
];

const cellInput =
  "w-full rounded border border-slate-200 bg-white px-2 py-1.5 text-[12px] text-slate-700 text-center";
const cellSelect =
  "w-full rounded border border-slate-200 bg-slate-50 px-1.5 py-1.5 text-[12px] text-slate-600";

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
      unit: currentUnit || ROWS.find((r) => r.key === rowKey)?.unitOptions[0] || "",
    });
  }

  return (
    <details className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <summary className="cursor-pointer select-none px-5 py-4 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 rounded-lg transition-colors">
        Test Data
      </summary>

      <div className="border-t border-slate-100 px-5 py-3 flex items-center gap-2">
        <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Points:
        </label>
        <select
          value={numTestPoints}
          onChange={(e) => setNumTestPoints(parseInt(e.target.value))}
          className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-[13px] text-slate-700"
        >
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto p-5 pt-0">
        <table className="w-full">
          <thead>
            <tr>
              <th className="pb-2 pr-3 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-40">
                Parameter
              </th>
              <th className="pb-2 pr-3 text-left text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-20">
                Units
              </th>
              {Array.from({ length: numTestPoints }, (_, i) => (
                <th
                  key={i}
                  className="pb-2 pr-2 text-center text-[10px] font-semibold uppercase tracking-wider text-slate-400"
                >
                  Point {i + 1}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Gas Selection row */}
            <tr>
              <td className="py-1.5 pr-3 text-[13px] text-slate-500 whitespace-nowrap">
                Gas Selection
              </td>
              <td className="py-1.5 pr-3" />
              {Array.from({ length: numTestPoints }, (_, pi) => (
                <td key={pi} className="py-1.5 pr-2">
                  <select
                    value={testPoints[pi]?.gasSelection ?? ""}
                    onChange={(e) => updateTestPointGas(pi, e.target.value)}
                    className={cellSelect}
                  >
                    <option value="">--</option>
                    {gasNames.map((name) => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </td>
              ))}
            </tr>

            {/* Quantity rows */}
            {ROWS.map((row, rowIdx) => {
              const unitValue = getRowUnit(row.key) || row.unitOptions[0];

              return (
                <tr
                  key={row.key}
                  className={rowIdx % 2 === 0 ? "" : "bg-slate-50/40"}
                >
                  <td className="py-1.5 pr-3 text-[13px] text-slate-500 whitespace-nowrap">
                    {row.label}
                    {row.optional && (
                      <span className="ml-1 text-[10px] text-slate-300">
                        opt.
                      </span>
                    )}
                  </td>
                  <td className="py-1.5 pr-3">
                    <select
                      value={unitValue}
                      onChange={(e) => handleUnitChange(row.key, e.target.value)}
                      className={cellSelect}
                    >
                      {row.unitOptions.map((u) => (
                        <option key={u} value={u}>{u}</option>
                      ))}
                    </select>
                  </td>
                  {Array.from({ length: numTestPoints }, (_, pi) => {
                    const val = testPoints[pi]?.[row.key] as QuantityInput | undefined;
                    return (
                      <td key={pi} className="py-1.5 pr-2">
                        <input
                          type="number"
                          value={val?.magnitude || ""}
                          onChange={(e) =>
                            handleValueChange(pi, row.key, parseFloat(e.target.value) || 0)
                          }
                          className={cellInput}
                          placeholder=""
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
