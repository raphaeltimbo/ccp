"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";

const ISO_OIL_OPTIONS = ["VG 32", "VG 46"];

export function OptionsSidebar() {
  const { options, updateOptions, oilInputs, updateOilInputs } =
    useStraightThroughStore();

  return (
    <aside className="w-72 shrink-0 rounded-xl border border-slate-200 bg-white shadow-sm self-start sticky top-8">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Calculation Options
        </h2>
      </div>

      <div className="p-5 space-y-4">
        {/* Checkboxes */}
        <label className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer group">
          <input
            type="checkbox"
            checked={options.reynoldsCorrection}
            onChange={(e) =>
              updateOptions({ reynoldsCorrection: e.target.checked })
            }
            className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="group-hover:text-slate-900">Reynolds correction</span>
        </label>

        <label className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer group">
          <input
            type="checkbox"
            checked={options.bearingMechanicalLosses}
            onChange={(e) =>
              updateOptions({ bearingMechanicalLosses: e.target.checked })
            }
            className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="group-hover:text-slate-900">Bearing mechanical losses</span>
        </label>

        {/* Polytropic method */}
        <div>
          <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Polytropic method
          </label>
          <select
            value={options.polytropicMethod}
            onChange={(e) =>
              updateOptions({ polytropicMethod: e.target.value })
            }
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
          >
            <option value="schultz">Schultz</option>
            <option value="huntington">Huntington</option>
          </select>
        </div>

        {/* Flow orifice */}
        <label className="flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer group">
          <input
            type="checkbox"
            checked={options.useFlowOrifice}
            onChange={(e) =>
              updateOptions({ useFlowOrifice: e.target.checked })
            }
            className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="group-hover:text-slate-900">Use flow orifice</span>
        </label>

        {/* Oil properties */}
        <div className="border-t border-slate-100 pt-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Oil Properties
          </h3>

          <label className="mb-3 flex items-center gap-2.5 text-sm text-slate-700 cursor-pointer group">
            <input
              type="checkbox"
              checked={oilInputs.useIsoOil ?? true}
              onChange={(e) => updateOilInputs({ useIsoOil: e.target.checked })}
              className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="group-hover:text-slate-900">Use ISO classification</span>
          </label>

          {oilInputs.useIsoOil ? (
            <div>
              <label className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-500">
                ISO classification
              </label>
              <select
                value={oilInputs.oilIsoClassification ?? "VG 32"}
                onChange={(e) =>
                  updateOilInputs({ oilIsoClassification: e.target.value })
                }
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              >
                {ISO_OIL_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-500">
                  Specific heat (J/(kg*degC))
                </label>
                <input
                  type="number"
                  value={oilInputs.oilSpecificHeat?.magnitude ?? 0}
                  onChange={(e) =>
                    updateOilInputs({
                      oilSpecificHeat: {
                        magnitude: parseFloat(e.target.value) || 0,
                        unit: "J/(kg*degC)",
                      },
                    })
                  }
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-500">
                  Density (kg/m³)
                </label>
                <input
                  type="number"
                  value={oilInputs.oilDensity?.magnitude ?? 0}
                  onChange={(e) =>
                    updateOilInputs({
                      oilDensity: {
                        magnitude: parseFloat(e.target.value) || 0,
                        unit: "kg/m**3",
                      },
                    })
                  }
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
