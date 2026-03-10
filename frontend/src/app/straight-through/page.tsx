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

  function handleCalculate() {
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

    calculation.mutate(request);
  }

  return (
    <div className="flex gap-8">
      {/* Main form content */}
      <div className="flex-1 min-w-0 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Straight-Through Compressor
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Performance test and evaluation
          </p>
        </div>

        <GasCompositionPanel />
        <DataSheetSection />
        <TestDataSection />

        {store.options.useFlowOrifice && <FlowOrificeSection />}

        {/* Calculate button */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleCalculate}
            disabled={store.isCalculating}
            className="rounded-lg bg-primary-600 px-8 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 active:bg-primary-800 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
          >
            {store.isCalculating ? (
              <span className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
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
            ) : (
              "Calculate"
            )}
          </button>

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
