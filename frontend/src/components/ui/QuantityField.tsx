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
    <div className="flex items-center gap-3 py-1">
      <label className="w-52 shrink-0 text-[13px] text-slate-500">
        {label}
      </label>
      <select
        value={value.unit}
        onChange={(e) => onChange({ ...value, unit: e.target.value })}
        disabled={disabled}
        className="w-24 shrink-0 rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-[13px] text-slate-600 disabled:opacity-50"
      >
        {unitOptions.map((u) => (
          <option key={u} value={u}>
            {u}
          </option>
        ))}
      </select>
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
        className="flex-1 rounded border border-slate-200 bg-white px-3 py-1.5 text-[13px] text-slate-700 placeholder:text-slate-300 disabled:opacity-50"
        placeholder=""
      />
    </div>
  );
}
