"""Smoke-test the ccp import chain in a frozen (PyInstaller) bundle.

Run via the packaged sidecar:

    ccp-django(.exe) check_ccp

Exits non-zero on any missing module. Used in CI to catch runtime import
errors that the `runserver` smoke test misses (the calc view imports ccp
lazily inside the request handler).
"""

from django.core.management.base import BaseCommand, CommandError


REQUIRED_IMPORTS = [
    # Hot path touched by /calculate/straight-through/
    "ccp",
    "ccp.state",
    "ccp.point",
    "ccp.compressor",
    "ccp.impeller",
    "ccp.evaluation",
    "ccp.config.fluids",
    "CoolProp.CoolProp",
    "ctREFPROP.ctREFPROP",
    # Transitive deps that have bitten us in frozen bundles before.
    "sklearn.cluster",
    "tqdm.auto",
    "plotly.graph_objects",
    "plotly.io",
    "scipy.optimize",
    "pandas",
    "toml",
    "pint",
]


class Command(BaseCommand):
    help = "Import every module the calculation path needs and exit 0 on success."

    def handle(self, *args, **options):
        import importlib

        failed = []
        for dotted in REQUIRED_IMPORTS:
            try:
                importlib.import_module(dotted)
            except Exception as e:  # noqa: BLE001
                failed.append((dotted, f"{type(e).__name__}: {e}"))

        if failed:
            for name, err in failed:
                self.stderr.write(f"FAIL {name}: {err}")
            raise CommandError(f"{len(failed)} import(s) failed")

        # Touch one concrete symbol per module so we catch the
        # "module imported but class missing" class of failures too.
        from ccp import Q_, State  # noqa: F401
        from ccp.compressor import Point1Sec, StraightThrough  # noqa: F401
        from ccp.point import Point  # noqa: F401

        self.stdout.write(
            self.style.SUCCESS(
                f"ccp imports OK ({len(REQUIRED_IMPORTS)} modules verified)"
            )
        )
