"use client";

import { useState } from "react";
import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { QuantityInput } from "../../lib/types/common";
import { UNIT_OPTIONS } from "../../lib/utils/units";

const TAPPING_OPTIONS = ["flange", "corner", "D D/2"];

export function FlowOrificeSection() {
  const { flowOrificeInputs, numTestPoints, updateFlowOrifice } =
    useStraightThroughStore();

  const [activeTab, setActiveTab] = useState(0);

  const fo = flowOrificeInputs[activeTab];
  if (!fo) return null;

  function handleQtyChange(
    field:
      | "upstreamPressure"
      | "upstreamTemperature"
      | "pressureDrop"
      | "D"
      | "d",
    magnitude: number,
  ) {
    const current = fo[field] as QuantityInput;
    updateFlowOrifice(activeTab, field, {
      magnitude,
      unit: current.unit,
    });
  }

  function handleUnitChange(
    field:
      | "upstreamPressure"
      | "upstreamTemperature"
      | "pressureDrop"
      | "D"
      | "d",
    unit: string,
  ) {
    const current = fo[field] as QuantityInput;
    updateFlowOrifice(activeTab, field, {
      magnitude: current.magnitude,
      unit,
    });
  }

  const fields: {
    key:
      | "upstreamPressure"
      | "upstreamTemperature"
      | "pressureDrop"
      | "D"
      | "d";
    label: string;
    unitOptions: string[];
  }[] = [
    {
      key: "upstreamPressure",
      label: "Upstream Pressure",
      unitOptions: UNIT_OPTIONS.pressure,
    },
    {
      key: "upstreamTemperature",
      label: "Upstream Temperature",
      unitOptions: UNIT_OPTIONS.temperature,
    },
    {
      key: "pressureDrop",
      label: "Pressure Drop",
      unitOptions: UNIT_OPTIONS.pressure,
    },
    {
      key: "D",
      label: "Pipe Diameter (D)",
      unitOptions: UNIT_OPTIONS.length,
    },
    {
      key: "d",
      label: "Orifice Diameter (d)",
      unitOptions: UNIT_OPTIONS.length,
    },
  ];

  return (
    <details className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <summary className="cursor-pointer select-none px-5 py-4 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 rounded-lg transition-colors">
        Flowrate Calculation
      </summary>

      {/* Tabs */}
      <div className="flex border-t border-slate-100 px-5">
        {Array.from({ length: numTestPoints }, (_, i) => (
          <button
            key={i}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-[13px] font-medium transition-colors border-b-2 -mb-px ${
              activeTab === i
                ? "border-primary-500 text-primary-600"
                : "border-transparent text-slate-400 hover:text-slate-600"
            }`}
          >
            Point {i + 1}
          </button>
        ))}
      </div>

      {/* Fields */}
      <div className="p-5 space-y-2">
        {fields.map((f) => {
          const val = fo[f.key] as QuantityInput;
          return (
            <div
              key={f.key}
              className="flex items-center gap-3 py-1"
            >
              <label className="w-52 shrink-0 text-[13px] text-slate-500">
                {f.label}
              </label>
              <select
                value={val.unit}
                onChange={(e) => handleUnitChange(f.key, e.target.value)}
                className="w-24 shrink-0 rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600"
              >
                {f.unitOptions.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
              <input
                type="number"
                value={val.magnitude || ""}
                onChange={(e) =>
                  handleQtyChange(f.key, parseFloat(e.target.value) || 0)
                }
                className="flex-1 rounded border border-slate-200 bg-white px-3 py-1.5 text-[13px] text-slate-700"
                placeholder="0"
              />
            </div>
          );
        })}

        {/* Tappings dropdown */}
        <div className="flex items-center gap-3 py-1">
          <label className="w-52 shrink-0 text-[13px] text-slate-500">
            Tappings
          </label>
          <select
            value={fo.tappings}
            onChange={(e) =>
              updateFlowOrifice(activeTab, "tappings", e.target.value)
            }
            className="w-24 shrink-0 rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600"
          >
            {TAPPING_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>
    </details>
  );
}
