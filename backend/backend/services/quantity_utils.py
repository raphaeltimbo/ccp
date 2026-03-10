from ccp.config.units import Q_
from backend.schemas.common import QuantityInput


def to_q(qi: QuantityInput):
    """Convert a QuantityInput to a pint Quantity."""
    return Q_(qi.magnitude, qi.unit)
