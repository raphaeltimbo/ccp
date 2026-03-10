import { create } from "zustand";
import { QuantityInput } from "../lib/types/common";
import {
  GasComposition,
  DataSheetInputs,
  TestPointInputs,
  OilInputs,
  FlowOrificeInputs,
  CalculationOptions,
  CalculationResponse,
} from "../lib/types/straightThrough";

// Default quantity helper
const qty = (magnitude: number, unit: string): QuantityInput => ({
  magnitude,
  unit,
});

function createDefaultDataSheet(): DataSheetInputs {
  return {
    flow: qty(0, "m³/h"),
    suctionPressure: qty(0, "bar"),
    suctionTemperature: qty(0, "degC"),
    dischargePressure: qty(0, "bar"),
    dischargeTemperature: qty(0, "degC"),
    speed: qty(0, "rpm"),
    b: qty(0, "mm"),
    D: qty(0, "mm"),
    power: qty(0, "kW"),
  };
}

function createDefaultTestPoint(): TestPointInputs {
  return {
    flow: qty(0, "m³/h"),
    suctionPressure: qty(0, "bar"),
    suctionTemperature: qty(0, "degC"),
    dischargePressure: qty(0, "bar"),
    dischargeTemperature: qty(0, "degC"),
    speed: qty(0, "rpm"),
  };
}

function createDefaultFlowOrifice(): FlowOrificeInputs {
  return {
    upstreamPressure: qty(0, "bar"),
    upstreamTemperature: qty(0, "degC"),
    pressureDrop: qty(0, "mbar"),
    D: qty(0, "mm"),
    d: qty(0, "mm"),
    tappings: "flange",
  };
}

function createDefaultOilInputs(): OilInputs {
  return {
    oilFlowJournalBearingDE: qty(0, "L/h"),
    oilFlowJournalBearingNDE: qty(0, "L/h"),
    oilFlowThrustBearingNDE: qty(0, "L/h"),
    oilInletTemperature: qty(0, "degC"),
    oilOutletTemperatureDE: qty(0, "degC"),
    oilOutletTemperatureNDE: qty(0, "degC"),
    oilSpecificHeat: null,
    oilDensity: null,
    oilIsoClassification: "VG 32",
    useIsoOil: true,
  };
}

const NUM_TEST_POINTS = 6;

interface StraightThroughState {
  // Gas compositions
  gasCompositions: GasComposition[];
  guaranteeGasName: string;
  testGasName: string;

  // Data sheet (guarantee point)
  dataSheet: DataSheetInputs;

  // Test points (array of up to 6)
  testPoints: TestPointInputs[];
  numTestPoints: number;

  // Oil inputs
  oilInputs: OilInputs;

  // Flow orifice inputs (one per test point)
  flowOrificeInputs: FlowOrificeInputs[];

  // Options
  options: CalculationOptions;

  // Results (from API response)
  results: CalculationResponse | null;
  isCalculating: boolean;

  // Actions
  setGasCompositions: (compositions: GasComposition[]) => void;
  setGuaranteeGasName: (name: string) => void;
  setTestGasName: (name: string) => void;
  updateDataSheet: (
    field: keyof DataSheetInputs,
    value: QuantityInput,
  ) => void;
  updateTestPoint: (
    index: number,
    field: keyof TestPointInputs,
    value: QuantityInput,
  ) => void;
  setNumTestPoints: (n: number) => void;
  updateOilInputs: (inputs: Partial<OilInputs>) => void;
  updateFlowOrifice: (
    index: number,
    field: keyof FlowOrificeInputs,
    value: QuantityInput | string,
  ) => void;
  updateOptions: (opts: Partial<CalculationOptions>) => void;
  setResults: (results: CalculationResponse | null) => void;
  setIsCalculating: (v: boolean) => void;
}

export const useStraightThroughStore = create<StraightThroughState>(
  (set) => ({
    // Initial state
    gasCompositions: [],
    guaranteeGasName: "",
    testGasName: "",
    dataSheet: createDefaultDataSheet(),
    testPoints: Array.from({ length: NUM_TEST_POINTS }, () =>
      createDefaultTestPoint(),
    ),
    numTestPoints: NUM_TEST_POINTS,
    oilInputs: createDefaultOilInputs(),
    flowOrificeInputs: Array.from({ length: NUM_TEST_POINTS }, () =>
      createDefaultFlowOrifice(),
    ),
    options: {
      reynoldsCorrection: false,
      bearingMechanicalLosses: false,
      polytropicMethod: "schultz",
      useFlowOrifice: false,
    },
    results: null,
    isCalculating: false,

    // Actions
    setGasCompositions: (compositions) =>
      set({ gasCompositions: compositions }),

    setGuaranteeGasName: (name) => set({ guaranteeGasName: name }),

    setTestGasName: (name) => set({ testGasName: name }),

    updateDataSheet: (field, value) =>
      set((state) => ({
        dataSheet: { ...state.dataSheet, [field]: value },
      })),

    updateTestPoint: (index, field, value) =>
      set((state) => {
        const testPoints = [...state.testPoints];
        testPoints[index] = { ...testPoints[index], [field]: value };
        return { testPoints };
      }),

    setNumTestPoints: (n) =>
      set((state) => {
        const testPoints = [...state.testPoints];
        while (testPoints.length < n) {
          testPoints.push(createDefaultTestPoint());
        }
        const flowOrificeInputs = [...state.flowOrificeInputs];
        while (flowOrificeInputs.length < n) {
          flowOrificeInputs.push(createDefaultFlowOrifice());
        }
        return {
          numTestPoints: n,
          testPoints: testPoints.slice(0, n),
          flowOrificeInputs: flowOrificeInputs.slice(0, n),
        };
      }),

    updateOilInputs: (inputs) =>
      set((state) => ({
        oilInputs: { ...state.oilInputs, ...inputs },
      })),

    updateFlowOrifice: (index, field, value) =>
      set((state) => {
        const flowOrificeInputs = [...state.flowOrificeInputs];
        flowOrificeInputs[index] = {
          ...flowOrificeInputs[index],
          [field]: value,
        };
        return { flowOrificeInputs };
      }),

    updateOptions: (opts) =>
      set((state) => ({
        options: { ...state.options, ...opts },
      })),

    setResults: (results) => set({ results }),

    setIsCalculating: (v) => set({ isCalculating: v }),
  }),
);
