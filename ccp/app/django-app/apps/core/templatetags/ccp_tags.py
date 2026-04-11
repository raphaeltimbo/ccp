"""Template tags and filters for the ccp Django app.

Exposes helpers for rendering shared UI partials (parameter row,
expander) and embedding Plotly figures produced by the ``ccp`` library.
"""

from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def plotly_figure(fig, div_id: str | None = None) -> str:
    """Render a plotly figure as an inline HTML fragment.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        Figure to serialise. ``base.html`` is expected to load
        ``plotly.min.js`` exactly once, so this tag never inlines
        the library.
    div_id : str, optional
        Explicit ``id`` for the generated ``<div>``.

    Returns
    -------
    str
        Safe HTML ready to be injected into a Django template.
    """
    import plotly.io as pio

    html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
    )
    return mark_safe(html)


@register.inclusion_tag("core/partials/parameter_row.html")
def parameter_row(
    key: str,
    value=None,
    units=None,
    selected_unit: str | None = None,
    label: str | None = None,
    help: str = "",
):
    """Render a labeled parameter input row."""
    return {
        "key": key,
        "label": label or key,
        "value": value,
        "units": units or [],
        "selected_unit": selected_unit,
        "help": help,
    }


@register.inclusion_tag("core/partials/expander.html")
def expander(title: str, body_id: str, expanded: bool = False):
    """Render an expander header. Body is injected via a ``body`` context variable."""
    return {
        "title": title,
        "body_id": body_id,
        "expanded": expanded,
        "body": "",
    }


_UNIT_SUFFIXES = ("_units", "_unit")
_VALUE_SUFFIX = "_value"


def _pair_field(name: str, fields: dict) -> tuple[str, str] | None:
    """Return ``(base, units_name)`` if *name* is a value field with a
    matching units field, else ``None``.

    Supports both conventions in use by the ported forms:
    * ``<base>_value`` + ``<base>_units`` (back_to_back, parameter_map)
    * ``<base>`` + ``<base>_unit`` / ``<base>_units`` (straight_through)
    """
    if name.endswith(_VALUE_SUFFIX):
        base = name[: -len(_VALUE_SUFFIX)]
        for suffix in _UNIT_SUFFIXES:
            candidate = f"{base}{suffix}"
            if candidate in fields:
                return base, candidate
        return None
    if any(name.endswith(s) for s in _UNIT_SUFFIXES):
        return None
    for suffix in _UNIT_SUFFIXES:
        candidate = f"{name}{suffix}"
        if candidate in fields:
            return name, candidate
    return None


@register.simple_tag
def form_param_rows(form) -> str:
    """Render a form as Streamlit-style ``label | units | value`` rows.

    Fields whose names follow ``<base>_value``/``<base>_units`` or
    ``<base>``/``<base>_unit`` conventions are collapsed into a 3-column
    grid row (label | units dropdown | value input). Any field that
    cannot be paired becomes a full-width row so no form data is lost.
    """
    from django.utils.html import conditional_escape as esc

    fields = {f.name: f for f in form}
    seen: set[str] = set()
    rows: list[str] = []
    for name, field in fields.items():
        if name in seen:
            continue
        pairing = _pair_field(name, fields)
        if pairing is not None:
            base, units_name = pairing
            units_field = fields[units_name]
            label = field.label or base.replace("_", " ").title()
            help_text = field.field.help_text or ""
            help_html = (
                f'<span class="ccp-param-row__help" title="{esc(help_text)}">?</span>'
                if help_text
                else ""
            )
            err_html = ""
            if field.errors:
                err_html = (
                    '<div class="ccp-param-row__error">'
                    f"{esc(', '.join(field.errors))}</div>"
                )
            rows.append(
                '<div class="ccp-param-row">'
                f'<label for="{field.id_for_label}" class="ccp-param-row__label">'
                f"{esc(label)}{help_html}</label>"
                f'<div class="ccp-param-row__units">{units_field}</div>'
                f'<div class="ccp-param-row__value">{field}</div>'
                "</div>"
                f"{err_html}"
            )
            seen.add(name)
            seen.add(units_name)
            continue
        if any(name.endswith(s) for s in _UNIT_SUFFIXES):
            base = name.rsplit("_", 1)[0]
            if base in fields or f"{base}_value" in fields:
                continue
        label = field.label or name
        rows.append(
            '<div class="ccp-param-row ccp-param-row--single">'
            f'<label for="{field.id_for_label}" class="ccp-param-row__label">{esc(label)}</label>'
            f'<div class="ccp-param-row__wide">{field}</div>'
            "</div>"
        )
        seen.add(name)
    return mark_safe('<div class="ccp-param-table">' + "".join(rows) + "</div>")


@register.filter
def format_quantity(q) -> str:
    """Render a :class:`pint.Quantity` as ``"<magnitude> <units>"``.

    Falls back to ``str(q)`` when the input is not a pint quantity.
    """
    magnitude = getattr(q, "magnitude", None)
    units = getattr(q, "units", None)
    if magnitude is None or units is None:
        return str(q)
    return f"{magnitude} {units}"
