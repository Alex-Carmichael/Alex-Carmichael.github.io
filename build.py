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
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
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
OG_IMAGE = "media/og-card.png"
OG_IMAGE_ALT = "Alex Carmichael — full-stack software developer. I build software people actually use."

# Chrome is used to prerender the page so crawlers and no-JS clients get real
# content instead of the runtime's mustache template.
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#0B0C0E"/>
  <circle cx="16" cy="16" r="6" fill="oklch(0.62 0.16 255)"/>
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
        # The runtime hides the raw template at boot; without JS nothing does,
        # so the mustache source would render under the prerendered copy.
        "<style>x-dc{display:none!important}</style>",
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
        # og:image must be absolute, so it only goes in when the URL is known.
        tags.append(f'<meta property="og:image" content="{url}{OG_IMAGE}">')
        tags.append(f'<meta property="og:image:alt" content="{OG_IMAGE_ALT}">')
        tags.append(f'<meta name="twitter:image" content="{url}{OG_IMAGE}">')
    return "\n".join(tags) + "\n"


def extract_root(dom: str) -> str | None:
    """Inner HTML of #dc-root, found by balancing <div> tags."""
    open_tag = '<div id="dc-root">'
    start = dom.find(open_tag)
    if start == -1:
        return None
    pos = start + len(open_tag)
    depth = 1
    for m in re.finditer(r"<div\b|</div>", dom[pos:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return dom[pos : pos + m.start()]
    return None


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        if "/" in candidate:
            if Path(candidate).exists():
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def prerender(dist: Path) -> bool:
    """Bake the rendered DOM into index.html.

    The page renders entirely client-side, so without this a crawler (or a
    LinkedIn/Slack unfurl, or an ATS scraper) sees the runtime's `{{ }}`
    template instead of the copy. Chrome renders the built page; the resulting
    #dc-root markup and the styles the runtime injected are written back into
    the file. The runtime still boots normally and drops the static copy once
    it has mounted, so interactivity is unchanged.
    """
    chrome = find_chrome()
    if not chrome:
        print("  ! no Chrome found - skipping prerender")
        return False

    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = partial(QuietHandler, directory=str(dist))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        proc = subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=20000", "--dump-dom",
                f"http://127.0.0.1:{port}/",
            ],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        server.shutdown()

    dom = proc.stdout
    body_html = extract_root(dom)
    if not body_html or len(body_html) < 5000:
        print("  ! prerender produced no usable DOM - skipping")
        return False
    if "{{" in body_html:
        print("  ! prerender still contains template markers - skipping")
        return False

    head = dom[: dom.find("</head>")]
    styles = re.findall(r"<style[^>]*>.*?</style>", head, re.S)
    fonts = re.findall(r'<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>', head)

    index = dist / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace(
        "</head>",
        "\n".join(fonts + styles)
        + "\n<style>#dc-root:not(:empty) ~ #dc-prerender{display:none}</style>\n</head>",
        1,
    )
    html = html.replace("<x-dc>", f'<div id="dc-prerender">{body_html}</div>\n<x-dc>', 1)
    html = html.replace(
        "</body>",
        "<script>(function(){function p(){var r=document.getElementById('dc-root'),"
        "s=document.getElementById('dc-prerender');"
        "if(r&&r.firstChild&&s){s.remove();return true}return false}"
        "if(!p()){new MutationObserver(function(m,o){if(p())o.disconnect()})"
        ".observe(document.body,{childList:true,subtree:true})}})();</script>\n</body>",
        1,
    )
    index.write_text(html, encoding="utf-8")
    print(f"  prerendered {len(body_html):,} chars of static markup")
    return True


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

    prerender(DIST)

    print(f"built -> {DIST}")
    for path in sorted(DIST.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(DIST)}  ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
