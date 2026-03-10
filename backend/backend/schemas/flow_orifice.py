from pydantic import BaseModel

from .common import FluidComposition, QuantityInput


class FlowOrificeRequest(BaseModel):
    upstream_pressure: QuantityInput
    upstream_temperature: QuantityInput
    fluid: FluidComposition
    pressure_drop: QuantityInput
    D: QuantityInput  # pipe diameter
    d: QuantityInput  # orifice diameter
    tappings: str  # "flange", "corner", or "D D/2"


class FlowOrificeResponse(BaseModel):
    flow_m: dict  # {magnitude: float, unit: str}
    flow_v: dict  # {magnitude: float, unit: str}
