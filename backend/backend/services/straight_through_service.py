import numpy as np

import ccp
from ccp import Q_
from ccp.compressor import Point1Sec, StraightThrough
from ccp.config.utilities import r_getattr

from ..schemas.straight_through import (
    CellHighlight,
    StraightThroughRequest,
    StraightThroughResponse,
)
from .quantity_utils import to_q


def _find_gas_components(request: StraightThroughRequest, gas_name: str) -> dict:
    """Look up a gas composition by name from the request's gas_compositions list."""
    for gas in request.gas_compositions:
        if gas.name == gas_name:
            return {k: v for k, v in gas.components.items() if v != 0}
    raise ValueError(f"Gas composition '{gas_name}' not found")


def _specific_heat_calculate(T_in, T_out, oil_iso_classification: str):
    """Calculate oil specific heat using ISO classification polynomials."""
    T_in_c = T_in.to("degC").m
    T_out_c = T_out.to("degC").m

    if oil_iso_classification[3:] == "32":
        a, b, c = -0.0000019, 0.0042, 1.80
    else:
        a, b, c = -0.0000018, 0.0040, 1.83

    cp = (
        a * (T_out_c**3 - T_in_c**3) / 3
        + b * (T_out_c**2 - T_in_c**2) / 2
        + c * (T_out_c - T_in_c)
    ) / (T_out_c - T_in_c)
    return Q_(cp, "kJ/kg/degK")


def _density_calculate(T_in, T_out, oil_iso_classification: str):
    """Calculate oil density using ISO classification."""
    T_in_c = T_in.to("degC").m
    T_out_c = T_out.to("degC").m
    beta = Q_(0.00075, "1/degC").m

    if oil_iso_classification[3:] == "32":
        rho_15 = Q_(870, "kg/m³").m
    else:
        rho_15 = Q_(876, "kg/m³").m

    density = (
        rho_15
        / (beta * (T_out_c - T_in_c))
        * (
            np.log(1 + beta * T_out_c - 15 * beta)
            - np.log(1 + beta * T_in_c - 15 * beta)
        )
    )
    return Q_(density, "kg/m³")


def _is_mass_flow(qi) -> bool:
    """Check if a QuantityInput represents mass flow (vs volumetric)."""
    return Q_(0, qi.unit).dimensionality == Q_(0, "kg/s").dimensionality


def calculate_straight_through(
    request: StraightThroughRequest,
) -> StraightThroughResponse:
    """Execute the straight-through compressor calculation.

    Replicates the logic from ccp/app/pages/1_straight_through.py.
    """
    options = request.options
    ds = request.data_sheet

    # --- Build guarantee point ---
    guarantee_fluid = _find_gas_components(request, request.guarantee_gas)

    kwargs_guarantee = {}
    if _is_mass_flow(ds.flow):
        kwargs_guarantee["flow_m"] = to_q(ds.flow)
    else:
        kwargs_guarantee["flow_v"] = to_q(ds.flow)

    kwargs_guarantee["suc"] = ccp.State(
        p=to_q(ds.suction_pressure),
        T=to_q(ds.suction_temperature),
        fluid=guarantee_fluid,
    )
    kwargs_guarantee["disch"] = ccp.State(
        p=to_q(ds.discharge_pressure),
        T=to_q(ds.discharge_temperature),
        fluid=guarantee_fluid,
    )
    kwargs_guarantee["speed"] = to_q(ds.speed)
    kwargs_guarantee["b"] = to_q(ds.b)
    kwargs_guarantee["D"] = to_q(ds.D)

    # Power losses for guarantee point
    if options.bearing_mechanical_losses and ds.power is not None:
        power_guarantee = to_q(ds.power).to("kW")
        if ds.power_shaft is not None:
            power_shaft_guarantee = to_q(ds.power_shaft).to("kW")
        else:
            power_shaft_guarantee = power_guarantee
        kwargs_guarantee["power_losses"] = power_shaft_guarantee - power_guarantee
    else:
        kwargs_guarantee["power_losses"] = Q_(0, "W")

    guarantee_point = ccp.Point(**kwargs_guarantee)

    # --- Build test points ---
    test_points = []
    for tp in request.test_points:
        kwargs = {}
        test_fluid = _find_gas_components(request, tp.gas_name)

        if _is_mass_flow(tp.flow):
            kwargs["flow_m"] = to_q(tp.flow)
        else:
            kwargs["flow_v"] = to_q(tp.flow)

        kwargs["suc"] = ccp.State(
            p=to_q(tp.suction_pressure),
            T=to_q(tp.suction_temperature),
            fluid=test_fluid,
        )
        kwargs["disch"] = ccp.State(
            p=to_q(tp.discharge_pressure),
            T=to_q(tp.discharge_temperature),
            fluid=test_fluid,
        )

        # Casing heat loss
        if tp.casing_delta_T is not None and options.casing_heat_loss:
            kwargs["casing_temperature"] = to_q(tp.casing_delta_T)
            kwargs["ambient_temperature"] = 0
        else:
            kwargs["casing_temperature"] = 0
            kwargs["ambient_temperature"] = 0

        # Leakages
        if options.calculate_leakages:
            if tp.balance_line_flow_m is not None:
                kwargs["balance_line_flow_m"] = to_q(tp.balance_line_flow_m)
            else:
                kwargs["balance_line_flow_m"] = None

            if options.seal_gas_flow and tp.seal_gas_flow_m is not None:
                kwargs["seal_gas_flow_m"] = to_q(tp.seal_gas_flow_m)
            else:
                kwargs["seal_gas_flow_m"] = Q_(0, "kg/s")

            if options.seal_gas_flow and tp.seal_gas_temperature is not None:
                kwargs["seal_gas_temperature"] = to_q(tp.seal_gas_temperature)
            else:
                kwargs["seal_gas_temperature"] = Q_(0, "degK")

        # Bearing mechanical losses
        kwargs["bearing_mechanical_losses"] = options.bearing_mechanical_losses
        if options.bearing_mechanical_losses:
            # Oil flows
            if tp.oil_flow_journal_bearing_de is not None:
                kwargs["oil_flow_journal_bearing_de"] = to_q(
                    tp.oil_flow_journal_bearing_de
                )
            else:
                kwargs["oil_flow_journal_bearing_de"] = None

            if tp.oil_flow_journal_bearing_nde is not None:
                kwargs["oil_flow_journal_bearing_nde"] = to_q(
                    tp.oil_flow_journal_bearing_nde
                )
            else:
                kwargs["oil_flow_journal_bearing_nde"] = None

            if tp.oil_flow_thrust_bearing_nde is not None:
                kwargs["oil_flow_thrust_bearing_nde"] = to_q(
                    tp.oil_flow_thrust_bearing_nde
                )
            else:
                kwargs["oil_flow_thrust_bearing_nde"] = None

            if tp.oil_inlet_temperature is not None:
                kwargs["oil_inlet_temperature"] = to_q(tp.oil_inlet_temperature)
            else:
                kwargs["oil_inlet_temperature"] = None

            if tp.oil_outlet_temperature_de is not None:
                kwargs["oil_outlet_temperature_de"] = to_q(tp.oil_outlet_temperature_de)
            else:
                kwargs["oil_outlet_temperature_de"] = None

            if tp.oil_outlet_temperature_nde is not None:
                kwargs["oil_outlet_temperature_nde"] = to_q(
                    tp.oil_outlet_temperature_nde
                )
            else:
                kwargs["oil_outlet_temperature_nde"] = None

            # Oil specific heat / density from ISO or direct input
            oil = request.oil_inputs
            if oil is not None and oil.use_iso_oil and oil.oil_iso_classification:
                iso = oil.oil_iso_classification
                kwargs["oil_specific_heat_de"] = _specific_heat_calculate(
                    kwargs["oil_inlet_temperature"],
                    kwargs["oil_outlet_temperature_de"],
                    iso,
                )
                kwargs["oil_specific_heat_nde"] = _specific_heat_calculate(
                    kwargs["oil_inlet_temperature"],
                    kwargs["oil_outlet_temperature_nde"],
                    iso,
                )
                kwargs["oil_density_de"] = _density_calculate(
                    kwargs["oil_inlet_temperature"],
                    kwargs["oil_outlet_temperature_de"],
                    iso,
                )
                kwargs["oil_density_nde"] = _density_calculate(
                    kwargs["oil_inlet_temperature"],
                    kwargs["oil_outlet_temperature_nde"],
                    iso,
                )
            elif oil is not None and oil.oil_specific_heat is not None:
                kwargs["oil_specific_heat_de"] = to_q(oil.oil_specific_heat)
                kwargs["oil_specific_heat_nde"] = to_q(oil.oil_specific_heat)
                kwargs["oil_density_de"] = to_q(oil.oil_density)
                kwargs["oil_density_nde"] = to_q(oil.oil_density)

            # Geometry from data sheet for test points
            kwargs["b"] = to_q(ds.b)
            kwargs["D"] = to_q(ds.D)
            if ds.casing_area is not None:
                kwargs["casing_area"] = to_q(ds.casing_area)
            if ds.surface_roughness is not None:
                kwargs["surface_roughness"] = to_q(ds.surface_roughness)

        test_points.append(
            Point1Sec(
                speed=to_q(tp.speed),
                **kwargs,
            )
        )

    # --- Create StraightThrough ---
    straight_through = StraightThrough(
        guarantee_point=guarantee_point,
        test_points=test_points,
        reynolds_correction=options.reynolds_correction,
        bearing_mechanical_losses=options.bearing_mechanical_losses,
    )

    if options.calculate_speed_to_match:
        straight_through = (
            straight_through.calculate_speed_to_match_discharge_pressure()
        )

    # --- Build results table ---
    _t = "\u209c"
    _sp = "\u209b\u209a"
    conv = "\u1d9c\u1d52\u207f\u1d5b"

    # Create interpolated point at guarantee flow
    point_interpolated = straight_through.point(
        flow_v=straight_through.guarantee_point.flow_v,
        speed=straight_through.speed_operational,
    )

    results = {}
    gp = straight_through.guarantee_point

    # Test points columns
    results[f"\u03c6{_t}"] = [
        round(p.phi.m, 5) for p in straight_through.test_points
    ]
    results[f"\u03c6{_t} / \u03c6{_sp}"] = [
        round(p.phi.m / gp.phi.m, 5) for p in straight_through.test_points
    ]
    results["vi / vd"] = [
        round(p.volume_ratio.m, 5) for p in straight_through.test_points
    ]
    results[f"(vi/vd){_t}/(vi/vd){_sp}"] = [
        round(p.volume_ratio.m / gp.volume_ratio.m, 5)
        for p in straight_through.test_points
    ]
    results[f"Mach{_t}"] = [
        round(p.mach.m, 5) for p in straight_through.test_points
    ]
    results[f"Mach{_t} - Mach{_sp}"] = [
        round(p.mach.m - gp.mach.m, 5) for p in straight_through.test_points
    ]
    results[f"Re{_t}"] = [
        round(p.reynolds.m, 5) for p in straight_through.test_points
    ]
    results[f"Re{_t} / Re{_sp}"] = [
        round(p.reynolds.m / gp.reynolds.m, 5) for p in straight_through.test_points
    ]
    results[f"pd{conv} (bar)"] = [
        round(p.disch.p("bar").m, 5) for p in straight_through.points_flange_sp
    ]
    results[f"pd{conv}/pd{_sp}"] = [
        round(p.disch.p("bar").m / gp.disch.p("bar").m, 5)
        for p in straight_through.points_flange_sp
    ]
    results[f"Head{_t} (kJ/kg)"] = [
        round(p.head.to("kJ/kg").m, 5) for p in straight_through.points_flange_sp
    ]
    results[f"Head{_t}/Head{_sp}"] = [
        round(p.head.to("kJ/kg").m / gp.head.to("kJ/kg").m, 5)
        for p in straight_through.test_points
    ]
    results[f"Head{conv} (kJ/kg)"] = [
        round(p.head.to("kJ/kg").m, 5) for p in straight_through.points_flange_sp
    ]
    results[f"Head{conv}/Head{_sp}"] = [
        round(p.head.to("kJ/kg").m / gp.head.to("kJ/kg").m, 5)
        for p in straight_through.points_flange_sp
    ]
    results[f"Q{conv} (m3/h)"] = [
        round(p.flow_v.to("m\u00b3/h").m, 5)
        for p in straight_through.points_flange_sp
    ]
    results[f"Q{conv}/Q{_sp}"] = [
        round(p.flow_v.to("m\u00b3/h").m / gp.flow_v.to("m\u00b3/h").m, 5)
        for p in straight_through.points_flange_sp
    ]
    results[f"W{_t} (kW)"] = [
        round(p.power_shaft.to("kW").m, 5) for p in straight_through.points_rotor_t
    ]

    # Power ratios depend on bearing_mechanical_losses
    if options.bearing_mechanical_losses and ds.power_shaft is not None:
        power_ref = to_q(ds.power_shaft).to("kW").m
    elif ds.power is not None:
        power_ref = to_q(ds.power).to("kW").m
    else:
        power_ref = 1.0  # fallback

    results[f"W{_t}/W{_sp}"] = [
        round(p.power_shaft.to("kW").m / power_ref, 5)
        for p in straight_through.points_rotor_t
    ]
    results[f"W{conv} (kW)"] = [
        round(p.power_shaft.to("kW").m, 5) for p in straight_through.points_rotor_sp
    ]
    results[f"W{conv}/W{_sp}"] = [
        round(p.power_shaft.to("kW").m / power_ref, 5)
        for p in straight_through.points_rotor_sp
    ]
    results[f"Eff{_t}"] = [
        round(p.eff.m, 5) for p in straight_through.points_flange_t
    ]
    results[f"Eff{conv}"] = [
        round(p.eff.m, 5) for p in straight_through.points_flange_sp
    ]

    # Append interpolated (guarantee) row
    results[f"\u03c6{_t}"].append(round(point_interpolated.phi.m, 5))
    results[f"\u03c6{_t} / \u03c6{_sp}"].append(
        round(point_interpolated.phi.m / gp.phi.m, 5)
    )
    results["vi / vd"].append(round(point_interpolated.volume_ratio.m, 5))
    results[f"(vi/vd){_t}/(vi/vd){_sp}"].append(
        round(point_interpolated.volume_ratio.m / gp.volume_ratio.m, 5)
    )
    results[f"Mach{_t}"].append(round(point_interpolated.mach.m, 5))
    results[f"Mach{_t} - Mach{_sp}"].append(
        round(point_interpolated.mach.m - gp.mach.m, 5)
    )
    results[f"Re{_t}"].append(round(point_interpolated.reynolds.m, 5))
    results[f"Re{_t} / Re{_sp}"].append(
        round(point_interpolated.reynolds.m / gp.reynolds.m, 5)
    )
    results[f"pd{conv} (bar)"].append(
        round(point_interpolated.disch.p("bar").m, 5)
    )
    results[f"pd{conv}/pd{_sp}"].append(
        round(point_interpolated.disch.p("bar").m / gp.disch.p("bar").m, 5)
    )
    results[f"Head{_t} (kJ/kg)"].append(
        round(point_interpolated.head.to("kJ/kg").m, 5)
    )
    results[f"Head{_t}/Head{_sp}"].append(
        round(point_interpolated.head.to("kJ/kg").m / gp.head.to("kJ/kg").m, 5)
    )
    results[f"Head{conv} (kJ/kg)"].append(
        round(point_interpolated.head.to("kJ/kg").m, 5)
    )
    results[f"Head{conv}/Head{_sp}"].append(
        round(point_interpolated.head.to("kJ/kg").m / gp.head.to("kJ/kg").m, 5)
    )
    results[f"Q{conv} (m3/h)"].append(
        round(point_interpolated.flow_v.to("m\u00b3/h").m, 5)
    )
    results[f"Q{conv}/Q{_sp}"].append(
        round(
            point_interpolated.flow_v.to("m\u00b3/h").m
            / gp.flow_v.to("m\u00b3/h").m,
            5,
        )
    )
    results[f"W{_t} (kW)"].append(None)
    results[f"W{_t}/W{_sp}"].append(None)
    results[f"W{conv} (kW)"].append(
        round(point_interpolated.power_shaft.to("kW").m, 5)
    )
    results[f"W{conv}/W{_sp}"].append(
        round(point_interpolated.power_shaft.to("kW").m / power_ref, 5)
    )
    results[f"Eff{_t}"].append(round(point_interpolated.eff.m, 5))
    results[f"Eff{conv}"].append(round(point_interpolated.eff.m, 5))

    # Build row-indexed results dict: {row_label: {col_label: value}}
    num_test = len(straight_through.points_flange_t)
    row_labels = [f"Point {i + 1}" for i in range(num_test)] + ["Guarantee Point"]
    results_by_row = {}
    for row_idx, label in enumerate(row_labels):
        results_by_row[label] = {
            col: vals[row_idx] for col, vals in results.items()
        }

    # --- Cell highlights ---
    highlights = []
    gp_label = "Guarantee Point"
    gp_idx = num_test  # last row

    def _add_highlight(col: str, value, lower: float, upper: float):
        if value is None:
            return
        if lower <= value <= upper:
            color = "green"
        else:
            color = "red"
        highlights.append(CellHighlight(row=gp_label, col=col, color=color))

    # Mach limits
    mach_limits = point_interpolated.mach_limits()
    _add_highlight(
        f"Mach{_t}",
        results_by_row[gp_label].get(f"Mach{_t}"),
        mach_limits["lower"],
        mach_limits["upper"],
    )

    # Reynolds limits
    reynolds_limits = point_interpolated.reynolds_limits()
    _add_highlight(
        f"Re{_t}",
        results_by_row[gp_label].get(f"Re{_t}"),
        reynolds_limits["lower"],
        reynolds_limits["upper"],
    )

    # Volume ratio
    _add_highlight(
        f"(vi/vd){_t}/(vi/vd){_sp}",
        results_by_row[gp_label].get(f"(vi/vd){_t}/(vi/vd){_sp}"),
        0.95,
        1.05,
    )

    # Phi ratio
    _add_highlight(
        f"\u03c6{_t} / \u03c6{_sp}",
        results_by_row[gp_label].get(f"\u03c6{_t} / \u03c6{_sp}"),
        0.96,
        1.04,
    )

    # Pressure and power limits depend on variable speed
    if options.variable_speed:
        power_limit = 1.04
        pressure_limit = 1e15
    else:
        power_limit = 1.07
        pressure_limit = 1.05

    _add_highlight(
        f"pd{conv}/pd{_sp}",
        results_by_row[gp_label].get(f"pd{conv}/pd{_sp}"),
        1.0,
        pressure_limit,
    )
    _add_highlight(
        f"W{conv}/W{_sp}",
        results_by_row[gp_label].get(f"W{conv}/W{_sp}"),
        0.0,
        power_limit,
    )

    # --- Plots ---
    plots = {}
    for curve in ["head", "eff", "discharge_pressure", "power"]:
        if curve == "discharge_pressure":
            curve_plot_method = "disch.p"
        else:
            curve_plot_method = curve

        try:
            fig = r_getattr(straight_through, f"{curve_plot_method}_plot")()
            fig = r_getattr(point_interpolated, f"{curve_plot_method}_plot")(fig=fig)
            fig.update_layout(
                showlegend=True,
                legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01),
            )
            plots[curve] = fig.to_dict()
        except Exception:
            plots[curve] = {}

    return StraightThroughResponse(
        results=results_by_row,
        highlights=highlights,
        plots=plots,
        speed_operational_rpm=round(
            straight_through.speed_operational.to("rpm").m, 2
        ),
    )
