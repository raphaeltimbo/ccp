"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";

const ISO_OIL_OPTIONS = ["VG 32", "VG 46"];

const PRESSURE_UNITS = [
  "bar",
  "kgf/cm²",
  "barg",
  "Pa",
  "kPa",
  "MPa",
  "psi",
  "mm*H2O*g0",
];

const POLYTROPIC_METHODS: Record<string, string> = {
  "Sandberg-Colby": "sandberg_colby",
  "Sandberg-Colby Multistep": "sandberg_colby_multistep",
  Huntington: "huntington",
  "Mallen-Saville": "mallen_saville",
  Schultz: "schultz",
};

function Checkbox({
  checked,
  onChange,
  label,
  extra,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  extra?: React.ReactNode;
}) {
  return (
    <label className="flex items-center gap-2.5 text-[13px] text-slate-600 cursor-pointer group">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="group-hover:text-slate-800">{label}</span>
      {extra}
    </label>
  );
}

export function OptionsSidebar() {
  const { options, updateOptions, oilInputs, updateOilInputs } =
    useStraightThroughStore();

  return (
    <aside className="w-64 shrink-0 rounded-lg border border-slate-200 bg-white shadow-sm self-start sticky top-8">
      <div className="border-b border-slate-100 px-4 py-3">
        <h2 className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Options
        </h2>
      </div>

      <div className="p-4 space-y-3">
        <Checkbox
          checked={options.reynoldsCorrection}
          onChange={(v) => updateOptions({ reynoldsCorrection: v })}
          label="Reynolds Correction"
        />
        <Checkbox
          checked={options.casingHeatLoss}
          onChange={(v) => updateOptions({ casingHeatLoss: v })}
          label="Casing Heat Loss"
        />
        <Checkbox
          checked={options.bearingMechanicalLosses}
          onChange={(v) => updateOptions({ bearingMechanicalLosses: v })}
          label="Bearing Mechanical Losses"
        />
        <Checkbox
          checked={options.calculateLeakages}
          onChange={(v) => updateOptions({ calculateLeakages: v })}
          label="Calculate Leakages"
        />
        <Checkbox
          checked={options.sealGasFlow}
          onChange={(v) => updateOptions({ sealGasFlow: v })}
          label="Seal Gas Flow"
        />
        <Checkbox
          checked={options.variableSpeed}
          onChange={(v) => updateOptions({ variableSpeed: v })}
          label="Variable Speed"
        />
        <Checkbox
          checked={options.showPoints}
          onChange={(v) => updateOptions({ showPoints: v })}
          label="Show Points"
          extra={
            <span
              className="ml-auto text-[11px] text-slate-400 cursor-help"
              title="If marked, shows points in the plotted curves in addition to interpolation."
            >
              ?
            </span>
          }
        />

        {/* Ambient Pressure */}
        <div className="pt-2">
          <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Ambient Pressure
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="any"
              value={options.ambientPressure.magnitude}
              onChange={(e) =>
                updateOptions({
                  ambientPressure: {
                    magnitude: parseFloat(e.target.value) || 0,
                    unit: options.ambientPressure.unit,
                  },
                })
              }
              className="w-1/2 rounded border border-slate-200 bg-white px-2 py-1.5 text-[13px] text-slate-700"
            />
            <select
              value={options.ambientPressure.unit}
              onChange={(e) =>
                updateOptions({
                  ambientPressure: {
                    magnitude: options.ambientPressure.magnitude,
                    unit: e.target.value,
                  },
                })
              }
              className="w-1/2 rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600"
            >
              {PRESSURE_UNITS.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </div>
        </div>

        <Checkbox
          checked={options.useFlowOrifice}
          onChange={(v) => updateOptions({ useFlowOrifice: v })}
          label="Use Flow Orifice"
        />

        {/* Oil properties */}
        <div className="border-t border-slate-100 pt-3">
          <h3 className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Test Lube Oil
          </h3>

          <div className="space-y-3">
            <Checkbox
              checked={!(oilInputs.useIsoOil ?? true)}
              onChange={(v) => updateOilInputs({ useIsoOil: !v })}
              label="Specific Heat"
            />

            {!(oilInputs.useIsoOil ?? true) && (
              <div className="space-y-2 pl-7">
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={oilInputs.oilSpecificHeat?.magnitude ?? 2.03}
                    onChange={(e) =>
                      updateOilInputs({
                        oilSpecificHeat: {
                          magnitude: parseFloat(e.target.value) || 0,
                          unit: "kJ/(kg*degC)",
                        },
                      })
                    }
                    className="w-1/2 rounded border border-slate-200 bg-white px-2 py-1.5 text-[13px] text-slate-700"
                  />
                  <span className="flex items-center text-[12px] text-slate-400">
                    kJ/(kg*K)
                  </span>
                </div>
                <div>
                  <label className="mb-1 block text-[12px] text-slate-500">
                    Density
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={oilInputs.oilDensity?.magnitude ?? 846.9}
                      onChange={(e) =>
                        updateOilInputs({
                          oilDensity: {
                            magnitude: parseFloat(e.target.value) || 0,
                            unit: "kg/m**3",
                          },
                        })
                      }
                      className="w-1/2 rounded border border-slate-200 bg-white px-2 py-1.5 text-[13px] text-slate-700"
                    />
                    <span className="flex items-center text-[12px] text-slate-400">
                      kg/m³
                    </span>
                  </div>
                </div>
              </div>
            )}

            <Checkbox
              checked={oilInputs.useIsoOil ?? true}
              onChange={(v) => updateOilInputs({ useIsoOil: v })}
              label="Oil ISO Classification"
            />

            {(oilInputs.useIsoOil ?? true) && (
              <select
                value={oilInputs.oilIsoClassification ?? "VG 32"}
                onChange={(e) =>
                  updateOilInputs({ oilIsoClassification: e.target.value })
                }
                className="ml-7 w-[calc(100%-1.75rem)] rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600"
              >
                {ISO_OIL_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* Polytropic method */}
        <div className="border-t border-slate-100 pt-3">
          <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Polytropic Method
          </label>
          <select
            value={
              Object.entries(POLYTROPIC_METHODS).find(
                ([, v]) => v === options.polytropicMethod,
              )?.[0] ?? "Sandberg-Colby"
            }
            onChange={(e) =>
              updateOptions({
                polytropicMethod: POLYTROPIC_METHODS[e.target.value],
              })
            }
            className="w-full rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600"
          >
            {Object.keys(POLYTROPIC_METHODS).map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </aside>
  );
}
