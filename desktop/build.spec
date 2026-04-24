# PyInstaller spec for the Django sidecar bundled into the Electron app.
#
# Usage:
#   uv run pyinstaller build.spec --noconfirm
#
# Produces dist/ccp-django/ — a onedir layout with ccp-django(.exe) next to
# its _internal/ resources. Electron's main.js spawns that exe with
# `runserver <port> --noreload`.

from PyInstaller.utils.hooks import collect_all, collect_submodules


def _collect_package(name):
    """collect_all that tolerates missing optional deps."""
    try:
        return collect_all(name)
    except Exception:  # noqa: BLE001 — optional deps are best-effort
        return [], [], []


coolprop_datas, coolprop_binaries, coolprop_hidden = collect_all("CoolProp")
ccp_datas, ccp_binaries, ccp_hidden = collect_all("ccp")
# plotly ships a pile of template data files (colorscales, default theme, etc.).
plotly_datas, plotly_binaries, plotly_hidden = _collect_package("plotly")
pint_datas, pint_binaries, pint_hidden = collect_all("pint")

hiddenimports = (
    coolprop_hidden
    + ccp_hidden
    + plotly_hidden
    + pint_hidden
    + collect_submodules("django")
    + collect_submodules("whitenoise")
    + collect_submodules("django_htmx")
    + collect_submodules("evaluation")
    + collect_submodules("core")
    + [
        "core.settings",
        "core.urls",
        "core.wsgi",
    ]
)

datas = (
    coolprop_datas
    + ccp_datas
    + plotly_datas
    + pint_datas
    + [
        ("templates", "templates"),
        ("static", "static"),
    ]
)

binaries = coolprop_binaries + ccp_binaries + plotly_binaries + pint_binaries


a = Analysis(
    ["manage.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Heavy deps we don't use in the desktop calc path.
        "IPython",
        "jupyter",
        "notebook",
        "matplotlib",
        "tkinter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ccp-django",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep stdout/stderr visible for Electron to capture
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ccp-django",
)
