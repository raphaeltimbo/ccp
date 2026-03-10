from pydantic import BaseModel

from .common import FluidComposition, QuantityInput


class GasCompositionInput(BaseModel):
    name: str
    components: dict[str, float]


class DataSheetInput(BaseModel):
    flow: QuantityInput
    suction_pressure: QuantityInput
    suction_temperature: QuantityInput
    discharge_pressure: QuantityInput
    discharge_temperature: QuantityInput
    speed: QuantityInput
    b: QuantityInput  # impeller width
    D: QuantityInput  # impeller diameter
    power: QuantityInput | None = None
    power_shaft: QuantityInput | None = None
    surface_roughness: QuantityInput | None = None
    casing_area: QuantityInput | None = None


class TestPointInput(BaseModel):
    flow: QuantityInput
    suction_pressure: QuantityInput
    suction_temperature: QuantityInput
    discharge_pressure: QuantityInput
    discharge_temperature: QuantityInput
    speed: QuantityInput
    gas_name: str  # name of gas to use from gas_compositions
    casing_delta_T: QuantityInput | None = None
    balance_line_flow_m: QuantityInput | None = None
    seal_gas_flow_m: QuantityInput | None = None
    seal_gas_temperature: QuantityInput | None = None
    oil_flow_journal_bearing_de: QuantityInput | None = None
    oil_flow_journal_bearing_nde: QuantityInput | None = None
    oil_flow_thrust_bearing_nde: QuantityInput | None = None
    oil_inlet_temperature: QuantityInput | None = None
    oil_outlet_temperature_de: QuantityInput | None = None
    oil_outlet_temperature_nde: QuantityInput | None = None


class OilInput(BaseModel):
    oil_specific_heat: QuantityInput | None = None
    oil_density: QuantityInput | None = None
    oil_iso_classification: str | None = None  # "VG 32" or "VG 46"
    use_iso_oil: bool = False


class CalculationOptions(BaseModel):
    reynolds_correction: bool = False
    bearing_mechanical_losses: bool = False
    casing_heat_loss: bool = False
    calculate_leakages: bool = True
    seal_gas_flow: bool = True
    variable_speed: bool = False
    calculate_speed_to_match: bool = False


class StraightThroughRequest(BaseModel):
    gas_compositions: list[GasCompositionInput]
    guarantee_gas: str  # name of gas to use for guarantee point
    data_sheet: DataSheetInput
    test_points: list[TestPointInput]
    oil_inputs: OilInput | None = None
    options: CalculationOptions


class CellHighlight(BaseModel):
    row: str
    col: str
    color: str  # "green" or "red"


class StraightThroughResponse(BaseModel):
    results: dict  # Row label -> {col_label: value}
    highlights: list[CellHighlight]
    plots: dict  # plot_name -> Plotly figure JSON
    speed_operational_rpm: float
