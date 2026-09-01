#!/usr/bin/env python3
"""Build the static site for GitHub Pages.

Source of truth is the Claude Design canvas file (`*.dc.html`) so it stays
editable in the canvas editor. This copies it to `dist/index.html` and injects
the <head> metadata a real deployed page needs (title, description, social
cards, favicon, lang attribute) plus a <noscript> fallback.

Usage:
    python3 build.py                     # -> dist/
    SITE_URL=https://you.github.io/repo python3 build.py
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DIST = ROOT / "dist"
SOURCE = ROOT / "Alex Carmichael Portfolio.dc.html"

TITLE = "Alex Carmichael — Software Developer"
DESCRIPTION = (
    "Full-stack software developer in Hull, UK. Four years on production "
    "systems: B2B ecommerce, a component-driven CMS, CRM reporting, search "
    "and backend services."
)
THEME_COLOR = "#0B0C0E"

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0B0C0E"/>
  <circle cx="16" cy="16" r="6" fill="oklch(0.63 0.19 45)"/>
</svg>
"""

NOSCRIPT = """
<noscript>
  <div style="max-width:640px;margin:14vh auto;padding:0 28px;font-family:system-ui,sans-serif;color:#0B0C0E;">
    <h1 style="font-size:28px;letter-spacing:-0.03em;margin:0 0 14px;">Alex Carmichael — Software Developer</h1>
    <p style="font-size:16px;line-height:1.6;color:#55595F;margin:0 0 18px;">
      This portfolio renders with JavaScript, which is currently disabled in your browser.
      Enable it to view the site, or reach me directly at
      <a href="mailto:alexcarmichael857@gmail.com" style="color:#0B0C0E;">alexcarmichael857@gmail.com</a>.
    </p>
    <p style="font-size:15px;line-height:1.6;color:#55595F;margin:0;">
      .NET / C# / VB / Vue / JavaScript / TypeScript / MySQL / SQL Server / Solr
    </p>
  </div>
</noscript>
"""


def head_meta(site_url: str) -> str:
    tags = [
        f"<title>{TITLE}</title>",
        f'<meta name="description" content="{DESCRIPTION}">',
        '<meta name="author" content="Alex Carmichael">',
        f'<meta name="theme-color" content="{THEME_COLOR}">',
        '<link rel="icon" href="./favicon.svg" type="image/svg+xml">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{TITLE}">',
        f'<meta property="og:description" content="{DESCRIPTION}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{TITLE}">',
        f'<meta name="twitter:description" content="{DESCRIPTION}">',
    ]
    if site_url:
        url = site_url.rstrip("/") + "/"
        tags.insert(1, f'<link rel="canonical" href="{url}">')
        tags.append(f'<meta property="og:url" content="{url}">')
    return "\n".join(tags) + "\n"


def build() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"source not found: {SOURCE}")

    html = SOURCE.read_text(encoding="utf-8")

    if "<html>" not in html:
        raise SystemExit("expected a bare <html> tag to add lang= to")
    html = html.replace("<html>", '<html lang="en">', 1)

    if "</head>" not in html:
        raise SystemExit("no </head> found in source")
    html = html.replace("</head>", head_meta(os.environ.get("SITE_URL", "")) + "</head>", 1)

    if "<body>" not in html:
        raise SystemExit("no <body> found in source")
    html = html.replace("<body>", "<body>" + NOSCRIPT, 1)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    (DIST / "index.html").write_text(html, encoding="utf-8")
    (DIST / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    # Tell Pages to serve the directory verbatim (no Jekyll processing).
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    shutil.copy2(ROOT / "support.js", DIST / "support.js")

    uploads = ROOT / "uploads"
    if uploads.is_dir():
        shutil.copytree(uploads, DIST / "uploads")

    # Anything in public/ (CV, images, downloads) is copied to the site root.
    public = ROOT / "public"
    if public.is_dir():
        shutil.copytree(public, DIST, dirs_exist_ok=True)

    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, DIST / "CNAME")

    print(f"built -> {DIST}")
    for path in sorted(DIST.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(DIST)}  ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
