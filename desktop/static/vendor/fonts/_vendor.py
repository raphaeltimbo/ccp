"""One-shot helper: download every woff2 referenced in _remote.css and
rewrite the stylesheet so it points at the local files. Run from this
directory:

    uv run python _vendor.py

The output is `../fonts.css` (read by base.html via {% static %}).
The `_remote.css` source is left in place for future regeneration; if
you need to add or change weights, refetch it from Google Fonts and
re-run this script.
"""

from __future__ import annotations

import hashlib
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "_remote.css"
OUT_CSS = HERE.parent / "fonts.css"

URL_RE = re.compile(r"https://fonts\.gstatic\.com/[^)]+\.woff2")


def short_name(url: str) -> str:
    """Stable, readable filename derived from the Google URL.

    Example:
        .../s/geist/v3/gyByhwUxId8gMEwSGFWNOITd.woff2
        -> geist_v3_gyByhwU.woff2
    """
    parts = url.split("/")
    family = parts[-3]
    version = parts[-2]
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{family}_{version}_{digest}.woff2"


def main() -> None:
    css = SRC.read_text(encoding="utf-8")
    urls = sorted(set(URL_RE.findall(css)))
    print(f"{len(urls)} unique woff2 URLs")

    mapping: dict[str, str] = {}
    for url in urls:
        name = short_name(url)
        target = HERE / name
        if not target.exists():
            print(f"  fetching {name}")
            with urllib.request.urlopen(url) as resp:
                target.write_bytes(resp.read())
        mapping[url] = name

    rewritten = css
    for url, name in mapping.items():
        rewritten = rewritten.replace(url, f"fonts/{name}")

    OUT_CSS.write_text(rewritten, encoding="utf-8")
    print(f"wrote {OUT_CSS.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
