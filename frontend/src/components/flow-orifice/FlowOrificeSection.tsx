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
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-800">
          Flow Orifice
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Orifice flow measurement parameters
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-100 px-5">
        {Array.from({ length: numTestPoints }, (_, i) => (
          <button
            key={i}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
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
      <div className="p-5 space-y-3">
        {fields.map((f) => {
          const val = fo[f.key] as QuantityInput;
          return (
            <div
              key={f.key}
              className="grid grid-cols-[1fr_auto] items-center gap-2"
            >
              <label className="text-sm font-medium text-slate-600">
                {f.label}
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  value={val.magnitude || ""}
                  onChange={(e) =>
                    handleQtyChange(f.key, parseFloat(e.target.value) || 0)
                  }
                  className="w-32 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
                  placeholder="0"
                />
                <select
                  value={val.unit}
                  onChange={(e) => handleUnitChange(f.key, e.target.value)}
                  className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-600"
                >
                  {f.unitOptions.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          );
        })}

        {/* Tappings dropdown */}
        <div className="grid grid-cols-[1fr_auto] items-center gap-2">
          <label className="text-sm font-medium text-slate-600">
            Tappings
          </label>
          <select
            value={fo.tappings}
            onChange={(e) =>
              updateFlowOrifice(activeTab, "tappings", e.target.value)
            }
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-600"
          >
            {TAPPING_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}
