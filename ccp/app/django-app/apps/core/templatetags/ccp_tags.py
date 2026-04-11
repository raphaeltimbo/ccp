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


@register.simple_tag
def formset_param_grid(formset, scope: str = "") -> str:
    """Render a formset as a parameters × points grid.

    Each form in *formset* becomes a column (``Point 1``..``Point N``) and
    every ``<base>_value`` field in form 0 whose paired ``<base>_units``
    also exists becomes a row with a shared units dropdown. Changing the
    visible select cascades the value into hidden ``_units`` inputs for
    the remaining forms so formset validation still sees per-form units.

    Parameters
    ----------
    formset : django.forms.formsets.BaseFormSet
        Bound or unbound formset to pivot.
    scope : str, optional
        Prefix used by the sync-unit ``data-sync-unit`` attribute so that
        multiple grids on the same page don't clobber each other's state.
        Defaults to ``formset.prefix`` when omitted.
    """
    from django.utils.html import conditional_escape as esc

    if not formset.forms:
        return ""

    scope = scope or formset.prefix or ""
    first = formset.forms[0]
    fields = {f.name: f for f in first}

    params: list[tuple[str, str, str, object]] = []
    for name, bound in fields.items():
        if not name.endswith(_VALUE_SUFFIX):
            continue
        base = name[: -len(_VALUE_SUFFIX)]
        units_name = f"{base}_units"
        if units_name not in fields:
            continue
        label = bound.field.label or base.replace("_", " ").title()
        help_text = bound.field.help_text or ""
        params.append((base, label, help_text, fields[units_name]))

    if not params:
        return ""

    n = len(formset.forms)
    parts: list[str] = ['<div class="ccp-grid-wrap"><table class="ccp-grid-table"><thead><tr>']
    parts.append('<th scope="col" class="ccp-grid-corner"></th>')
    parts.append('<th scope="col" class="ccp-grid-units-col">Units</th>')
    for i in range(n):
        parts.append(f'<th scope="col">Point {i + 1}</th>')
    parts.append("</tr></thead><tbody>")

    for base, label, help_text, units_bf in params:
        sync_key = f"{scope}-{base}" if scope else base
        initial_unit = units_bf.value() or ""
        help_html = (
            f'<span class="ccp-param-row__help" title="{esc(help_text)}">?</span>'
            if help_text
            else ""
        )

        # Render the visible units select for form 0 with sync hooks.
        visible_options = []
        for value, display in units_bf.field.choices:
            selected = " selected" if value == initial_unit else ""
            visible_options.append(
                f'<option value="{esc(value)}"{selected}>{esc(display)}</option>'
            )
        visible_select = (
            f'<select name="{units_bf.html_name}" id="{units_bf.auto_id}" '
            f'class="form-select form-select-sm ccp-grid-units" '
            f'data-sync-unit="{sync_key}" '
            f'onchange="ccpSyncUnit(this)">'
            f'{"".join(visible_options)}'
            "</select>"
        )

        parts.append("<tr>")
        parts.append(
            f'<th scope="row" class="ccp-grid-label">{esc(label)}{help_html}</th>'
        )
        parts.append(f'<td class="ccp-grid-units-cell">{visible_select}</td>')

        for i, form in enumerate(formset.forms):
            form_fields = {bf.name: bf for bf in form}
            value_bf = form_fields[f"{base}_value"]
            parts.append(f'<td class="ccp-grid-value-cell">{value_bf}</td>')

        parts.append("</tr>")

    parts.append("</tbody></table>")

    # Hidden mirrors for forms 1..n-1 so the formset sees per-form units.
    for i, form in enumerate(formset.forms):
        if i == 0:
            continue
        form_fields = {bf.name: bf for bf in form}
        for base, _label, _help, _units_bf in params:
            units_bf_i = form_fields[f"{base}_units"]
            initial_unit = units_bf_i.value() or ""
            sync_key = f"{scope}-{base}" if scope else base
            parts.append(
                f'<input type="hidden" name="{units_bf_i.html_name}" '
                f'value="{esc(initial_unit)}" '
                f'data-sync-unit="{sync_key}">'
            )
    parts.append("</div>")
    return mark_safe("".join(parts))


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
