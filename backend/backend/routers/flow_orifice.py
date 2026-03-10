from fastapi import APIRouter

from ..schemas.flow_orifice import FlowOrificeRequest, FlowOrificeResponse
from ..services.flow_orifice_service import calculate_flow_orifice

router = APIRouter(prefix="/api/flow-orifice", tags=["flow-orifice"])


@router.post("/calculate", response_model=FlowOrificeResponse)
async def calculate(request: FlowOrificeRequest):
    return calculate_flow_orifice(request)
