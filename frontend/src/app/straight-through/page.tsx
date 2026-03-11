"use client";

import { useStraightThroughStore } from "../../stores/straightThroughStore";
import { useCalculation } from "../../hooks/useCalculation";
import { OptionsSidebar } from "../../components/options/OptionsSidebar";
import { GasCompositionPanel } from "../../components/gas-composition/GasCompositionPanel";
import { DataSheetSection } from "../../components/data-sheet/DataSheetSection";
import { TestDataSection } from "../../components/test-data/TestDataSection";
import { FlowOrificeSection } from "../../components/flow-orifice/FlowOrificeSection";
import { ResultsPanel } from "../../components/results/ResultsPanel";
import { CalculationRequest } from "../../lib/types/straightThrough";

export default function StraightThroughPage() {
  const store = useStraightThroughStore();
  const calculation = useCalculation();

  function buildRequest(): CalculationRequest {
    const request: CalculationRequest = {
      gasCompositions: store.gasCompositions,
      guaranteeGas: store.guaranteeGasName,
      testGas: store.testGasName,
      dataSheet: store.dataSheet,
      testPoints: store.testPoints.slice(0, store.numTestPoints),
      options: store.options,
    };

    if (store.options.bearingMechanicalLosses) {
      request.oilInputs = store.oilInputs;
    }

    if (store.options.useFlowOrifice) {
      request.flowOrifice = store.flowOrificeInputs.slice(
        0,
        store.numTestPoints,
      );
    }

    return request;
  }

  function handleCalculate() {
    calculation.mutate(buildRequest());
  }

  function handleCalculateSpeed() {
    calculation.mutate({ ...buildRequest(), calculationType: "speed" });
  }

  function handleCalculateFlowrate() {
    calculation.mutate({ ...buildRequest(), calculationType: "flowrate" });
  }

  const buttonClass =
    "flex-1 rounded-lg bg-slate-800 px-4 py-2.5 text-[13px] font-semibold text-white hover:bg-slate-700 active:bg-slate-900 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors";

  const spinner = (
    <span className="flex items-center justify-center gap-2">
      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      Calculating...
    </span>
  );

  return (
    <div className="flex gap-8">
      {/* Main form content */}
      <div className="flex-1 min-w-0 space-y-4">
        <h1 className="text-xl font-bold text-slate-800">
          Performance Test Straight-Through Compressor
        </h1>

        <GasCompositionPanel />
        <DataSheetSection />
        <TestDataSection />

        {store.options.useFlowOrifice && <FlowOrificeSection />}

        {/* Action buttons */}
        <div className="space-y-4">
          <div className="flex gap-4">
            <button
              onClick={handleCalculate}
              disabled={store.isCalculating}
              className={buttonClass}
            >
              {store.isCalculating ? spinner : "Calculate"}
            </button>
            <button
              onClick={handleCalculateSpeed}
              disabled={store.isCalculating}
              className={buttonClass}
            >
              {store.isCalculating ? spinner : "Calculate Speed"}
            </button>
            <button
              onClick={handleCalculateFlowrate}
              disabled={store.isCalculating}
              className={buttonClass}
            >
              {store.isCalculating ? spinner : "Calculate Flowrate"}
            </button>
          </div>

          {calculation.isError && (
            <span className="text-sm text-red-600 bg-red-50 px-3 py-1.5 rounded-md">
              Calculation failed. Check inputs and try again.
            </span>
          )}
        </div>

        {/* Results */}
        <ResultsPanel />
      </div>

      {/* Right sidebar */}
      <OptionsSidebar />
    </div>
  );
}
