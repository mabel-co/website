#!/usr/bin/env python3
"""Class-coverage gate for the website AND the compliance dashboard
(Issue #1660, P0b; dashboard sweep added by Issue #2571).

Design Review v2 (_departments/website/design-review-v2.md §3) found that the
old hand-maintained `public/style.css` silently omitted 35 of the 130 Tailwind
utility classes referenced by the Astro pages: markup was written as if a real
Tailwind pipeline existed, nothing failed, and dead classes shipped. This script
is the regression gate so that cannot recur:

    every class token referenced in the scanned sources MUST exist as a
    selector in the committed stylesheet.

It reads the *committed* `public/style.css`, so it runs in CI without invoking
the Tailwind build (`make style` regenerates the artifact; `make check`
runs `astro check` plus this gate). If someone edits the pages without
re-running the build, or hand-edits the CSS and drops a utility, this fails.

Since Issue #2571 the dashboard renders from this same committed artifact, so
the gate is the dashboard's CSS gate too: a class token emitted by dashboard
markup that the artifact lacks fails the build, exactly as for the website.

Scanned sources (the same surface the build's @source globs + an explicit
public/js sweep cover):
  * class="..."   and class='...'  in src/**/*.astro
  * className = '...' assignments  in public/js/*.js (script is:inline assets)
  * class="..."   and class='...'  in
    apps/compliance-dashboard/compliance_dashboard/*.py (server-rendered HTML)

Deliberately NOT scanned: Tailwind's own generated file (public/style.css) is
the artifact under test; dist/ is gitignored build output.

Allowlist: tokens may be appended to allowlist.txt (one per line, `#`
comments). Use it for classes that are toggled by means this scanner cannot
see, never to paper over a genuinely missing utility. Exit code: 0 pass,
1 fail.

Usage: python3 scripts/style-class-coverage.py [--repo-root PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Repo-root anchors (migrated from apps/website in the private development
# repository: paths are relative to THIS repo root now; the dashboard sweep of
# #2571 only applies to the private development repo and stays inert here —
# this repo has no apps/ tree).
WEBSITE_DIR = Path(".")
DASHBOARD_DIR = Path("apps/compliance-dashboard")
CLASS_ATTR_RE = re.compile(r"""class\s*=\s*(["'])(.*?)\1""", re.DOTALL)
JS_CLASSNAME_RE = re.compile(r"""className\s*=\s*(["'])(.*?)\1""", re.DOTALL)
# A CSS class selector: leading dot, then CSS identifier chars where `\X`
# (backslash + any char) is one escaped unit. Stops at whitespace, braces,
# combinators, pseudo colons, attribute brackets, semicolons (declaration
# ends), etc.
SELECTOR_TOKEN_RE = re.compile(r"[.\\](?:\\.|[^\s{}>+~,:#()\[\]/\";=\'])+")


def split_tokens(raw: str) -> set[str]:
    """Class attribute values may contain template braces; keep plain tokens."""
    tokens = set()
    for piece in raw.split():
        piece = piece.strip()
        if not piece or "{" in piece or "}" in piece or piece.startswith(":"):
            continue
        tokens.add(piece)
    return tokens


def referenced_tokens(sources_astro, sources_js, sources_py) -> dict[str, set[str]]:
    """Map token -> set of files referencing it."""
    refs: dict[str, set[str]] = {}

    def add(token: str, origin: Path) -> None:
        refs.setdefault(token, set()).add(str(origin))

    for path in sources_astro + sources_py:
        text = path.read_text(encoding="utf-8")
        for _q, value in CLASS_ATTR_RE.findall(text):
            for token in split_tokens(value):
                add(token, path)
    for path in sources_js:
        text = path.read_text(encoding="utf-8")
        for _q, value in JS_CLASSNAME_RE.findall(text):
            for token in split_tokens(value):
                add(token, path)
    return refs


def css_tokens(css_text: str) -> set[str]:
    """Unescape class names used as selectors and split compound/variant forms
    into the markup-level tokens they match.

    `.hover\\:bg-white\\/10:hover`  ->  {'hover:bg-white/10', 'bg-white/10'}
    `.sm\\:grid-cols-2`             ->  {'sm:grid-cols-2', 'grid-cols-2'}
    `.banner.ok`                    ->  {'banner.ok', 'banner', 'ok'}  (#2571:
                                         each compound segment is a token the
                                         markup actually carries)
    """
    found: set[str] = set()
    for match in SELECTOR_TOKEN_RE.finditer(css_text):
        raw = match.group(0)
        if raw.startswith("."):
            raw = raw[1:]
        # Compound class selectors: every dot-separated, UNESCAPED segment is
        # its own markup-level token (`.pill.muted` licenses `pill`+`muted`).
        for part in re.split(r"(?<!\\)\.", raw):
            # Undo CSS identifier escaping: `\:` -> `:`, `\/` -> `/`, `\[` -> `[`.
            name = re.sub(r"\\(.)", r"\1", part)
            if not name:
                continue
            found.add(name)
            # Variant prefixes: Tailwind emits the base utility too, but record
            # the implication here as well so a selector like `group-hover:x`
            # also licenses plain `x`.
            head, sep, tail = name.rpartition(":")
            if sep and tail:
                found.add(tail)
    return found


def load_allowlist(website_dir: Path) -> set[str]:
    path = website_dir / "scripts" / "style-class-allowlist.txt"
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Fail if a class token referenced by website or dashboard "
        "sources is absent from the committed stylesheet."
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    website_dir = args.repo_root / WEBSITE_DIR
    src_dir = website_dir / "src"
    css_path = website_dir / "public" / "style.css"
    dashboard_dir = args.repo_root / DASHBOARD_DIR / "compliance_dashboard"
    if not src_dir.is_dir() or not css_path.is_file():
        print(f"style-class-coverage: unexpected layout under {website_dir}", file=sys.stderr)
        return 1

    astro_sources = sorted(src_dir.rglob("*.astro"))
    js_sources = sorted((website_dir / "public" / "js").glob("*.js"))
    # Dashboard sweep (#2571): the server-rendered markup lives in the
    # package's .py modules; a missing dashboard package is not a layout
    # error the way a missing website src/ would be, it just adds no tokens.
    py_sources = sorted(dashboard_dir.glob("*.py")) if dashboard_dir.is_dir() else []
    refs = referenced_tokens(astro_sources, js_sources, py_sources)
    have = css_tokens(css_path.read_text(encoding="utf-8"))
    allowlist = load_allowlist(website_dir)

    missing = {t: files for t, files in refs.items() if t not in have and t not in allowlist}
    if missing:
        print(
            f"style-class-coverage: FAIL — {len(missing)} class token(s) referenced "
            f"by sources are absent from {css_path.relative_to(args.repo_root)}",
            file=sys.stderr,
        )
        for token in sorted(missing):
            files = ", ".join(
                sorted(str(Path(f).relative_to(args.repo_root)) for f in missing[token])
            )
            print(f"  - {token}  ({files})", file=sys.stderr)
        print(
            "Fix: run `make style` (and commit the regenerated style.css), "
            "or add the token to scripts/style-class-allowlist.txt with a reason.",
            file=sys.stderr,
        )
        return 1

    print(
        f"style-class-coverage: OK — all {len(refs)} referenced class token(s) "
        f"present in committed style.css "
        f"({len(allowlist)} allowlisted)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
