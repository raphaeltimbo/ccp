# desktop/ — CLAUDE.md

Context for the **Electron + Django desktop prototype**. Inherits everything from the root `CLAUDE.md`; the notes here apply only when working inside `desktop/`.

## What this is

A distributable desktop app alternative to the Streamlit UI in `ccp/app/`. Electron spawns a local Django server as a sidecar and loads it in a Chromium window — no REST API, no SPA.

Status: **prototype**. The UI shell and forms are in place; calculations are not yet wired to the `ccp` library. CoolProp is intentionally not installed in this venv yet.

## Stack

- **Electron** (main.js) — spawns Django, loads `http://127.0.0.1:<port>`
- **Django 5** — templates + views, no ORM/admin/auth used
- **HTMX + Alpine.js** — loaded from CDN in `base.html`. HTMX for server interactions, Alpine for small client state (collapsibles, tweaks panel)
- **Plain CSS** with oklch design tokens — no Tailwind build step

## Layout

```
desktop/
├── main.js                  # Electron entry — spawns Django via `uv run`
├── manage.py                # Django entry
├── core/                    # Django project (settings, urls, wsgi)
├── evaluation/              # Django app — views.py holds the view-model
├── templates/
│   ├── base.html            # app shell: top bar, nav, main, inspector, status
│   └── evaluation/          # per-page templates
├── static/css/app.css       # full design system
├── pyproject.toml           # separate from root ccp library
└── package.json             # Electron deps
```

Each page:
- View in `evaluation/views.py` builds a plain context dict (no forms framework)
- Template extends `base.html`, fills `content` / `inspector` / `top_right` / `status` blocks
- Client interactivity via `{% block extra_js %}`

## Running

```bash
# dev — Django only, open in browser
uv run python manage.py runserver 8418

# full Electron shell
npm install            # first time
npm start
```

Pages: `/` (performance evaluation), `/straight-through/`.

## Design system

- Tokens in `:root` of `static/css/app.css` — oklch palette, type, density
- Theme via `html[data-mode]`, `html[data-type]`, `html[data-density]` attributes
- Palette/hue/mode persisted to `localStorage` (key: `ccp-tweaks`) by script in `base.html`
- Fonts: Geist + Geist Mono from Google Fonts. Alternates: IBM Plex, Fraunces, JetBrains Mono

## Gotchas / conventions

- **`.main` must be `display: block`** — not flex. Flex-column collapses sections to viewport height and `overflow: hidden` on `.section` clips their content. Scrolling lives on `.main` itself.
- **CSS cache-buster**: `base.html` loads `app.css?v={% now 'U' %}` — every request gets a fresh URL, so CSS edits show up without forcing a hard reload.
- **Section collapse**: each `<section class="section" x-data="{ collapsed: false }">` uses Alpine `x-show` on its `.body`. Header has `@click` that ignores clicks inside `.actions`.
- **Editable gas table**: cells are `<input>` wrapped in `<label class="cell-edit">` so the `::after` bar indicator stays on the wrapper. Reactivity is plain JS (see `extra_js` in `straight_through.html`) — totals and bars recompute on `input` events. Using Alpine for all 90 cells was avoided to keep DOM simple.
- **No Python package**: `pyproject.toml` declares `packages = ["core", "evaluation"]` only so `uv sync` succeeds. Nothing here is meant to be importable from outside.

## Parity with the Streamlit app

When reimplementing a Streamlit page here:
- Source of truth: `../ccp/app/pages/*.py` and `../ccp/app/common.py`
- Mirror the expander structure as collapsible `.section` cards
- Mirror the `parameters_map` in `common.py` for units and labels, but keep data in plain Python lists in `views.py` (not a mutable module-level dict)
- Test data tables (multiple points × parameters) render as `<table class="test-table">` with sticky-left parameter column
- Options that were in the Streamlit sidebar expander live in a slide-out `.options-panel` opened from the section header

## What NOT to do

- Don't add a JS build step, bundler, or Tailwind unless there's a clear reason — the design tokens and HTMX/Alpine approach is the whole point.
- Don't wire Django models/migrations/auth. This is a single-user desktop app; state lives in the view and the browser.
- Don't import from the top-level `ccp` package yet — calculation integration is a separate future task. If you do, note that CoolProp/REFPROP are not currently in this venv.
