from fastapi import APIRouter

from ..schemas.straight_through import StraightThroughRequest, StraightThroughResponse
from ..services.straight_through_service import calculate_straight_through

router = APIRouter(prefix="/api/straight-through", tags=["straight-through"])


@router.post("/calculate", response_model=StraightThroughResponse)
async def calculate(request: StraightThroughRequest):
    return calculate_straight_through(request)
