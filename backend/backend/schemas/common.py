from pydantic import BaseModel


class QuantityInput(BaseModel):
    magnitude: float
    unit: str


class FluidComposition(BaseModel):
    """Dict of component name to molar fraction."""

    components: dict[str, float]  # e.g. {"methane": 0.8, "ethane": 0.2}


class StateInput(BaseModel):
    pressure: QuantityInput
    temperature: QuantityInput
    fluid: FluidComposition
