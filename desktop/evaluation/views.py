import base64
import io
import json
import logging
import re
import traceback
import zipfile
from datetime import datetime, timezone

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

CCP_DESKTOP_FORMAT_VERSION = "0.1"


def _strip_data_url(s):
    """Drop a leading data-URL prefix like 'data:image/png;base64,' if present."""
    if s.startswith("data:"):
        comma = s.find(",")
        if comma != -1:
            return s[comma + 1 :]
    return s

COMPONENTS = [
    {"key": "methane", "formula": "CH\u2084"},
    {"key": "ethane", "formula": "C\u2082H\u2086"},
    {"key": "propane", "formula": "C\u2083H\u2088"},
    {"key": "n-butane", "formula": "nC\u2084H\u2081\u2080"},
    {"key": "i-butane", "formula": "iC\u2084H\u2081\u2080"},
    {"key": "n-pentane", "formula": "nC\u2085H\u2081\u2082"},
    {"key": "i-pentane", "formula": "iC\u2085H\u2081\u2082"},
    {"key": "n-hexane", "formula": "C\u2086H\u2081\u2084"},
    {"key": "n-heptane", "formula": "C\u2087H\u2081\u2086"},
    {"key": "n-octane", "formula": "C\u2088H\u2081\u2088"},
    {"key": "n-nonane", "formula": "C\u2089H\u2082\u2080"},
    {"key": "nitrogen", "formula": "N\u2082"},
    {"key": "h2s", "formula": "H\u2082S"},
    {"key": "co2", "formula": "CO\u2082"},
    {"key": "h2o", "formula": "H\u2082O"},
]

FLUID_LIST = sorted([
    "methane", "ethane", "propane", "n-butane", "i-butane", "isobutane",
    "n-pentane", "i-pentane", "isopentane", "neopentane",
    "n-hexane", "n-heptane", "n-octane", "n-nonane", "n-decane",
    "n-undecane", "n-dodecane", "cyclohexane", "cyclopentane", "cyclopropane",
    "ethylene", "propylene", "1-butene", "i-butene", "cis-2-butene", "trans-2-butene",
    "1-pentene", "acetylene",
    "benzene", "toluene", "ethylbenzene", "m-xylene", "o-xylene", "p-xylene",
    "methanol", "ethanol",
    "nitrogen", "oxygen", "hydrogen", "helium", "argon", "krypton", "neon", "xenon",
    "co2", "carbon monoxide", "carbonyl sulfide", "sulfur dioxide",
    "h2s", "h2o", "water", "steam", "air", "ammonia",
    "r11", "r12", "r13", "r14", "r22", "r23", "r32", "r41",
    "r123", "r124", "r125", "r134a", "r143a", "r152a", "r161",
    "r218", "r227ea", "r236ea", "r236fa", "r245ca", "r245fa",
    "r1234yf", "r1234ze(e)", "r1234ze(z)",
    "ethylene oxide", "diethyl ether", "dimethyl ether",
])

DEFAULT_CASES = [
    {
        "name": "case_a",
        "hue": 255,
        "data": [83.94, 3.73, 1.58, 1.75, 1.82, 0.39, 0.30, 0.10, 0.00, 0.00, 0.00, 1.49, 0.017, 5.25, 0.00],
    },
    {
        "name": "case_b",
        "hue": 186,
        "data": [47.21, 3.45, 3.22, 1.19, 0.59, 0.78, 0.29, 0.24, 0.00, 0.00, 0.00, 0.39, 4.03, 40.31, 0.00],
    },
    {
        "name": "case_c",
        "hue": 65,
        "data": [29.55, 3.04, 2.23, 0.62, 0.36, 0.36, 0.20, 0.38, 0.00, 0.00, 0.00, 0.25, 0.02, 61.98, 0.00],
    },
    {
        "name": "case_d",
        "hue": 15,
        "data": [57.21, 6.39, 0.92, 2.57, 1.37, 0.07, 0.11, 0.46, 0.00, 0.00, 0.00, 6.24, 0.01, 20.49, 0.00],
    },
    {
        "name": "gas_4",
        "hue": 145,
        "data": [0.0] * 15,
    },
    {
        "name": "gas_5",
        "hue": 300,
        "data": [0.0] * 15,
    },
]

FLOW_M_UNITS = ["kg/h", "kg/min", "kg/s", "lbm/h", "lbm/min", "lbm/s"]
FLOW_V_UNITS = ["m\u00b3/h", "m\u00b3/min", "m\u00b3/s"]
FLOW_UNITS = FLOW_M_UNITS + FLOW_V_UNITS
PRESSURE_UNITS = ["bar", "kgf/cm\u00b2", "barg", "Pa", "kPa", "MPa", "psi", "mmH2O"]
TEMPERATURE_UNITS = ["degK", "degC", "degF", "degR"]
HEAD_UNITS = ["kJ/kg", "J/kg", "m*g0", "ft"]
POWER_UNITS = ["kW", "hp", "W", "Btu/h", "MW"]
SPEED_UNITS = ["rpm", "Hz"]
LENGTH_UNITS = ["m", "mm", "ft", "in"]
OIL_FLOW_UNITS = ["l/min", "l/h", "gal/min", "m\u00b3/h", "m\u00b3/min", "m\u00b3/s"]
SPECIFIC_HEAT_UNITS = ["kJ/kg/degK", "J/kg/degK", "cal/g/degC", "Btu/lb/degF"]
DENSITY_UNITS = ["kg/m\u00b3", "g/cm\u00b3", "g/ml", "g/l"]

POLYTROPIC_METHODS = [
    {"value": "sandberg_colby", "label": "Sandberg-Colby"},
    {"value": "sandberg_colby_multistep", "label": "Sandberg-Colby Multistep"},
    {"value": "huntington", "label": "Huntington"},
    {"value": "mallen_saville", "label": "Mallen-Saville"},
    {"value": "schultz", "label": "Schultz"},
]

DATA_SHEET_PARAMETERS = [
    {"key": "flow", "label": "Flow", "units": FLOW_UNITS, "help": "Mass or volumetric flow depending on selected unit."},
    {"key": "suction_pressure", "label": "Suction Pressure", "units": PRESSURE_UNITS},
    {"key": "suction_temperature", "label": "Suction Temperature", "units": TEMPERATURE_UNITS},
    {"key": "discharge_pressure", "label": "Discharge Pressure", "units": PRESSURE_UNITS},
    {"key": "discharge_temperature", "label": "Discharge Temperature", "units": TEMPERATURE_UNITS},
    {"key": "power", "label": "Gas Power", "units": POWER_UNITS},
    {"key": "power_shaft", "label": "Shaft Power", "units": POWER_UNITS},
    {"key": "speed", "label": "Speed", "units": SPEED_UNITS},
    {"key": "head", "label": "Head", "units": HEAD_UNITS},
    {"key": "eff", "label": "Efficiency", "units": [""]},
    {"key": "b", "label": "First Impeller Width", "units": LENGTH_UNITS},
    {"key": "D", "label": "First Impeller Diameter", "units": LENGTH_UNITS},
    {"key": "surface_roughness", "label": "Surface Roughness", "units": LENGTH_UNITS + ["microm"]},
    {"key": "casing_area", "label": "Casing Area", "units": ["m\u00b2", "mm\u00b2", "ft\u00b2", "in\u00b2"]},
]

TEST_PARAMETERS = [
    {"key": "flow", "label": "Flow", "units": FLOW_UNITS, "help": "Mass or volumetric flow depending on selected unit."},
    {"key": "suction_pressure", "label": "Suction Pressure", "units": PRESSURE_UNITS},
    {"key": "suction_temperature", "label": "Suction Temperature", "units": TEMPERATURE_UNITS},
    {"key": "discharge_pressure", "label": "Discharge Pressure", "units": PRESSURE_UNITS},
    {"key": "discharge_temperature", "label": "Discharge Temperature", "units": TEMPERATURE_UNITS},
    {"key": "casing_delta_T", "label": "Casing \u0394T", "units": TEMPERATURE_UNITS, "help": "Temperature difference between casing and ambient."},
    {"key": "speed", "label": "Speed", "units": SPEED_UNITS},
    {"key": "balance_line_flow_m", "label": "Balance Line Flow", "units": FLOW_M_UNITS},
    {"key": "seal_gas_flow_m", "label": "Seal Gas Flow", "units": FLOW_M_UNITS, "group": "seal_gas"},
    {"key": "seal_gas_temperature", "label": "Seal Gas Temperature", "units": TEMPERATURE_UNITS, "group": "seal_gas"},
    {"key": "oil_flow_journal_bearing_de", "label": "Oil Flow Journal Bearing DE", "units": OIL_FLOW_UNITS, "group": "oil"},
    {"key": "oil_flow_journal_bearing_nde", "label": "Oil Flow Journal Bearing NDE", "units": OIL_FLOW_UNITS, "group": "oil"},
    {"key": "oil_flow_thrust_bearing_nde", "label": "Oil Flow Thrust Bearing NDE", "units": OIL_FLOW_UNITS, "group": "oil"},
    {"key": "oil_inlet_temperature", "label": "Oil Inlet Temperature", "units": TEMPERATURE_UNITS, "group": "oil"},
    {"key": "oil_outlet_temperature_de", "label": "Oil Outlet Temperature DE", "units": TEMPERATURE_UNITS, "group": "oil"},
    {"key": "oil_outlet_temperature_nde", "label": "Oil Outlet Temperature NDE", "units": TEMPERATURE_UNITS, "group": "oil"},
]

FLOWRATE_PARAMETERS = [
    {"key": "outer_diameter_fo", "label": "Outer Diameter", "units": ["mm", "m", "ft", "in"], "help": "Outer diameter of orifice plate."},
    {"key": "inner_diameter_fo", "label": "Inner Diameter", "units": ["mm", "m", "ft", "in"], "help": "Inner diameter of orifice plate."},
    {"key": "upstream_pressure_fo", "label": "Upstream Pressure", "units": PRESSURE_UNITS},
    {"key": "upstream_temperature_fo", "label": "Upstream Temperature", "units": TEMPERATURE_UNITS},
    {"key": "pressure_drop_fo", "label": "Pressure Drop", "units": PRESSURE_UNITS},
    {"key": "tappings_fo", "label": "Tappings", "units": ["flange", "corner", "D D/2"], "is_select": True},
    {"key": "mass_flow_fo", "label": "Mass Flow (Result)", "units": ["kg/h", "lbm/h", "kg/s", "lbm/s"], "readonly": True},
]

CURVE_TYPES = [
    {"key": "head", "label": "Head"},
    {"key": "eff", "label": "Efficiency"},
    {"key": "discharge_pressure", "label": "Discharge Pressure"},
    {"key": "power", "label": "Power"},
]

NUM_TEST_POINTS = 6


def _build_gas_table_data(cases=None):
    if cases is None:
        cases = DEFAULT_CASES
    rows = []
    for i, comp in enumerate(COMPONENTS):
        row_values = [case["data"][i] for case in cases]
        row_max = max(row_values)
        cells = []
        for v in row_values:
            bar = (v / row_max * 0.65) if row_max > 0 else 0
            cells.append({
                "value": f"{v:.3f}",
                "bar": f"{bar:.2f}",
                "is_zero": v == 0,
                "is_dominant": v > 40,
            })
        rows.append({"component": comp, "cells": cells})

    totals = []
    for case in cases:
        s = sum(case["data"])
        totals.append({
            "value": f"{s:.3f}",
            "ok": abs(s - 100) < 0.5 or s == 0,
        })
    return rows, totals


_POLYTROPIC_LABEL_TO_VALUE = {m["label"]: m["value"] for m in POLYTROPIC_METHODS}


def _looks_like_streamlit(state):
    return (
        isinstance(state, dict)
        and "gas_compositions_table" in state
        and "form" not in state
        and "gas_composition" not in state
    )


def _adapt_streamlit_state(state):
    """Translate a Streamlit st.session_state dump into the desktop schema."""
    form = {}

    # Data-sheet (guarantee point) — Streamlit uses `<param>_point_guarantee`
    # and `<param>_units_point_guarantee`, desktop drops the `_point_`.
    for param in (p["key"] for p in DATA_SHEET_PARAMETERS):
        src = state.get(f"{param}_point_guarantee")
        if src is not None:
            form[f"{param}_guarantee"] = src
        src_units = state.get(f"{param}_units_point_guarantee")
        if src_units is not None:
            form[f"{param}_units_guarantee"] = src_units
    if "gas_point_guarantee" in state:
        form["gas_point_guarantee"] = state["gas_point_guarantee"]

    # Test points — key shape already matches (`<param>_point_<i>` + shared `<param>_units`).
    for param in (p["key"] for p in TEST_PARAMETERS):
        for i in range(1, NUM_TEST_POINTS + 1):
            k = f"{param}_point_{i}"
            if k in state:
                form[k] = state[k]
        units_key = f"{param}_units"
        if units_key in state:
            form[units_key] = state[units_key]
    for i in range(1, NUM_TEST_POINTS + 1):
        if f"gas_point_{i}" in state:
            form[f"gas_point_{i}"] = state[f"gas_point_{i}"]

    # Flowrate / orifice — key shape already matches.
    for param in (p["key"] for p in FLOWRATE_PARAMETERS):
        for i in range(1, NUM_TEST_POINTS + 1):
            k = f"{param}_{i}"
            if k in state:
                form[k] = state[k]
        units_key = f"{param}_units"
        if units_key in state:
            form[units_key] = state[units_key]
    for i in range(1, NUM_TEST_POINTS + 1):
        if f"gas_fo_{i}" in state:
            form[f"gas_fo_{i}"] = state[f"gas_fo_{i}"]

    # Curve ranges — key shape already matches.
    for curve in (c["key"] for c in CURVE_TYPES):
        for suffix in ("lower", "upper", "units"):
            for axis in ("x", "y"):
                k = f"{axis}_{curve}_{suffix}"
                if k in state:
                    form[k] = state[k]
        flow_key = f"x_{curve}_flow_units"
        if flow_key in state:
            form[flow_key] = state[flow_key]

    # Options (partial mismatch).
    if "ambient_pressure_magnitude" in state:
        form["ambient_pressure"] = state["ambient_pressure_magnitude"]
    for key in (
        "ambient_pressure_unit",
        "bearing_mechanical_losses",
        "oil_specific_heat",
        "oil_iso",
        "oil_iso_classification",
    ):
        if key in state:
            form[key] = state[key]
    if "polytropic_method" in state:
        label_or_value = state["polytropic_method"]
        form["polytropic_method"] = _POLYTROPIC_LABEL_TO_VALUE.get(
            label_or_value, label_or_value
        )

    # Gas composition — rebuild nested schema, matching by component name
    # (Streamlit file has 14 components; desktop has 15, n-nonane stays zero).
    gct = state.get("gas_compositions_table") or {}
    desktop_components = [c["key"] for c in COMPONENTS]
    cases = []
    for i, default in enumerate(DEFAULT_CASES):
        entry_key = f"gas_{i}"
        gas_dict = gct.get(entry_key) or {}
        name = state.get(entry_key) or default["name"]
        comp_to_value = {}
        for j in range(len(COMPONENTS) + 1):  # iterate generously
            comp_name = gas_dict.get(f"component_{j}")
            if comp_name is None:
                continue
            raw = gas_dict.get(f"molar_fraction_{j}", "")
            try:
                comp_to_value[str(comp_name)] = float(str(raw).replace(",", ".") or 0)
            except (TypeError, ValueError):
                comp_to_value[str(comp_name)] = 0.0
        values = [comp_to_value.get(c, 0.0) for c in desktop_components]
        cases.append({"name": str(name), "hue": default["hue"], "values": values})

    return {
        "app_type": state.get("app_type", "straight_through"),
        "saved_at": state.get("saved_at"),
        "source": "streamlit",
        "ccp_version": state.get("ccp_version"),
        "form": form,
        "gas_composition": {"components": desktop_components, "cases": cases},
    }


def performance(request):
    rows, totals = _build_gas_table_data()
    conditions = [
        {"group": "Suction", "label": "Pressure", "value": "42.80", "unit": "bar a"},
        {"group": "Suction", "label": "Temperature", "value": "38.20", "unit": "\u00b0C"},
        {"group": "Suction", "label": "Flow (mass)", "value": "186.40", "unit": "t/h"},
        {"group": "Suction", "label": "Z-factor", "value": "0.842", "unit": "\u2014"},
        {"group": "Discharge", "label": "Pressure", "value": "128.40", "unit": "bar a"},
        {"group": "Discharge", "label": "Temperature", "value": "132.10", "unit": "\u00b0C"},
        {"group": "Shaft", "label": "Speed", "value": "9 420", "unit": "rpm"},
        {"group": "Shaft", "label": "Power (meas.)", "value": "7.28", "unit": "MW"},
    ]
    return render(request, "evaluation/performance.html", {
        "cases": DEFAULT_CASES,
        "rows": rows,
        "totals": totals,
        "conditions": conditions,
    })


@require_POST
def save_state(request, app_type):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON body"}, status=400)

    state = payload.get("state") or {}
    # Separate PNG images out of the JSON state — they go in as top-level zip
    # entries (matching Streamlit's on-disk format) rather than being bloated
    # into session_state.json as base64.
    curve_images = state.pop("curveImages", None) if isinstance(state, dict) else None

    requested_name = (payload.get("filename") or "").strip()
    safe_stem = re.sub(r"[^\w.-]+", "_", requested_name).strip("._") or app_type
    if safe_stem.lower().endswith(".ccp"):
        safe_stem = safe_stem[:-4]
    download_name = f"{safe_stem}.ccp"

    session_state = {
        "app_type": app_type,
        "schema_version": 1,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **state,
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ccp.version", f"desktop-{CCP_DESKTOP_FORMAT_VERSION}\n")
        zf.writestr(
            "session_state.json",
            json.dumps(session_state, indent=2, ensure_ascii=False),
        )
        if isinstance(curve_images, dict):
            for key, b64 in curve_images.items():
                if not b64:
                    continue
                safe_key = re.sub(r"[^\w.-]+", "_", str(key))
                try:
                    png_bytes = base64.b64decode(_strip_data_url(str(b64)))
                except Exception as e:  # noqa: BLE001 — tolerate bad uploads
                    logger.warning("Skipping fig_%s.png: %s", safe_key, e)
                    continue
                zf.writestr(f"fig_{safe_key}.png", png_bytes)
    body = buf.getvalue()

    response = HttpResponse(body, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{download_name}"'
    response["Content-Length"] = str(len(body))
    response["X-CCP-App-Type"] = app_type
    return response


@require_POST
def load_state(request):
    upload = request.FILES.get("file")
    if upload is None:
        return JsonResponse({"error": "no file uploaded"}, status=400)

    try:
        with zipfile.ZipFile(upload) as zf:
            names = zf.namelist()
            version = (
                zf.read("ccp.version").decode("utf-8").strip()
                if "ccp.version" in names
                else ""
            )
            if "session_state.json" not in names:
                return JsonResponse(
                    {"error": "session_state.json missing from archive"},
                    status=400,
                )
            state = json.loads(zf.read("session_state.json").decode("utf-8"))

            curve_images = {}
            for name in names:
                m = re.fullmatch(r"fig_([a-zA-Z0-9_-]+)\.png", name)
                if not m:
                    continue
                data = zf.read(name)
                if not data:
                    continue
                curve_images[m.group(1)] = base64.b64encode(data).decode("ascii")
    except zipfile.BadZipFile:
        return JsonResponse({"error": "not a valid .ccp archive"}, status=400)
    except json.JSONDecodeError as e:
        return JsonResponse(
            {"error": f"session_state.json is not valid JSON: {e}"}, status=400
        )

    if _looks_like_streamlit(state):
        state = _adapt_streamlit_state(state)

    if curve_images:
        if not isinstance(state, dict):
            state = {"form": {}, "gas_composition": None}
        state["curveImages"] = curve_images

    return JsonResponse({"version": version, "state": state})


def straight_through(request):
    rows, totals = _build_gas_table_data()
    gas_names = [c["name"] for c in DEFAULT_CASES]
    point_range = range(1, NUM_TEST_POINTS + 1)
    return render(request, "evaluation/straight_through.html", {
        "components": COMPONENTS,
        "fluid_list": FLUID_LIST,
        "cases": DEFAULT_CASES,
        "gas_names": gas_names,
        "rows": rows,
        "totals": totals,
        "data_sheet_parameters": DATA_SHEET_PARAMETERS,
        "test_parameters": TEST_PARAMETERS,
        "flowrate_parameters": FLOWRATE_PARAMETERS,
        "curve_types": CURVE_TYPES,
        "point_range": point_range,
        "num_test_points": NUM_TEST_POINTS,
        "pressure_units": PRESSURE_UNITS,
        "polytropic_methods": POLYTROPIC_METHODS,
        "flow_v_units": FLOW_V_UNITS,
    })


def _q(value, unit):
    """Build a pint Quantity from a possibly-blank string; return None if blank."""
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _gas_composition_from_case(case, components):
    values = case.get("values") or []
    return {
        comp: float(v)
        for comp, v in zip(components, values)
        if isinstance(v, (int, float)) and v > 0
    }


def _flow_kwarg(unit_str):
    """Return 'flow_m' or 'flow_v' based on whether the unit is mass or volume flow."""
    from ccp import Q_

    dim = Q_(1, unit_str).dimensionality
    mass_dim = Q_(1, "kg/s").dimensionality
    return "flow_m" if dim == mass_dim else "flow_v"


@require_POST
def calculate_straight_through(request):
    try:
        from ccp import Q_, State, ureg
        from ccp.compressor import Point1Sec, StraightThrough
        from ccp.point import Point
    except ImportError as e:
        return JsonResponse(
            {"error": f"ccp library is not available in this environment: {e}"},
            status=500,
        )

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid JSON body"}, status=400)

    form = payload.get("form") or {}

    # Register `barg` against the user-selected ambient pressure, mirroring the
    # Streamlit page (ccp/app/pages/1_straight_through.py:161). Safe to re-run:
    # if the definition changes we update it in-place.
    try:
        amb_mag = float(str(form.get("ambient_pressure") or 1.01325).replace(",", "."))
    except ValueError:
        amb_mag = 1.01325
    amb_unit = form.get("ambient_pressure_unit") or "bar"
    try:
        ambient_bar = Q_(amb_mag, amb_unit).to("bar").magnitude
    except Exception:
        ambient_bar = 1.01325
    try:
        ureg.define(f"barg = 1 * bar; offset: {ambient_bar}")
    except Exception:
        # pint raises if already defined with a different offset; redefine via remove.
        try:
            del ureg._units["barg"]
        except Exception:
            pass
        ureg.define(f"barg = 1 * bar; offset: {ambient_bar}")
    gas_composition = payload.get("gas_composition") or {}
    cases = gas_composition.get("cases") or []
    components = (
        gas_composition.get("components")
        or [c["key"] for c in COMPONENTS]
    )
    cases_by_name = {
        c.get("name"): _gas_composition_from_case(c, components) for c in cases
    }

    def fluid_for(gas_name, context):
        comp = cases_by_name.get(gas_name)
        if not comp:
            raise ValueError(
                f"{context}: gas '{gas_name}' is empty or not defined"
            )
        return comp

    def q(value_key, unit_key, default_unit=None, required=False, context=""):
        raw = form.get(value_key)
        unit = form.get(unit_key) or default_unit
        parsed = _q(raw, unit)
        if parsed is None:
            if required:
                raise ValueError(f"{context}: missing value for {value_key}")
            return None
        if unit is None:
            raise ValueError(f"{context}: missing unit for {unit_key}")
        return Q_(parsed, unit)

    try:
        # --- Guarantee point ---
        g_fluid = fluid_for(form.get("gas_point_guarantee"), "guarantee point")
        flow_unit_g = form.get("flow_units_guarantee") or "kg/h"
        flow_kw_g = _flow_kwarg(flow_unit_g)
        flow_g = q("flow_guarantee", "flow_units_guarantee",
                   default_unit="kg/h", required=True, context="guarantee point")

        suc_g = State(
            p=q("suction_pressure_guarantee", "suction_pressure_units_guarantee",
                default_unit="bar", required=True, context="guarantee point"),
            T=q("suction_temperature_guarantee",
                "suction_temperature_units_guarantee",
                default_unit="degK", required=True, context="guarantee point"),
            fluid=g_fluid,
        )
        disch_g = State(
            p=q("discharge_pressure_guarantee",
                "discharge_pressure_units_guarantee",
                default_unit="bar", required=True, context="guarantee point"),
            T=q("discharge_temperature_guarantee",
                "discharge_temperature_units_guarantee",
                default_unit="degK", required=True, context="guarantee point"),
            fluid=g_fluid,
        )
        speed_g = q("speed_guarantee", "speed_units_guarantee",
                    default_unit="rpm", required=True, context="guarantee point")
        b_g = q("b_guarantee", "b_units_guarantee",
                default_unit="m", required=True, context="guarantee point")
        D_g = q("D_guarantee", "D_units_guarantee",
                default_unit="m", required=True, context="guarantee point")

        guarantee_point = Point(
            suc=suc_g,
            disch=disch_g,
            speed=speed_g,
            b=b_g,
            D=D_g,
            power_losses=Q_(0, "W"),
            **{flow_kw_g: flow_g},
        )
    except Exception as e:
        logger.exception("Guarantee-point build failed")
        return JsonResponse(
            {"error": f"Failed to build guarantee point: {e}"}, status=400
        )

    # --- Test points ---
    test_points = []
    skipped = []
    try:
        flow_unit_t = form.get("flow_units") or "kg/s"
        flow_kw_t = _flow_kwarg(flow_unit_t)

        for i in range(1, NUM_TEST_POINTS + 1):
            fp = form.get(f"flow_point_{i}")
            sp = form.get(f"suction_pressure_point_{i}")
            stp = form.get(f"suction_temperature_point_{i}")
            if not fp or not sp or not stp:
                skipped.append(i)
                continue

            p_fluid = fluid_for(form.get(f"gas_point_{i}"), f"test point {i}")
            point_suc = State(
                p=q(f"suction_pressure_point_{i}", "suction_pressure_units",
                    default_unit="bar", required=True,
                    context=f"test point {i}"),
                T=q(f"suction_temperature_point_{i}", "suction_temperature_units",
                    default_unit="degK", required=True,
                    context=f"test point {i}"),
                fluid=p_fluid,
            )
            point_disch = State(
                p=q(f"discharge_pressure_point_{i}", "discharge_pressure_units",
                    default_unit="bar", required=True,
                    context=f"test point {i}"),
                T=q(f"discharge_temperature_point_{i}",
                    "discharge_temperature_units",
                    default_unit="degK", required=True,
                    context=f"test point {i}"),
                fluid=p_fluid,
            )
            flow_val = q(f"flow_point_{i}", "flow_units",
                         default_unit="kg/s", required=True,
                         context=f"test point {i}")
            speed_val = q(f"speed_point_{i}", "speed_units",
                          default_unit="rpm", required=True,
                          context=f"test point {i}")

            test_points.append(
                Point1Sec(
                    suc=point_suc,
                    disch=point_disch,
                    speed=speed_val,
                    b=b_g,
                    D=D_g,
                    casing_area=0,
                    casing_temperature=0,
                    ambient_temperature=0,
                    **{flow_kw_t: flow_val},
                )
            )
    except Exception as e:
        logger.exception("Test-point build failed")
        return JsonResponse(
            {"error": f"Failed to build test points: {e}", "skipped": skipped},
            status=400,
        )

    if not test_points:
        return JsonResponse(
            {
                "error": (
                    "No complete test points — each point needs flow, suction "
                    "pressure, and suction temperature filled."
                ),
                "skipped": skipped,
            },
            status=400,
        )

    reynolds_correction = bool(form.get("reynolds_correction", False))
    try:
        st_obj = StraightThrough(
            guarantee_point=guarantee_point,
            test_points=test_points,
            reynolds_correction=reynolds_correction,
            bearing_mechanical_losses=False,
        )
    except Exception as e:
        logger.exception("StraightThrough construction failed")
        return JsonResponse(
            {
                "error": f"StraightThrough construction failed: {e}",
                "trace": traceback.format_exc() if request.GET.get("debug") else None,
            },
            status=400,
        )

    def extract(point, idx):
        def _f(attr, to_unit=None):
            val = getattr(point, attr, None)
            if val is None:
                return None
            try:
                return float(val.to(to_unit).m if to_unit else val.m)
            except Exception:
                return None

        try:
            suc_p = point.suc.p().to("bar").m
            disch_p = point.disch.p().to("bar").m
            return {
                "point": idx,
                "flow_m_kgs": _f("flow_m", "kg/s"),
                "phi": _f("phi"),
                "pressure_ratio": disch_p / suc_p if suc_p else None,
                "head_kJkg": _f("head", "kJ/kg"),
                "eff": _f("eff"),
                "power_kW": _f("power", "kW"),
                "speed_rpm": _f("speed", "rpm"),
                "suc_p_bar": suc_p,
                "suc_T_degC": point.suc.T().to("degC").m,
                "disch_p_bar": disch_p,
                "disch_T_degC": point.disch.T().to("degC").m,
            }
        except Exception as e:
            return {"point": idx, "error": str(e)}

    # --- Plotly charts ---
    charts = _build_st_charts(st_obj, form, payload.get("curveImages") or {})

    return JsonResponse(
        {
            "speed_operational_rpm": float(st_obj.speed_operational.to("rpm").m),
            "test_point_count": len(test_points),
            "skipped_points": skipped,
            "reynolds_correction": reynolds_correction,
            "test_flange_points": [extract(p, i + 1) for i, p in enumerate(st_obj.points_flange_t)],
            "converted_points": [extract(p, i + 1) for i, p in enumerate(st_obj.points_flange_sp)],
            "charts": charts,
        }
    )


_CURVE_CONFIG = [
    ("head", "head_plot", "head_units", "kJ/kg"),
    ("eff", "eff_plot", None, None),
    ("discharge_pressure", "disch.p_plot", "p_units", "bar"),
    ("power", "power_plot", "power_units", "kW"),
]


def _apply_background_image(fig, form, curve_key, png_b64):
    """Overlay a base64-encoded PNG as a background image on a figure.

    Requires all four axis bounds (x/y lower/upper) to be present and numeric;
    otherwise silently skips, since placement is ambiguous without them.
    """
    try:
        x_lo = float(form.get(f"x_{curve_key}_lower"))
        x_hi = float(form.get(f"x_{curve_key}_upper"))
        y_lo = float(form.get(f"y_{curve_key}_lower"))
        y_hi = float(form.get(f"y_{curve_key}_upper"))
    except (TypeError, ValueError):
        return
    try:
        png_bytes = base64.b64decode(_strip_data_url(str(png_b64)))
    except Exception:  # noqa: BLE001
        return
    if not png_bytes:
        return
    encoded = base64.b64encode(png_bytes).decode("ascii")
    fig.add_layout_image(
        dict(
            source=f"data:image/png;base64,{encoded}",
            xref="x",
            yref="y",
            x=x_lo,
            y=y_hi,
            sizex=x_hi - x_lo,
            sizey=y_hi - y_lo,
            sizing="stretch",
            opacity=0.5,
            layer="below",
        )
    )


def _build_st_charts(st_obj, form, curve_images):
    """Build JSON Plotly figures for head / eff / disch.p / power / mach / reynolds.

    Returns a dict {curve_key: figure_dict}. If plotting fails for a curve,
    that key is missing and 'chart_errors' on the enclosing response holds
    the exception — we keep best-effort so partial failures don't break
    the result table.
    """
    from ccp.impeller import r_getattr
    import plotly.io as pio

    # Interpolated guarantee point overlay (same pattern as Streamlit page).
    try:
        point_interp = st_obj.point(
            flow_v=st_obj.guarantee_point.flow_v,
            speed=st_obj.speed_operational,
        )
    except Exception:
        logger.exception("Interpolated guarantee point failed")
        point_interp = None

    charts = {}

    # Mach and Reynolds come from the interpolated point only (match Streamlit).
    if point_interp is not None:
        for key, method in (("mach", "plot_mach"), ("reynolds", "plot_reynolds")):
            try:
                fig = getattr(point_interp, method)()
                fig.update_layout(
                    showlegend=True,
                    legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01),
                    margin=dict(l=48, r=16, t=24, b=40),
                )
                charts[key] = json.loads(pio.to_json(fig))
            except Exception as e:
                logger.exception("Plot %s failed", key)
                charts[key] = {"error": str(e)}

    for curve_key, plot_attr, y_unit_kw, default_y_unit in _CURVE_CONFIG:
        try:
            x_flow_units = form.get(f"x_{curve_key}_flow_units") or "m³/h"
            y_units = form.get(f"y_{curve_key}_units") or default_y_unit
            kwargs = {"flow_v_units": x_flow_units}
            if y_unit_kw and y_units:
                kwargs[y_unit_kw] = y_units

            fig = r_getattr(st_obj, plot_attr)(show_points=True, **kwargs)
            if point_interp is not None:
                try:
                    fig = r_getattr(point_interp, plot_attr)(
                        fig=fig, show_points=True, **kwargs
                    )
                except Exception:
                    logger.exception("Overlay for %s failed", curve_key)

            # Apply user-supplied axis ranges if all four bounds are present.
            x_lo = form.get(f"x_{curve_key}_lower")
            x_hi = form.get(f"x_{curve_key}_upper")
            y_lo = form.get(f"y_{curve_key}_lower")
            y_hi = form.get(f"y_{curve_key}_upper")
            if all(v not in (None, "") for v in (x_lo, x_hi, y_lo, y_hi)):
                try:
                    fig.update_layout(
                        xaxis_range=(float(x_lo), float(x_hi)),
                        yaxis_range=(float(y_lo), float(y_hi)),
                    )
                except (TypeError, ValueError):
                    pass

            fig.update_layout(
                showlegend=True,
                legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01),
                margin=dict(l=48, r=16, t=24, b=40),
            )

            png_b64 = curve_images.get(curve_key) if curve_images else None
            if png_b64:
                _apply_background_image(fig, form, curve_key, png_b64)

            charts[curve_key] = json.loads(pio.to_json(fig))
        except Exception as e:
            logger.exception("Plot %s failed", curve_key)
            charts[curve_key] = {"error": str(e)}

    return charts
