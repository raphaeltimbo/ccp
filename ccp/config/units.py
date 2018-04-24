from .. import Q_

units = {'p': 'pascal',
         'T': 'kelvin',
         'rho': 'kilogram/m**3',
         'speed': 'radian/second',
         'flow_v': 'meter**3/second',
         'flow_m': 'kilogram/second',
         'h': 'joule/kilogram',
         's': 'joule/(kelvin kilogram)',
         'b': 'meter',
         'D': 'meter',
         'head': 'joule/kilogram'}


def check_units(func):
    """Wrapper to check and convert units to base_units."""
    def inner(*args, **kwargs):
        base_unit_kwargs = {}
        for k, v in kwargs.items():
            if k in units and v is not None:
                try:
                    base_unit_kwargs[k] = v.to(units[k])
                except AttributeError:
                    base_unit_kwargs[k] = Q_(v, units[k])
            else:
                base_unit_kwargs[k] = v

        return func(*args, **base_unit_kwargs)
    return inner
