import pytest
from ccp.config.units import check_units, Q_, units


def test_new_units_loaded():
    speed = Q_(1, 'RPM')
    assert speed.magnitude == 1


@pytest.fixture
def auxiliary_function():
    @check_units
    def func(p=None, T=None, rho=None, speed=None, flow_v=None, flow_m=None,
             h=None, s=None, b=None, D=None, head=None):
        return p, T, rho, speed, flow_v, flow_m, h, s, b, D, head
    return func


def test_units(auxiliary_function):
    results = auxiliary_function(p=1, T=1, rho=1, speed=1, flow_v=1, flow_m=1,
                                 h=1, s=1, b=1, D=1, head=1)
    # check if all available units are tested
    assert len(results) == len(units)

    p, T, rho, speed, flow_v, flow_m, h, s, b, D, head = results

    assert p.magnitude == 1
    assert p.units == 'pascal'

    assert T.magnitude == 1
    assert T.units == 'kelvin'

    assert rho.magnitude == 1
    assert rho.units == 'kilogram/meter**3'

    assert speed.magnitude == 1
    assert speed.units == 'radian/second'

    assert flow_v.magnitude == 1
    assert flow_v.units == 'meter**3/second'

    assert flow_m.magnitude == 1
    assert flow_m.units == 'kilogram/second'

    assert h.magnitude == 1
    assert h.units == 'joule/kilogram'

    assert s.magnitude == 1
    assert s.units == 'joule/(kelvin kilogram)'

    assert b.magnitude == 1
    assert b.units == 'meter'

    assert D.magnitude == 1
    assert D.units == 'meter'

    assert head.magnitude == 1
    assert head.units == 'joule/kilogram'


def test_unit_Q_(auxiliary_function):
    results = auxiliary_function(p=Q_(1, 'pascal'), T=Q_(1, 'kelvin'),
                                 rho=Q_(1, 'kilogram/meter**3'),
                                 speed=Q_(1, 'radian/second'),
                                 flow_v=Q_(1, 'meter**3/second'),
                                 flow_m=Q_(1, 'kilogram/second'),
                                 h=Q_(1, 'joule/kilogram'),
                                 s=Q_(1, 'joule/(kelvin kilogram)'),
                                 b=Q_(1, 'meter'),
                                 D=Q_(1, 'meter'),
                                 head=Q_(1, 'joule/kilogram'))
    # check if all available units are tested
    assert len(results) == len(units)

    p, T, rho, speed, flow_v, flow_m, h, s, b, D, head = results

    assert p.magnitude == 1
    assert p.units == 'pascal'

    assert T.magnitude == 1
    assert T.units == 'kelvin'

    assert rho.magnitude == 1
    assert rho.units == 'kilogram/meter**3'

    assert speed.magnitude == 1
    assert speed.units == 'radian/second'

    assert flow_v.magnitude == 1
    assert flow_v.units == 'meter**3/second'

    assert flow_m.magnitude == 1
    assert flow_m.units == 'kilogram/second'

    assert h.magnitude == 1
    assert h.units == 'joule/kilogram'

    assert s.magnitude == 1
    assert s.units == 'joule/(kelvin kilogram)'

    assert b.magnitude == 1
    assert b.units == 'meter'

    assert D.magnitude == 1
    assert D.units == 'meter'

    assert head.magnitude == 1
    assert head.units == 'joule/kilogram'


def test_unit_Q_conversion(auxiliary_function):
    results = auxiliary_function(p=Q_(1, 'bar'), T=Q_(1, 'celsius'),
                                 rho=Q_(1, 'lb/foot**3'),
                                 speed=Q_(1, 'RPM'),
                                 flow_v=Q_(1, 'foot**3/second'),
                                 flow_m=Q_(1, 'lb/second'),
                                 h=Q_(1, 'btu/lb'),
                                 s=Q_(1, 'btu/(degF lb)'),
                                 b=Q_(1, 'inches'),
                                 D=Q_(1, 'inches'),
                                 head=Q_(1, 'btu/lb'))

    # check if all available units are tested
    assert len(results) == len(units)

    p, T, rho, speed, flow_v, flow_m, h, s, b, D, head = results

    assert p.magnitude == 1e5
    assert p.units == 'pascal'

    assert T.magnitude == 274.15
    assert T.units == 'kelvin'

    assert rho.magnitude == 16.018463373960145
    assert rho.units == 'kilogram/meter**3'

    assert speed.magnitude == 0.10471975511965977
    assert speed.units == 'radian/second'

    assert flow_v.magnitude == 0.028316846591999994
    assert flow_v.units == 'meter**3/second'

    assert flow_m.magnitude == 0.45359237
    assert flow_m.units == 'kilogram/second'

    assert h.magnitude == 2326.0
    assert h.units == 'joule/kilogram'

    assert s.magnitude == 4186.8
    assert s.units == 'joule/(kelvin kilogram)'

    assert b.magnitude == 0.0254
    assert b.units == 'meter'

    assert D.magnitude == 0.0254
    assert D.units == 'meter'

    assert head.magnitude == 2326.0
    assert head.units == 'joule/kilogram'