"use client";

import { QuantityInput } from "../../lib/types/common";

interface QuantityFieldProps {
  label: string;
  value: QuantityInput;
  unitOptions: string[];
  onChange: (value: QuantityInput) => void;
  disabled?: boolean;
}

export function QuantityField({
  label,
  value,
  unitOptions,
  onChange,
  disabled = false,
}: QuantityFieldProps) {
  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-2">
      <label className="text-sm font-medium text-slate-600">{label}</label>
      <div className="flex items-center gap-1.5">
        <input
          type="number"
          value={value.magnitude || ""}
          onChange={(e) =>
            onChange({
              ...value,
              magnitude: parseFloat(e.target.value) || 0,
            })
          }
          disabled={disabled}
          className="w-32 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 disabled:bg-slate-50 disabled:text-slate-400"
          placeholder="0"
        />
        <select
          value={value.unit}
          onChange={(e) => onChange({ ...value, unit: e.target.value })}
          disabled={disabled}
          className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-600 disabled:bg-slate-50 disabled:text-slate-400"
        >
          {unitOptions.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
