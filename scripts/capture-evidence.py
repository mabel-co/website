#!/usr/bin/env python3
"""Capture rendered-page evidence for apps/website (Issue #1660).

Shoots full-page and above-the-fold screenshots of every built page at the four
verification widths from the umbrella rule (#1659): 375/640/1440/1920 px.

Run against the production build output:

    make website-build
    python3 apps/website/scripts/capture-evidence.py OUT_DIR [--pages / /continuum/ ...]

Requires Playwright (any venv that has it; the fleet hosts it at
mvp/state/venv) and a provisioned Chromium under PLAYWRIGHT_BROWSERS_PATH or
the agent's ms-playwright cache. Motion is forced to `no-preference` because
the pages animate in via data-reveal (see src/styles/input.css); the default
`reduce` emulation would screenshot the reveal styles mid-flight.

Output names: YYYY-MM-DD-<kind>-<page>[-<width>].png (date-prefixed per the
evidence convention in _departments/website/evidence/).
"""

from __future__ import annotations

import argparse
import datetime
import http.server
import pathlib
import shutil
import sys
import threading
from functools import partial

WIDTHS = (375, 640, 1440, 1920)
FOLD = 900


def serve(dist: pathlib.Path, handler_cls=http.server.SimpleHTTPRequestHandler):
    handler = partial(handler_cls, directory=str(dist))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Screenshot built website pages.")
    parser.add_argument("dist", type=pathlib.Path, help="path to apps/website/dist")
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("_departments/website/evidence"),
        help="output directory for PNGs",
    )
    parser.add_argument(
        "--pages",
        nargs="*",
        default=["", "continuum/", "continuum/pricing/", "what-we-are/", "privacy/"],
        help="paths relative to site root ('' is the homepage)",
    )
    args = parser.parse_args(argv)

    dist = args.dist.resolve()
    if not (dist / "index.html").is_file():
        print(f"error: {dist} is not a website build output", file=sys.stderr)
        return 1
    if not shutil.which("chromium") and not (pathlib.Path.home() / ".cache/ms-playwright").is_dir():
        print("error: no chromium available for playwright", file=sys.stderr)
        return 1

    from playwright.sync_api import sync_playwright

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    date = datetime.date.today().isoformat()
    httpd, base = serve(dist)
    shots = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for page_path in args.pages:
                name = page_path.strip("/").replace("/", "-") or "index"
                url = f"{base}/{page_path}"
                for width in WIDTHS:
                    # Only all four widths for the homepage (hero/nav responsive
                    # behaviour lives there); secondary pages at desktop plus
                    # narrowest mobile keeps the evidence set reviewable.
                    widths = WIDTHS if name == "index" else (375, 1440)
                    if width not in widths:
                        continue
                    ctx = browser.new_context(
                        viewport={"width": width, "height": FOLD},
                        reduced_motion="no-preference",
                    )
                    pg = ctx.new_page()
                    pg.goto(url, wait_until="networkidle")
                    pg.wait_for_timeout(700)  # let calm-reveal animations settle
                    stem = f"{date}-{name}" + (f"-{width}" if name == "index" else "")
                    pg.screenshot(path=str(out / f"{stem}-full.png"), full_page=True)
                    pg.screenshot(path=str(out / f"{stem}-fold.png"))
                    shots += 2
                    ctx.close()
            browser.close()
    finally:
        httpd.shutdown()
    print(f"captured {shots} screenshots under {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
