"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { QuantityField } from "../ui/QuantityField";
import { UNIT_OPTIONS } from "../../lib/utils/units";

export function DataSheetSection() {
  const { dataSheet, updateDataSheet, options } = useStraightThroughStore();

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-800">Data Sheet</h2>
        <p className="text-xs text-slate-400 mt-0.5">Guarantee point parameters</p>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
          <QuantityField
            label="Flow"
            value={dataSheet.flow}
            unitOptions={UNIT_OPTIONS.flow}
            onChange={(v) => updateDataSheet("flow", v)}
          />
          <QuantityField
            label="Speed"
            value={dataSheet.speed}
            unitOptions={UNIT_OPTIONS.speed}
            onChange={(v) => updateDataSheet("speed", v)}
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
            label="Impeller Width (b)"
            value={dataSheet.b}
            unitOptions={UNIT_OPTIONS.length}
            onChange={(v) => updateDataSheet("b", v)}
          />
          <QuantityField
            label="Impeller Diameter (D)"
            value={dataSheet.D}
            unitOptions={UNIT_OPTIONS.length}
            onChange={(v) => updateDataSheet("D", v)}
          />
          {options.bearingMechanicalLosses && (
            <QuantityField
              label="Power"
              value={dataSheet.power}
              unitOptions={UNIT_OPTIONS.power}
              onChange={(v) => updateDataSheet("power", v)}
            />
          )}
        </div>
      </div>
    </section>
  );
}
