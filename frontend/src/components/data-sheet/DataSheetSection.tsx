"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { QuantityField } from "../ui/QuantityField";
import { UNIT_OPTIONS } from "../../lib/utils/units";

export function DataSheetSection() {
  const {
    dataSheet,
    updateDataSheet,
    gasCompositions,
    guaranteeGasName,
    setGuaranteeGasName,
  } = useStraightThroughStore();

  return (
    <details className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <summary className="cursor-pointer select-none px-5 py-4 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 rounded-lg transition-colors">
        Data Sheet
      </summary>

      <div className="border-t border-slate-100 px-5 py-4">
        {/* Column headers */}
        <div className="flex items-center gap-3 pb-2 mb-1 border-b border-slate-100">
          <span className="w-52 shrink-0 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Parameter
          </span>
          <span className="w-24 shrink-0 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Units
          </span>
          <span className="flex-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Value
          </span>
        </div>

        {/* Gas Selection */}
        <div className="flex items-center gap-3 py-1">
          <label className="w-52 shrink-0 text-[13px] text-slate-500">
            Gas Selection
          </label>
          <div className="w-24 shrink-0" />
          <select
            value={guaranteeGasName}
            onChange={(e) => setGuaranteeGasName(e.target.value)}
            className="flex-1 rounded border border-slate-200 bg-white px-3 py-1.5 text-[13px] text-slate-700"
          >
            <option value="">Select gas...</option>
            {gasCompositions.map((gc) => (
              <option key={gc.name} value={gc.name}>
                {gc.name}
              </option>
            ))}
          </select>
        </div>

        <QuantityField
          label="Flow"
          value={dataSheet.flow}
          unitOptions={UNIT_OPTIONS.flow}
          onChange={(v) => updateDataSheet("flow", v)}
        />
        <QuantityField
          label="Suction Pressure"
          value={dataSheet.suctionPressure}
          unitOptions={UNIT_OPTIONS.pressure}
          onChange={(v) => updateDataSheet("suctionPressure", v)}
        />
        <QuantityField
          label="Suction Temperature"
          value={dataSheet.suctionTemperature}
          unitOptions={UNIT_OPTIONS.temperature}
          onChange={(v) => updateDataSheet("suctionTemperature", v)}
        />
        <QuantityField
          label="Discharge Pressure"
          value={dataSheet.dischargePressure}
          unitOptions={UNIT_OPTIONS.pressure}
          onChange={(v) => updateDataSheet("dischargePressure", v)}
        />
        <QuantityField
          label="Discharge Temperature"
          value={dataSheet.dischargeTemperature}
          unitOptions={UNIT_OPTIONS.temperature}
          onChange={(v) => updateDataSheet("dischargeTemperature", v)}
        />
        <QuantityField
          label="Gas Power"
          value={dataSheet.gasPower}
          unitOptions={UNIT_OPTIONS.power}
          onChange={(v) => updateDataSheet("gasPower", v)}
        />
        <QuantityField
          label="Shaft Power"
          value={dataSheet.shaftPower}
          unitOptions={UNIT_OPTIONS.power}
          onChange={(v) => updateDataSheet("shaftPower", v)}
        />
        <QuantityField
          label="Speed"
          value={dataSheet.speed}
          unitOptions={UNIT_OPTIONS.speed}
          onChange={(v) => updateDataSheet("speed", v)}
        />
        <QuantityField
          label="Head"
          value={dataSheet.head}
          unitOptions={UNIT_OPTIONS.head}
          onChange={(v) => updateDataSheet("head", v)}
        />
        <QuantityField
          label="Efficiency"
          value={dataSheet.efficiency}
          unitOptions={UNIT_OPTIONS.efficiency}
          onChange={(v) => updateDataSheet("efficiency", v)}
        />
        <QuantityField
          label="First Impeller Width"
          value={dataSheet.b}
          unitOptions={UNIT_OPTIONS.length}
          onChange={(v) => updateDataSheet("b", v)}
        />
        <QuantityField
          label="First Impeller Diameter"
          value={dataSheet.D}
          unitOptions={UNIT_OPTIONS.length}
          onChange={(v) => updateDataSheet("D", v)}
        />
        <QuantityField
          label="Surface Roughness"
          value={dataSheet.surfaceRoughness}
          unitOptions={UNIT_OPTIONS.length}
          onChange={(v) => updateDataSheet("surfaceRoughness", v)}
        />
        <QuantityField
          label="Casing Area"
          value={dataSheet.casingArea}
          unitOptions={UNIT_OPTIONS.area}
          onChange={(v) => updateDataSheet("casingArea", v)}
        />
      </div>
    </details>
  );
}
