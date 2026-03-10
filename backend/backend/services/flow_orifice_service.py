import ccp

from ..schemas.flow_orifice import FlowOrificeRequest
from .quantity_utils import to_q


def calculate_flow_orifice(req: FlowOrificeRequest) -> dict:
    """Create a FlowOrifice from the request and return mass/volumetric flow."""
    state = ccp.State(
        p=to_q(req.upstream_pressure),
        T=to_q(req.upstream_temperature),
        fluid=req.fluid.components,
    )

    fo = ccp.FlowOrifice(
        state=state,
        delta_p=to_q(req.pressure_drop),
        D=to_q(req.D),
        d=to_q(req.d),
        tappings=req.tappings,
    )

    return {
        "flow_m": {
            "magnitude": float(fo.flow_m.to("kg/s").magnitude),
            "unit": "kg/s",
        },
        "flow_v": {
            "magnitude": float(fo.flow_v.to("m³/s").magnitude),
            "unit": "m³/s",
        },
    }
