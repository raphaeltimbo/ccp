# desktop/ — CLAUDE.md

Context for the **Electron + Django desktop app**. Inherits everything from the root `CLAUDE.md`; the notes here apply only when working inside `desktop/`.

## What this is

A distributable desktop app alternative to the Streamlit UI in `ccp/app/`. Electron spawns a local Django server as a sidecar and loads it in a Chromium window — no REST API for external consumers, no SPA.

Status: **straight-through page is functional end-to-end**. Gas composition → data sheet → test points → Calculate runs the real `ccp.StraightThrough` and returns tables + six Plotly charts (Mach, Reynolds, Head, Efficiency, Discharge Pressure, Power). `.ccp` files round-trip with the Streamlit app, including uploaded curve PNGs.

Performance-evaluation page still mostly mocks. `Calculate Speed` / `Calculate Flowrate` buttons are inert. Oil / seal-gas / casing heat-loss branches are not wired (`bearing_mechanical_losses` is forced off in the calc).

## Stack

- **Electron** (main.js) — spawns Django, loads `http://127.0.0.1:<port>`. `preload.js` exposes native file dialogs to the renderer via `contextBridge`.
- **Django 5** — templates + views. No ORM/admin/auth/sessions/CSRF middleware. Endpoints accept plain JSON or multipart, return JSON or binary.
- **HTMX + Alpine.js + Plotly.js** — vendored locally under `static/vendor/` and loaded via `{% static %}` in `base.html`. HTMX for server interactions, Alpine for small client state (collapsibles, tweaks panel), Plotly for result charts.
- **Plain CSS** with oklch design tokens — no Tailwind build step.
- **Fonts vendored locally** — Geist + Geist Mono + IBM Plex + Fraunces + JetBrains Mono are downloaded as woff2 under `static/vendor/fonts/`, served via `static/vendor/fonts.css`. The full app boots offline; no Google Fonts / unpkg / cdn.plot.ly traffic at runtime.
- **`ccp` library** — installed as an editable path dep (`ccp-performance = { path = "..", editable = true }`). Brings CoolProp, pint, plotly, numpy/scipy/pandas.

## Layout

```
desktop/
├── main.js                  # Electron entry — spawns Django, IPC handlers for native Save/Open dialogs
├── preload.js               # contextBridge — exposes window.ccpElectron to the renderer
├── manage.py                # Django entry
├── core/                    # Django project (settings, urls, wsgi)
├── evaluation/              # Django app — views.py holds the view-model AND the calc/save/load/adapter logic
├── templates/
│   ├── base.html            # app shell + top-bar Save/Open buttons + CCP state JS module
│   └── evaluation/          # per-page templates
├── static/
│   ├── css/app.css          # full design system + .chart-grid layout
│   ├── js/                  # (reserved; most page JS is still inline in templates)
│   └── vendor/              # local copies of htmx, alpine, plotly, fonts.css + fonts/*.woff2 (offline)
├── pyproject.toml           # separate from root ccp; adds ccp-performance as editable path dep
└── package.json             # Electron deps
```

Each page:
- View in `evaluation/views.py` builds a plain context dict (no forms framework)
- Template extends `base.html`, fills `content` / `inspector` / `top_right` / `status` blocks
- Declares `{% block app_type %}<slug>{% endblock %}` so the shared save/load JS knows which `/save/<app_type>/` endpoint to hit
- Page-specific JS goes in `{% block extra_js %}`; shared JS (state collect/apply, curve upload, tweaks) lives in `base.html`

## Running

```bash
# dev — Django only, open in browser
uv run python manage.py runserver 8418

# full Electron shell
npm install            # first time
npm start
```

Pages: `/` (performance evaluation, still mocky), `/straight-through/` (the working one).

## Endpoints

- `POST /save/<app_type>/` — body `{state, filename}` → returns `.ccp` zip bytes with `Content-Disposition`.
- `POST /load/` — multipart `file=@*.ccp` → returns `{version, state}`. Detects Streamlit-format files and adapts them on the fly.
- `POST /calculate/straight-through/` — body `{form, gas_composition, curveImages}` → returns `{speed_operational_rpm, test_flange_points, converted_points, charts}`. `charts` is a dict of plotly figure JSON keyed by `mach | reynolds | head | eff | discharge_pressure | power`.

## `.ccp` file format

A zip archive containing:
- `ccp.version` — version string (`desktop-<v>` on the desktop, `0.3.x` on Streamlit).
- `session_state.json` — the state dict.
- `fig_<curve>.png` — optional curve image uploads, at the zip root (matches Streamlit).

**Two schemas coexist inside `session_state.json`:**
- **Desktop** (what save writes now): nested `{form: {...}, gas_composition: {components[15], cases[6]}, curveImages?}`
- **Streamlit** (what the ccp app writes): flat `{flow_point_guarantee: "...", suction_pressure_point_guarantee: "...", gas_compositions_table: {gas_0: {...}}, ...}` — 14 components indexed 0..13.

`_adapt_streamlit_state()` in `views.py` bridges from Streamlit → desktop on load. The reverse direction (desktop → Streamlit-loadable) is **not** implemented — a `.ccp` saved by this app won't open in the Streamlit app, though PNG curves round-trip byte-identically because we use the exact same `fig_*.png` naming at the zip root. If bidirectional compatibility is ever needed, write the adapter in the save endpoint too.

## Client-side state API (`window.CCP`)

Defined in `base.html`. Pages opt in by setting `{% block app_type %}`.

- `CCP.collectState()` → `{form, gas_composition, curveImages}`. Walks every `[name]` input under `#main`, plus the gas table (component selects, case names, cell values, hues), plus `window.CCP.curveImages`.
- `CCP.applyState(state)` — reverse. After restoring gas table values, dispatches `input` events so the page's own recalc code updates bars/totals.
- `CCP.save()` / `CCP.load()` — top-bar Save/Open button handlers. Use Electron dialogs when `window.ccpElectron` is present, fall back to browser download / `<input type=file>` otherwise.
- `CCP.curveImages` — `{curveKey: base64String}` (no data-URL prefix). Populated from file inputs with `data-curve-key=...` or from load responses.

## Dual-mode design (Electron vs hosted browser)

The Django endpoints are format-only — they produce or consume `.ccp` bytes over HTTP and never touch the filesystem. Delivery is the layer that varies:

- **Electron renderer** — hands bytes to `main.js` through IPC (`ccp:saveFile` / `ccp:openFile`), which shows `dialog.showSaveDialog` / `showOpenDialog` and reads/writes via `fs/promises`.
- **Plain browser** — `<a download>` for save and a hidden `<input type=file>` for load. Same endpoints, different delivery.

Don't introduce server-side session storage or per-user DB models to extend save/load — if/when that's needed, layer it as a *second* save target alongside the file flow, not a replacement.

## Design system

- Tokens in `:root` of `static/css/app.css` — oklch palette, type, density
- Theme via `html[data-mode]`, `html[data-type]`, `html[data-density]` attributes
- Palette/hue/mode persisted to `localStorage` (key: `ccp-tweaks`) by script in `base.html`
- Fonts: Geist + Geist Mono from Google Fonts. Alternates: IBM Plex, Fraunces, JetBrains Mono
- Result charts use `.chart-grid` (auto-fit minmax(340px, 1fr)) with `.chart-card` tiles; Plotly figures get transparent paper/plot backgrounds so the theme carries through.

## Gotchas / conventions

- **`.main` must be `display: block`** — not flex. Flex-column collapses sections to viewport height and `overflow: hidden` on `.section` clips their content. Scrolling lives on `.main` itself.
- **CSS cache-buster**: `base.html` loads `app.css?v={% now 'U' %}` — every request gets a fresh URL, so CSS edits show up without forcing a hard reload.
- **`runserver --noreload`**: templates still hot-reload because the filesystem loader re-reads per request, but Python code changes need a manual restart. If you launch Django in the background make sure to kill the old process before starting a new one.
- **`barg` is defined at calc time**, not at import. Pint doesn't know "barg" out of the box — `calculate_straight_through` does `ureg.define(f"barg = 1 * bar; offset: {ambient_pressure}")` using the value from the form's Options panel, mirroring `ccp/app/pages/1_straight_through.py`. If you add new endpoints that parse pressures in gauge units, you need the same registration.
- **`Point.pressure_ratio` is `None`** by default — `Point` just stores it if given, doesn't compute it. The calc endpoint computes it in the extract step from `disch.p / suc.p`.
- **Section collapse**: each `<section class="section" x-data="{ collapsed: false }">` uses Alpine `x-show` on its `.body`. Header has `@click` that ignores clicks inside `.actions`. `#resultsSection` starts with `collapsed: false` *and* `style="display:none"` — the JS toggles `display` to reveal the expanded section; don't flip `collapsed` to reveal it or Alpine scope access gets fiddly.
- **Editable gas table**: cells are `<input>` wrapped in `<label class="cell-edit">` so the `::after` bar indicator stays on the wrapper. Reactivity is plain JS (see `extra_js` in `straight_through.html`) — totals and bars recompute on `input` events. Using Alpine for all 90 cells was avoided to keep DOM simple.
- **Gas-reference dropdowns** (`gas_point_*`, `gas_fo_*`) are rebuilt from current case names every time `applyGasTable` runs — so imported case-name aliases from a Streamlit file actually resolve.
- **No Python package**: `pyproject.toml` declares `packages = ["core", "evaluation"]` only so `uv sync` succeeds. Nothing here is meant to be importable from outside.
- **Vendored frontend assets** (`static/vendor/`) — htmx, alpine, plotly, and all woff2 files are checked in so the app runs fully offline. To upgrade a JS lib, replace the file under `static/vendor/`. To add or change fonts, edit the Google Fonts URL in `static/vendor/fonts/_vendor.py`, refetch `_remote.css` with a Chrome UA, and re-run the script — it downloads the woff2 files and rewrites `static/vendor/fonts.css` with local paths.

## Parity with the Streamlit app

When reimplementing a Streamlit page here:
- Source of truth: `../ccp/app/pages/*.py` and `../ccp/app/common.py`
- Mirror the expander structure as collapsible `.section` cards
- Mirror the `parameters_map` in `common.py` for units and labels, but keep data in plain Python lists in `views.py` (not a mutable module-level dict)
- Test data tables (multiple points × parameters) render as `<table class="test-table">` with sticky-left parameter column
- Options that were in the Streamlit sidebar expander live in a slide-out `.options-panel` opened from the section header
- For the calculation itself, mirror the sequence in `1_straight_through.py` around line 638 (build kwargs_guarantee → build test-point kwargs → `StraightThrough(...)` → extract fields). The Streamlit page is the reference for which fields are optional, how empty strings are handled, and where `Q_` conversions happen.

## What NOT to do

- Don't add a JS build step, bundler, or Tailwind unless there's a clear reason — the design tokens and HTMX/Alpine approach is the whole point.
- Don't wire Django models/migrations/auth. This is still a single-user desktop app; state lives in the view and the browser. If multi-user server-side persistence is ever needed, layer it on top of the file-based flow rather than replacing it.
- Don't change the `.ccp` zip layout (`session_state.json`, `ccp.version`, `fig_<key>.png`) without also updating the Streamlit adapter, or round-trip with existing `.ccp` files will break.
- Don't move shared client helpers (`window.CCP.*`, the top-bar Save/Open wiring) out of `base.html` unless you also wire per-page init properly — they assume the app_type meta tag and the `#runBtn` / `#resultsSection` / `#gasTable` IDs.
