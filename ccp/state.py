from copy import copy
from warnings import warn

import CoolProp.CoolProp as CP
import numpy as np
import ccp.config
from scipy.optimize import newton
from plotly import graph_objects as go
from itertools import combinations
from . import _RP

from . import Q_
from .config.fluids import get_name, normalize_mix
from .config.units import check_units


# ---------------------------------------------------------------------------
# Module-level REFPROP fluid cache
# ---------------------------------------------------------------------------
_current_refprop_fluid = None


def _ensure_refprop_fluid(fluid_string):
    """Call SETFLUIDSdll only when the active fluid has changed."""
    global _current_refprop_fluid
    if _current_refprop_fluid != fluid_string:
        ierr = _RP.SETFLUIDSdll(fluid_string)
        if ierr != 0:
            # Retry with .PPF extension for pseudo-pure fluids (e.g., AIR)
            ppf_string = ";".join(
                f"{c}.PPF" if "." not in c else c
                for c in fluid_string.split(";")
            )
            ierr = _RP.SETFLUIDSdll(ppf_string)
            if ierr != 0:
                raise ValueError(
                    f"SETFLUIDSdll failed for '{fluid_string}' with ierr={ierr}"
                )
            _current_refprop_fluid = fluid_string
        else:
            _current_refprop_fluid = fluid_string


# ---------------------------------------------------------------------------
# Pre-compute pint conversion factors (done once at import time)
# ---------------------------------------------------------------------------
_kPa_per_Pa = Q_(1, "Pa").to("kPa").m  # 0.001
_Pa_per_kPa = Q_(1, "kPa").to("Pa").m  # 1000.0
_uPas_to_Pas = Q_(1, "micropascal * second").to("pascal * second").m  # 1e-6
_kg_per_g = Q_(1, "g").to("kg").m  # 0.001


# ---------------------------------------------------------------------------
# _REFPROPBackend – calls ctREFPROP DLL routines directly
# ---------------------------------------------------------------------------
class _REFPROPBackend:
    """Direct REFPROP backend bypassing CoolProp entirely."""

    _phase_kph = {"gas": 2, "liquid": 1}

    def __init__(self, fluid_string, molar_fractions):
        self._fluid_string = fluid_string
        self._molar_fractions = list(molar_fractions)
        # pad to 20 elements for REFPROP
        self._z = self._molar_fractions + [0.0] * (20 - len(self._molar_fractions))

        _ensure_refprop_fluid(self._fluid_string)

        # Cache molar mass and gas constant (constant for a given composition)
        wmm_gmol = _RP.WMOLdll(self._z)  # g/mol
        self._wmm_gmol = wmm_gmol
        self._wmm_kgmol = Q_(wmm_gmol, "g/mol").to("kg/mol").m
        self._Rgas = _RP.RMIX2dll(self._z)  # J/(mol·K)

        # State variables (set by flash)
        self._T = None
        self._p = None
        self._rho = None
        self._h = None
        self._s = None
        self._cp = None
        self._cv = None
        self._w = None
        # Molar-basis values for TRNPRPdll / DERVPVTdll
        self._T_mol = None
        self._D_mol = None

        # Lazy caches (cleared on each flash)
        self._viscosity_val = None
        self._conductivity_val = None
        self._derivs = None
        self._Tc = None
        self._Pc = None

    # ---- core flash -------------------------------------------------------

    def flash(self, ab, a, b, iFlag=0):
        """Run ABFLSHdll and cache all results in mass-basis SI."""
        if np.isnan(a) or np.isnan(b):
            raise ValueError(
                f"ABFLSHdll('{ab}', {a}, {b}) failed: NaN in input"
            )
        _ensure_refprop_fluid(self._fluid_string)
        T, P, D, Dl, Dv, x, y, q, e, h, s, Cv, Cp, w, ierr, herr = (
            _RP.ABFLSHdll(ab, a, b, self._z, iFlag)
        )
        if ierr > 0:
            raise ValueError(
                f"ABFLSHdll('{ab}', {a}, {b}, iFlag={iFlag}) failed: "
                f"ierr={ierr}, herr='{herr}'"
            )

        # Store molar-basis for transport / derivative calls
        self._T_mol = T
        self._D_mol = D

        # Convert to mass-basis SI using pint-derived factors
        self._T = T  # K
        self._p = P * _Pa_per_kPa  # kPa -> Pa
        self._rho = D * self._wmm_gmol  # mol/L * g/mol = g/L = kg/m³
        self._h = h / self._wmm_kgmol  # J/mol / (kg/mol) = J/kg
        self._s = s / self._wmm_kgmol
        self._cp = Cp / self._wmm_kgmol
        self._cv = Cv / self._wmm_kgmol
        self._w = w  # m/s (mass-independent)

        # Clear lazy caches
        self._viscosity_val = None
        self._conductivity_val = None
        self._derivs = None

    def flash_1phase(self, ab, a, b, kph):
        """Single-phase flash via ABFL1dll, then full flash for all props."""
        _ensure_refprop_fluid(self._fluid_string)
        T, P, D, ierr, herr = _RP.ABFL1dll(a, b, self._z, kph, ab, 0, 0)
        if ierr > 0:
            raise ValueError(
                f"ABFL1dll('{ab}', {a}, {b}, kph={kph}) failed: "
                f"ierr={ierr}, herr='{herr}'"
            )
        # Use TD flash with the resolved T and D from ABFL1dll.
        # This avoids TP flash issues near phase boundaries and the
        # REFPROP 10.0 bug with iFlag > 0.
        self.flash("TD", T, D)

    # ---- input pair helpers ------------------------------------------------

    def _to_kPa(self, p_Pa):
        return p_Pa * _kPa_per_Pa

    def _to_mol_per_L(self, rho_kgm3):
        return rho_kgm3 / self._wmm_gmol

    def _to_Jmol(self, val_Jkg):
        return val_Jkg * self._wmm_kgmol

    # ---- transport (lazy) -------------------------------------------------

    def _compute_transport(self):
        if self._viscosity_val is None:
            _ensure_refprop_fluid(self._fluid_string)
            eta, tcx, ierr, herr = _RP.TRNPRPdll(
                self._T_mol, self._D_mol, self._z
            )
            self._viscosity_val = eta * _uPas_to_Pas  # µPa·s -> Pa·s
            self._conductivity_val = tcx  # W/(m·K)

    @property
    def viscosity(self):
        self._compute_transport()
        return self._viscosity_val

    @property
    def conductivity(self):
        self._compute_transport()
        return self._conductivity_val

    # ---- critical (lazy, cached once) -------------------------------------

    def _compute_critical(self):
        if self._Tc is None:
            _ensure_refprop_fluid(self._fluid_string)
            Tc, Pc, Dc, ierr, herr = _RP.CRITPdll(self._z)
            self._Tc = Tc  # K
            self._Pc = Pc * _Pa_per_kPa  # kPa -> Pa

    @property
    def T_critical(self):
        self._compute_critical()
        return self._Tc

    @property
    def p_critical(self):
        self._compute_critical()
        return self._Pc

    # ---- derivatives (lazy) -----------------------------------------------

    def _compute_derivs(self):
        if self._derivs is None:
            _ensure_refprop_fluid(self._fluid_string)
            r = _RP.DERVPVTdll(self._T_mol, self._D_mol, self._z)
            # r.dDdT: mol/(L·K), r.dDdP: mol/(L·kPa)
            # Convert to mass basis:
            drhodT_P = r.dDdT * self._wmm_gmol  # kg/(m³·K)
            drhodP_T = r.dDdP * self._wmm_gmol * _kPa_per_Pa  # kg/(m³·Pa)
            self._derivs = {
                "drhodT_P": drhodT_P,
                "drhodP_T": drhodP_T,
            }

    @property
    def drhodT_P(self):
        """(∂ρ/∂T)_P in kg/(m³·K)."""
        self._compute_derivs()
        return self._derivs["drhodT_P"]

    @property
    def drhodP_T(self):
        """(∂ρ/∂P)_T in kg/(m³·Pa)."""
        self._compute_derivs()
        return self._derivs["drhodP_T"]

    @property
    def dPdrho_s(self):
        """(∂P/∂ρ)_s = w² in Pa/(kg/m³)."""
        return self._w ** 2

    @property
    def dTdP_s(self):
        """(∂T/∂P)_s in K/Pa."""
        # dT/dP|s = T * v * α_P / cp
        # α_P = -(1/ρ)(∂ρ/∂T)_P
        alpha_P = -self.drhodT_P / self._rho
        v = 1.0 / self._rho
        return self._T * v * alpha_P / self._cp


# ---------------------------------------------------------------------------
# _CoolPropBackend – wraps CP.AbstractState for HEOS/PR/SRK
# ---------------------------------------------------------------------------
class _CoolPropBackend:
    """CoolProp backend preserving existing behavior for non-REFPROP EOS."""

    def __init__(self, EOS, fluid_string, molar_fractions):
        self._state = CP.AbstractState(EOS, fluid_string)
        self._state.set_mole_fractions(list(molar_fractions))

    def specify_phase(self, phase_enum):
        self._state.specify_phase(phase_enum)

    def unspecify_phase(self):
        self._state.unspecify_phase()

    def update(self, input_pair, val1, val2):
        self._state.update(input_pair, val1, val2)

    # ---- properties (delegate to CoolProp) --------------------------------

    @property
    def T(self):
        return self._state.T()

    @property
    def p(self):
        return self._state.p()

    @property
    def rho(self):
        return self._state.rhomass()

    @property
    def h(self):
        return self._state.hmass()

    @property
    def s(self):
        return self._state.smass()

    @property
    def cp(self):
        return self._state.cpmass()

    @property
    def cv(self):
        return self._state.cvmass()

    @property
    def w(self):
        return np.sqrt(self._state.first_partial_deriv(CP.iP, CP.iDmass, CP.iSmass))

    @property
    def viscosity(self):
        return self._state.viscosity()

    @property
    def conductivity(self):
        return self._state.conductivity()

    @property
    def T_critical(self):
        return self._state.T_critical()

    @property
    def p_critical(self):
        return self._state.p_critical()

    @property
    def gas_constant(self):
        return self._state.gas_constant()

    @property
    def molar_mass(self):
        return self._state.molar_mass()

    def first_partial_deriv(self, of, wrt, const):
        return self._state.first_partial_deriv(of, wrt, const)

    @property
    def drhodT_P(self):
        return self._state.first_partial_deriv(CP.iDmass, CP.iT, CP.iP)

    @property
    def drhodP_T(self):
        return self._state.first_partial_deriv(CP.iDmass, CP.iP, CP.iT)

    @property
    def dPdrho_s(self):
        return self._state.first_partial_deriv(CP.iP, CP.iDmass, CP.iSmass)

    @property
    def dTdP_s(self):
        return self._state.first_partial_deriv(CP.iT, CP.iP, CP.iSmass)

    def build_phase_envelope(self, dummy):
        self._state.build_phase_envelope(dummy)

    def get_phase_envelope_data(self):
        return self._state.get_phase_envelope_data()

    def backend_name(self):
        return self._state.backend_name()

    def fluid_names(self):
        return self._state.fluid_names()

    def get_mole_fractions(self):
        return self._state.get_mole_fractions()

    def hmass(self):
        return self._state.hmass()

    def smass(self):
        return self._state.smass()


# ---------------------------------------------------------------------------
# State – public-facing class using composition
# ---------------------------------------------------------------------------
class State:
    """A thermodynamic state.

    Creates a state from fluid composition and two properties.
    Properties can be floats (SI units are considered) or pint quantities.

    Parameters
    ----------
    p : float, pint.Quantity
        Pressure
    T : float, pint.Quantity
        Temperature
    h : float, pint.Quantity
        Enthalpy
    s : float, pint.Quantity
        Entropy
    rho : float, pint.Quantity
        Specific mass
    fluid : dict
        Dictionary with constituent and composition (mole fraction).
        (e.g.: fluid={'Oxygen': 0.2096, 'Nitrogen': 0.7812, 'Argon': 0.0092})
    EOS : str, optional
        String with REFPROP, HEOS, PR or SRK.
        Default is set in ccp.config.EOS
    phase : str, optional
        String with phase information.
        Options are:
        - "liquid"
        - "gas"
        - "two_phase"
        - "supercritical_liquid"
        - "supercritical_gas"
        - "supercritical"
        Default is None, in this case REFPROP/CoolProp will determine the phase.
        The phase calculation may require a non-trivial flash calculation which can be computationally expensive.

    Returns
    -------
    state : ccp.State

    Examples
    --------
    >>> import ccp
    >>> Q_ = ccp.Q_
    >>> fluid = {'Oxygen': 0.2096, 'Nitrogen': 0.7812, 'Argon': 0.0092}
    >>> s = ccp.State(p=101008, T=273, fluid=fluid)
    >>> s.rho()
    <Quantity(1.28939426, 'kilogram / meter ** 3')>
    >>> # Using pint quantities
    >>> s = ccp.State(fluid=fluid, p=Q_(1, 'atm'), T=Q_(0, 'degC'))
    >>> s.h()
    <Quantity(273291.7, 'joule / kilogram')>
    """

    def __new__(cls, *args, **kwargs):
        fluid = kwargs.get("fluid")
        if fluid is None:
            raise TypeError("A fluid is required. Provide as fluid=dict(...)")
        EOS = kwargs.get("EOS")
        if EOS is None:
            EOS = ccp.config.EOS

        # Validate fluid names
        try:
            _fluid = "&".join([get_name(name) for name in fluid.keys()])
        except ValueError as e:
            raise e

        # For non-REFPROP EOS, validate fluid pairs via CoolProp
        if EOS != "REFPROP":
            try:
                CP.AbstractState(EOS, _fluid)
            except ValueError:
                error_msg = ""
                constituents = list(fluid.keys())
                for fluid1, fluid2 in combinations(constituents, 2):
                    try:
                        fluid_pair = f"{fluid1}&{fluid2}"
                        CP.AbstractState(EOS, fluid_pair)
                    except ValueError:
                        error_msg += (
                            f"\nCould not create state with {fluid1} + {fluid2}"
                        )
                raise ValueError(error_msg)

        return object.__new__(cls)

    @check_units
    def __init__(
        self,
        p=None,
        T=None,
        h=None,
        s=None,
        rho=None,
        fluid=None,
        EOS=None,
        phase=None,
    ):
        if EOS is None:
            EOS = ccp.config.EOS
        self.EOS = EOS
        self.phase = phase
        self._is_refprop = EOS == "REFPROP"

        self._phase_dict = {
            "liquid": CP.iphase_liquid,
            "gas": CP.iphase_gas,
            "two_phase": CP.iphase_twophase,
            "supercritical_liquid": CP.iphase_supercritical_liquid,
            "supercritical_gas": CP.iphase_supercritical_gas,
            "supercritical": CP.iphase_supercritical,
        }

        constituents = []
        molar_fractions = []
        for k, v in fluid.items():
            try:
                k = get_name(k)
            except ValueError as e:
                raise e
            constituents.append(k)
            molar_fractions.append(v)

        _fluid = "&".join(constituents)
        self._fluid = _fluid

        normalize_mix(molar_fractions)
        self._molar_fractions = list(molar_fractions)
        self.fluid = dict(zip(constituents, molar_fractions))
        self.init_args = dict(p=p, T=T, h=h, s=s, rho=rho)
        self.setup_args = copy(self.init_args)

        if isinstance(fluid, str) and len(self.fluid) == 1:
            self.fluid[get_name(fluid)] = 1.0

        if isinstance(fluid, dict):
            if len(self.fluid) < len(fluid):
                from collections import Counter

                dupes = [
                    name
                    for name, count in Counter(constituents).items()
                    if count > 1
                ]
                raise ValueError(
                    f"Repeated components in the fluid dictionary: {dupes}. "
                    "Check that different names don't resolve to the same "
                    "component (e.g. 'butane' and 'n-butane')."
                )

        # Create the backend
        if self._is_refprop:
            refprop_fluid = ";".join(constituents)
            self._backend = _REFPROPBackend(refprop_fluid, molar_fractions)
        else:
            self._backend = _CoolPropBackend(EOS, _fluid, molar_fractions)
            if phase:
                self._backend.specify_phase(self._phase_dict[phase])

        self.update(**self.setup_args)

    # ---- repr / eq / hash -------------------------------------------------

    def __repr__(self):
        try:
            args = {k: v for k, v in self.init_args.items() if v is not None}
            args_repr = [
                f'{k}=Q_("{getattr(self, k)():.5f~P}")' for k, v in args.items()
            ]
            args_repr = ", ".join(args_repr)

            fluid_dict = self.fluid
            sorted_fluid_keys = sorted(fluid_dict, key=fluid_dict.get, reverse=True)
            fluid_repr = [f'"{k}": {fluid_dict[k]:.5f}' for k in sorted_fluid_keys]
            fluid_repr = "fluid={" + ", ".join(fluid_repr) + "}"
        except ValueError:
            return "State calculation did not converge"

        return "State(" + args_repr + ", " + fluid_repr + ")"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self_fluid_rounded = {k: round(v, 5) for k, v in self.fluid.items()}
            other_fluid_rounded = {k: round(v, 5) for k, v in other.fluid.items()}
            if (
                self_fluid_rounded == other_fluid_rounded
                and np.allclose(self.p(), other.p(), rtol=1e-4)
                and np.allclose(self.T(), other.T(), rtol=1e-4)
            ):
                return True
        return False

    def __hash__(self):
        try:
            fluid_hashable = tuple(
                sorted((k, round(v, 4)) for k, v in self.fluid.items())
            )

            def round_to_sig_figs(x, sig_figs=3):
                mag = x.to_base_units().magnitude
                if mag == 0:
                    return 0
                return round(mag, -int(np.floor(np.log10(abs(mag)))) + sig_figs - 1)

            p_val = round_to_sig_figs(self.p())
            T_val = round_to_sig_figs(self.T())

            return hash((fluid_hashable, p_val, T_val))
        except Exception:
            return hash("StateError")

    def __reduce__(self):
        kwargs = dict(p=self.p(), T=self.T(), fluid=self.fluid)
        return self._rebuild, (self.__class__, kwargs)

    @staticmethod
    def _rebuild(cls, kwargs):
        return cls(**kwargs)

    # ---- compatibility methods (CoolProp-inherited interface) ---------------

    def _fluid_dict(self):
        fluid_dict = {}
        for k, v in zip(self.fluid_names(), self.get_mole_fractions()):
            fluid_dict[k] = v
            self.fluid = fluid_dict
        return fluid_dict

    def fluid_names(self):
        return list(self.fluid.keys())

    def get_mole_fractions(self):
        return self._molar_fractions

    def set_mole_fractions(self, fracs):
        self._molar_fractions = list(fracs)

    def specify_phase(self, phase_enum):
        if not self._is_refprop:
            self._backend.specify_phase(phase_enum)

    def backend_name(self):
        if self._is_refprop:
            return "REFPROP"
        return self._backend.backend_name()

    def rhomass(self):
        return self.rho().m

    def hmass(self):
        return self.h().m

    def smass(self):
        return self.s().m

    def cpmass(self):
        return self.cp().m

    def cvmass(self):
        return self.cv().m

    def first_partial_deriv(self, of, wrt, const):
        if self._is_refprop:
            # Map the most common derivative requests
            if of == CP.iP and wrt == CP.iDmass and const == CP.iSmass:
                return self._backend.dPdrho_s
            elif of == CP.iDmass and wrt == CP.iT and const == CP.iP:
                return self._backend.drhodT_P
            elif of == CP.iDmass and wrt == CP.iP and const == CP.iT:
                return self._backend.drhodP_T
            elif of == CP.iT and wrt == CP.iP and const == CP.iSmass:
                return self._backend.dTdP_s
            else:
                raise NotImplementedError(
                    f"first_partial_deriv({of}, {wrt}, {const}) not implemented "
                    "for direct REFPROP backend"
                )
        return self._backend.first_partial_deriv(of, wrt, const)

    # ---- REFPROP direct call (for CoolProp backend fallback) ---------------

    @check_units
    def _call_REFPROP(
        self,
        p=None,
        T=None,
        h=None,
        s=None,
        rho=None,
        fluid=None,
        EOS=None,
        phase=None,
    ):
        """Function to call REFPROP directly (used as fallback for CoolProp)."""
        refprop_param_dict = {"p": "P", "T": "T", "rho": "D", "h": "H", "s": "S"}
        refprop_phase_dict = {"gas": "V", "liquid": "L"}

        input_str = ""
        args_dict = locals().copy()
        args_values = []
        for k in refprop_param_dict:
            if args_dict[k]:
                input_str += refprop_param_dict[k]
                args_values.append(args_dict[k])

        if phase:
            input_str += refprop_phase_dict[phase]

        fluids = self._fluid.replace("&", "*")
        r = _RP.REFPROPdll(
            fluids,
            input_str,
            "P,T,D,H,S",
            _RP.MASS_BASE_SI,
            0,
            0,
            args_values[0].m,
            args_values[1].m,
            self.get_mole_fractions(),
        )

        output = {
            "p": r.Output[0],
            "T": r.Output[1],
            "rho": r.Output[2],
            "h": r.Output[3],
            "s": r.Output[4],
        }
        return output

    # ---- property methods --------------------------------------------------

    def gas_constant(self, units=None):
        """Gas constant in joule / (mol kelvin)."""
        if self._is_refprop:
            gas_constant = Q_(self._backend._Rgas, "joule / (mol kelvin)")
        else:
            gas_constant = Q_(self._backend.gas_constant, "joule / (mol kelvin)")
        if units:
            gas_constant = gas_constant.to(units)
        return gas_constant

    def molar_mass(self, units=None):
        """Molar mass in kg/mol."""
        if self._is_refprop:
            molar_mass = Q_(self._backend._wmm_kgmol, "kg/mol")
        else:
            molar_mass = Q_(self._backend.molar_mass, "kg/mol")
        if units:
            molar_mass = molar_mass.to(units)
        return molar_mass

    def T(self, units=None):
        """Temperature in Kelvin."""
        T = Q_(self._backend._T if self._is_refprop else self._backend.T, "kelvin")
        if units:
            T = T.to(units)
        return T

    def p(self, units=None):
        """Pressure in Pascal."""
        p = Q_(self._backend._p if self._is_refprop else self._backend.p, "pascal")
        if units:
            p = p.to(units)
        return p

    def cp(self, units=None):
        """Specific heat at constant pressure joule/(kilogram kelvin)."""
        if self._is_refprop:
            cp_val = self._backend._cp
            if cp_val is not None and cp_val < 0:
                # Fallback: re-flash with forced vapor phase
                self._backend.flash_1phase(
                    "TP", self._backend._T_mol,
                    self._backend._p * _kPa_per_Pa,
                    kph=2,
                )
                cp_val = self._backend._cp
            cp = Q_(cp_val, "joule/(kilogram kelvin)")
        else:
            cp = Q_(self._backend.cp, "joule/(kilogram kelvin)")
            if cp < 0:
                fluids = self._fluid.replace("&", "*")
                r = _RP.REFPROPdll(
                    fluids,
                    "PTV",
                    "Cp",
                    _RP.MASS_BASE_SI,
                    0,
                    0,
                    self.p("kPa").m,
                    self.T().m,
                    self.get_mole_fractions(),
                )
                cp = Q_(r.Output[0], "joule/(kilogram kelvin)")
        if units:
            cp = cp.to(units)
        return cp

    def cv(self, units=None):
        """Specific heat at constant volume joule/(kilogram kelvin)."""
        cv = Q_(
            self._backend._cv if self._is_refprop else self._backend.cv,
            "joule/(kilogram kelvin)",
        )
        if units:
            cv = cv.to(units)
        return cv

    def h(self, units=None):
        """Specific Enthalpy (joule/kilogram)."""
        h = Q_(
            self._backend._h if self._is_refprop else self._backend.h,
            "joule/kilogram",
        )
        if units:
            h = h.to(units)
        return h

    def s(self, units=None):
        """Specific entropy (per unit of mass)."""
        s = Q_(
            self._backend._s if self._is_refprop else self._backend.s,
            "joule/(kelvin kilogram)",
        )
        if units:
            s = s.to(units)
        return s

    def p_critical(self, units=None):
        """Critical Pressure in Pa."""
        p_critical = Q_(self._backend.p_critical, "Pa")
        if units:
            p_critical = p_critical.to(units)
        return p_critical

    def T_critical(self, units=None):
        """Critical Temperature in K."""
        T_critical = Q_(self._backend.T_critical, "K")
        if units:
            T_critical = T_critical.to(units)
        return T_critical

    def rho(self, units=None):
        """Specific mass (kilogram/m**3)."""
        rho = Q_(
            self._backend._rho if self._is_refprop else self._backend.rho,
            "kilogram/m**3",
        )
        if units:
            rho = rho.to(units)
        return rho

    def v(self, units=None):
        """Specific volume (m**3/kilogram)."""
        v = 1 / self.rho()
        if units:
            v = (1 / self.rho()).to(units)
        return v

    def z(self, units=None):
        """Compressibility (dimensionless)."""
        z = (
            self.p() * self.molar_mass()
            / (self.rho() * self.gas_constant() * self.T())
        )
        return z.to("dimensionless")

    def speed_sound(self, units=None):
        """Speed of sound - Eq. 8.1 from P. Nederstigt - Real Gas Thermodynamics."""
        if self._is_refprop:
            speed_sound = Q_(self._backend._w, "m/s")
        else:
            try:
                speed_sound = Q_(
                    np.sqrt(
                        self.first_partial_deriv(CP.iP, CP.iDmass, CP.iSmass)
                    ),
                    "m/s",
                )
            except ValueError:
                dummy_state = copy(self)
                p0 = self.p()
                p1 = p0 + Q_(1e-6, "Pa")
                dummy_state.update(p=p1, s=self.s())
                rho0 = self.rho()
                rho1 = dummy_state.rho()
                delta_p = p1 - p0
                delta_rho = rho1 - rho0
                speed_sound = Q_(np.sqrt(delta_p / delta_rho), "m/s")

        if units:
            speed_sound = speed_sound.to(units)
        return speed_sound

    def viscosity(self, units=None):
        """Viscosity in pascal second."""
        if self._is_refprop:
            viscosity = Q_(self._backend.viscosity, "pascal second")
        else:
            try:
                viscosity = Q_(self._backend.viscosity, "pascal second")
            except ValueError:
                dummy_state = self.__class__(
                    p=self.p(), T=self.T(), fluid=self.fluid, EOS="REFPROP"
                )
                viscosity = dummy_state.viscosity()
        if units:
            viscosity = viscosity.to(units)
        return viscosity

    def kinematic_viscosity(self, units=None):
        """Kinematic viscosity in m²/s."""
        kinematic_viscosity = (self.viscosity() / self.rho()).to("m²/s")
        if units:
            kinematic_viscosity = kinematic_viscosity.to(units)
        return kinematic_viscosity

    def dpdv_s(self, units=None):
        """Partial derivative of pressure to spec. volume with const. entropy."""
        if self._is_refprop:
            dpdv_s = Q_(
                -(self._backend._rho ** 2) * self._backend.dPdrho_s,
                "pascal * kg / m**3",
            )
        else:
            try:
                dpdv_s = Q_(
                    -(self.rho().magnitude ** 2)
                    * self.first_partial_deriv(CP.iP, CP.iDmass, CP.iSmass),
                    "pascal * kg / m**3",
                )
            except ValueError:
                dummy_state = copy(self)
                p0 = self.p()
                p1 = p0 + Q_(1e-1, "Pa")
                dummy_state.update(p=p1, s=self.s())
                v0 = self.v()
                v1 = dummy_state.v()
                dp = p1 - p0
                dv = v1 - v0
                dpdv_s = dp / dv
        if units:
            dpdv_s = dpdv_s.to(units)
        return dpdv_s

    def _X(self):
        """Schultz compressibility coefficient X."""
        T = self.T().to("K").magnitude
        V = self.v().to("m³/kg").magnitude
        return Q_(
            -T * V * self._backend.drhodT_P - 1,
            "dimensionless",
        )

    def _Y(self):
        """Schultz compressibility coefficient Y."""
        P = self.p().to("Pa").magnitude
        V = self.v().to("m³/kg").magnitude
        return Q_(
            -(-P * V * self._backend.drhodP_T),
            "dimensionless",
        )

    def kv(self):
        """Isentropic volume exponent (dimensionless)."""
        return -(self.v() / self.p()) * self.dpdv_s()

    def dTdp_s(self, units=None):
        """(dT / dp)s - First partial derivative of temperature related to
        pressure with constant entropy."""
        if self._is_refprop:
            dTdp_s = Q_(self._backend.dTdP_s, "kelvin / pascal")
        else:
            try:
                dTdp_s = Q_(
                    self._backend.dTdP_s,
                    "kelvin / pascal",
                )
            except ValueError:
                dummy_state = copy(self)
                p0 = self.p()
                p1 = p0 + Q_(1e-1, "Pa")
                dummy_state.update(p=p1, s=self.s())
                T0 = self.T()
                T1 = dummy_state.T()
                dp = p1 - p0
                dT = T1 - T0
                dTdp_s = dT / dp
        if units:
            dTdp_s = dTdp_s.to(units)
        return dTdp_s

    def kT(self):
        """Isentropic temperature exponent (dimensionless)."""
        return 1 / (1 - (self.p() / self.T()) * self.dTdp_s())

    def conductivity(self, units=None):
        """Thermal conductivity (W/m/K)."""
        conductivity = Q_(self._backend.conductivity, "W/m/degK")
        if units:
            conductivity = conductivity.to(units)
        return conductivity

    # ---- update ------------------------------------------------------------

    @check_units
    def update(
        self,
        p=None,
        T=None,
        rho=None,
        h=None,
        s=None,
        phase=None,
        **kwargs,
    ):
        """Update the state.

        Parameters
        ----------
        p : float, pint.Quantity
            Pressure (Pa).
        T : float, pint.Quantity
            Temperature (degK).
        rho : float, pint.Quantity
            Specific mass (kg/m**3).
        h : float, pint.Quantity
            Enthalpy (J/kg).
        s : float, pint.Quantity
            Entropy (J/(kg*degK)).
        phase : str, optional
            String with phase information.
        """
        if phase:
            if not self._is_refprop:
                self._backend.specify_phase(self._phase_dict[phase])

        args = locals().copy()
        for item in ["kwargs", "self", "__class__"]:
            args.pop(item, None)
        args = [k for k, v in args.items() if v is not None]

        # Determine phase kph for REFPROP
        _phase = phase or self.phase
        _kph = _REFPROPBackend._phase_kph.get(_phase, 0) if self._is_refprop else 0

        try:
            if self._is_refprop:
                self._update_refprop(p, T, rho, h, s, _kph)
            else:
                self._update_coolprop(p, T, rho, h, s, args)
        except ValueError as e:
            args_dict = {}
            for k in args:
                args_dict[k] = locals()[k]
            args_dict["fluid"] = self.fluid
            args_repr = (
                str(args_dict)
                .replace(">", "")
                .replace("<", "")
                .replace("Quantity", "Q_")
            )
            raise ValueError(
                f"Could not define state with ccp.State(**{args_repr})"
            ) from e

        # Restore phase specification after calculation
        if self.phase and not self._is_refprop:
            self._backend.specify_phase(self._phase_dict[self.phase])

    def _update_refprop(self, p, T, rho, h, s, kph):
        """Update using direct REFPROP calls.

        If kph is set, uses single-phase flash directly.
        Otherwise tries auto-phase first, falling back to gas phase (kph=2).
        """
        b = self._backend

        # Determine ab string and inputs
        if p is not None and T is not None:
            ab = "TP"
            a, bv = T.magnitude, b._to_kPa(p.magnitude)
        elif p is not None and rho is not None:
            ab = "DP"
            a, bv = b._to_mol_per_L(rho.magnitude), b._to_kPa(p.magnitude)
        elif p is not None and h is not None:
            ab = "PH"
            a, bv = b._to_kPa(p.magnitude), b._to_Jmol(h.magnitude)
        elif p is not None and s is not None:
            ab = "PS"
            a, bv = b._to_kPa(p.magnitude), b._to_Jmol(s.magnitude)
        elif rho is not None and s is not None:
            ab = "DS"
            a, bv = b._to_mol_per_L(rho.magnitude), b._to_Jmol(s.magnitude)
        elif rho is not None and T is not None:
            ab = "TD"
            a, bv = T.magnitude, b._to_mol_per_L(rho.magnitude)
        elif h is not None and s is not None:
            ab = "HS"
            a, bv = b._to_Jmol(h.magnitude), b._to_Jmol(s.magnitude)
        elif T is not None and s is not None:
            ab = "TS"
            a, bv = T.magnitude, b._to_Jmol(s.magnitude)
        else:
            raise KeyError("Update key combination not implemented")

        if kph:
            b.flash_1phase(ab, a, bv, kph)
        else:
            try:
                b.flash(ab, a, bv)
            except ValueError:
                # Fallback: force gas phase
                b.flash_1phase(ab, a, bv, kph=2)

    def _update_coolprop(self, p, T, rho, h, s, args):
        """Update using CoolProp backend (preserves existing fallback logic)."""
        if p is not None and T is not None:
            try:
                self._backend.update(CP.PT_INPUTS, p.magnitude, T.magnitude)
            except ValueError:
                if self.backend_name() in ["REFPROP", "REFPROPMixtureBackend"]:
                    r = self._call_REFPROP(
                        p=p.magnitude, T=T.magnitude, phase="gas"
                    )
                    self._backend.update(CP.HmassP_INPUTS, r["h"], r["p"])
                else:
                    raise
        elif p is not None and rho is not None:
            try:
                self._backend.update(CP.DmassP_INPUTS, rho.magnitude, p.magnitude)
            except ValueError:
                if self.backend_name() in ["REFPROP", "REFPROPMixtureBackend"]:
                    r = self._call_REFPROP(
                        rho=rho.magnitude, p=p.magnitude, phase="gas"
                    )
                    self._backend.update(CP.PT_INPUTS, r["p"], r["T"])
                else:
                    raise
        elif p is not None and h is not None:
            try:
                self._backend.update(CP.HmassP_INPUTS, h.magnitude, p.magnitude)
            except ValueError:
                if self.backend_name() in ["REFPROP", "REFPROPMixtureBackend"]:
                    r = self._call_REFPROP(
                        p=p.magnitude, h=h.magnitude, phase="gas"
                    )
                    self._backend.update(CP.PT_INPUTS, r["p"], r["T"])
                else:
                    def objective(T_val):
                        self._backend.update(CP.PT_INPUTS, p.magnitude, T_val)
                        return self._backend.hmass() - h.magnitude

                    T0 = self._backend.T
                    if T0 == float("-inf"):
                        T0 = 300
                    newton(objective, x0=T0)
        elif p is not None and s is not None:
            if ccp.config.EOS == "REFPROP":
                try:
                    self._backend.update(
                        CP.PSmass_INPUTS, p.magnitude, s.magnitude
                    )
                except ValueError:
                    r = self._call_REFPROP(
                        p=p.magnitude, s=s.magnitude, phase="gas"
                    )
                    self._backend.update(CP.PT_INPUTS, r["p"], r["T"])
            else:
                def objective(T_val):
                    self._backend.update(CP.PT_INPUTS, p.magnitude, T_val)
                    return self._backend.smass() - s.magnitude

                T0 = self._backend.T
                if T0 == float("-inf"):
                    T0 = 300
                newton(objective, x0=T0)
        elif rho is not None and s is not None:
            try:
                self._backend.update(
                    CP.DmassSmass_INPUTS, rho.magnitude, s.magnitude
                )
            except ValueError:
                r = self._call_REFPROP(
                    rho=rho.magnitude, s=s.magnitude, phase="gas"
                )
                self._backend.update(CP.PT_INPUTS, r["p"], r["T"])
        elif rho is not None and T is not None:
            self._backend.update(CP.DmassT_INPUTS, rho.magnitude, T.magnitude)
        elif h is not None and s is not None:
            self._backend.update(CP.HmassSmass_INPUTS, h.magnitude, s.magnitude)
        elif T is not None and s is not None:
            self._backend.update(CP.SmassT_INPUTS, s.magnitude, T.magnitude)
        else:
            raise KeyError(f"Update key {args} not implemented")

    # ---- deprecated --------------------------------------------------------

    @classmethod
    @check_units
    def define(
        cls,
        p=None,
        T=None,
        h=None,
        s=None,
        rho=None,
        fluid=None,
        EOS=None,
        **kwargs,
    ):
        """Constructor for state.

        Creates a state from fluid composition and two properties.
        Properties can be floats (SI units are considered) or pint quantities.

        Parameters
        ----------
        p : float, pint.Quantity
            Pressure
        T : float, pint.Quantity
            Temperature
        h : float, pint.Quantity
            Enthalpy
        s : float, pint.Quantity
            Entropy
        rho : float, pint.Quantity
            Specific mass

        fluid : dict
            Dictionary with constituent and composition.
            (e.g.: fluid={'Oxygen': 0.2096, 'Nitrogen': 0.7812, 'Argon': 0.0092})
            String with REFPROP, HEOS, PR or SRK.
            Default is set in ccp.config.EOS

        Returns
        -------
        state : ccp.State

        Examples
        --------
        >>> import ccp
        >>> Q_ = ccp.Q_
        >>> fluid = {'Oxygen': 0.2096, 'Nitrogen': 0.7812, 'Argon': 0.0092}
        >>> s = ccp.State.define(p=101008, T=273, fluid=fluid)
        >>> s.rho()
        <Quantity(1.28939426, 'kilogram / meter ** 3')>
        >>> # Using pint quantities
        >>> s = ccp.State.define(fluid=fluid, p=Q_(1, 'atm'), T=Q_(0, 'degC'))
        >>> s.h()
        <Quantity(273291.7, 'joule / kilogram')>
        """
        warn(
            "Method ccp.State.define is deprecated. Use ccp.State() instead.",
            DeprecationWarning,
        )
        return cls(p=p, T=T, h=h, s=s, rho=rho, fluid=fluid, EOS=EOS, **kwargs)

    # ---- CoolProp utilities ------------------------------------------------

    def get_coolprop_state(self):
        """Return a CoolProp state object."""
        EOS = self.EOS
        if EOS is None:
            EOS = ccp.config.EOS
        return CP.AbstractState(EOS, self._fluid)

    # ---- plotting ----------------------------------------------------------

    def plot_envelope(
        self, T_units="degK", p_units="Pa", dew_point_margin=20, fig=None, **kwargs
    ):
        """Plot phase envelope.

        Plots the phase envelope and dew point limit.

        Parameters
        ----------
        T_units : str
            Temperature units. Default is 'degK'.
        p_units : str
            Pressure units. Default is 'Pa'.
        dew_point_margin : float
            Dew point margin. Default is 20 degK (from API).
        fig : plotly.graph_objects.Figure, optional
            The figure object with the rotor representation.

        Returns
        -------
        fig : plotly.graph_objects.Figure
            The figure object with the rotor representation.
        """
        if fig is None:
            fig = go.Figure()

        if len(self.fluid) < 2:
            warn(
                "Pure fluids are not fully supported and might break things "
                "(e.g. plot_phase_envelope"
                "See https://github.com/CoolProp/CoolProp/issues/1544"
            )

        # Use CoolProp for phase envelope (even for REFPROP backend)
        if self._is_refprop:
            cp_state = CP.AbstractState("REFPROP", self._fluid)
            cp_state.set_mole_fractions(self._molar_fractions)
            cp_state.specify_phase(CP.iphase_gas)
            cp_state.update(CP.PT_INPUTS, self.p().m, self.T().m)
            cp_state.build_phase_envelope("dummy")
            phase_envelope = cp_state.get_phase_envelope_data()
        else:
            self._backend.build_phase_envelope("dummy")
            phase_envelope = self._backend.get_phase_envelope_data()

        T = Q_(np.array(phase_envelope.T), "degK").to(T_units).m
        p = Q_(np.array(phase_envelope.p), "Pa").to(p_units).m

        p_lower_bound = Q_(0.1, "atm").to(p_units).m
        T = T[p > p_lower_bound]
        p = p[p > p_lower_bound]

        T_dew = (
            np.add(
                T[: np.argmax(T)],
                np.multiply(dew_point_margin, np.ones(np.argmax(T))),
            ),
        )
        p_dew = (p[: np.argmax(T)],)

        hovertemplate = (
            f"Temperature ({T_units}): %{{x}}<br>Pressure ({p_units}): %{{y}}"
        )

        fig.add_trace(
            go.Scatter(
                x=T,
                y=p,
                mode="lines",
                hovertemplate=hovertemplate,
                name="Phase Envelope",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=T_dew[0],
                y=p_dew[0],
                mode="lines",
                line=dict(dash="dash"),
                hovertemplate=hovertemplate,
                name=f"Dew Point Margin ({dew_point_margin} {T_units})",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[self.T().to(T_units).m],
                y=[self.p().to(p_units).m],
                hovertemplate=hovertemplate,
                name="State",
            )
        )

        fig.update_layout(
            xaxis=dict(title_text=f"Temperature ({T_units})"),
            yaxis=dict(
                type="log",
                exponentformat="e",
                title_text=f"Pressure ({p_units})",
            ),
        )

        return fig

    def plot_point(self, T_units="degK", p_units="Pa", fig=None, **kwargs):
        """Plot point.

        Plot point in the given figure. Function will check for axis units and
        plot the point accordingly.

        Parameters
        ----------
        T_units : str
            Temperature units. Default is 'degK'.
        p_units : str
            Pressure units. Default is 'Pa'.
        fig : plotly.graph_objects.Figure, optional
            The figure object with the rotor representation.
        kwargs : dict
            Dictionary that will be passed to go.Scatter method.

        Returns
        -------
        fig : plotly.graph_objects.Figure
            The figure object with the rotor representation.
        """
        if fig is None:
            fig = go.Figure()

        p = self.p().to(p_units)
        T = self.T().to(T_units)

        default_values = dict(name="State")

        for k, v in default_values.items():
            kwargs.setdefault(k, v)

        fig.add_trace(
            go.Scatter(
                x=[T.m],
                y=[p.m],
                hovertemplate=f"Temperature ({T_units}): %{{x}}<br>"
                f"Pressure ({p_units}): %{{y}}",
                **kwargs,
            )
        )

        return fig
