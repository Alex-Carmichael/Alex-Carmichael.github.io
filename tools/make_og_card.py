#!/usr/bin/env python3
"""Render public/media/og-card.png — the social preview image.

Deliberately carries no client content: just the name, role and stack on the
site's own dark ground, so sharing the link never discloses anything about the
systems described in the case studies.

Usage:
    python3 tools/make_og_card.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "media" / "og-card.png"

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)

CARD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; width: 1200px; height: 630px; background: #0B0C0E; color: #F6F5F1;
         font-family: Archivo, system-ui, sans-serif; overflow: hidden;
         background-image: radial-gradient(#FFFFFF14 1px, transparent 1px);
         background-size: 26px 26px; }
  .pad { padding: 76px 84px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
  .eyebrow { font-family: 'IBM Plex Mono', monospace; font-size: 20px; letter-spacing: 0.14em;
             text-transform: uppercase; color: #3986E4; margin: 0; }
  h1 { font-size: 92px; line-height: 0.98; letter-spacing: -0.045em; font-weight: 600; margin: 30px 0 0; }
  .stack { font-family: 'IBM Plex Mono', monospace; font-size: 22px; color: #8E9299; margin: 0; }
  .name { display: flex; align-items: center; gap: 14px; font-size: 26px; font-weight: 600; }
  .dot { width: 13px; height: 13px; border-radius: 50%; background: #3986E4; }
  .row { display: flex; align-items: flex-end; justify-content: space-between; gap: 40px; }
</style></head><body><div class="pad">
  <div>
    <p class="eyebrow">Software Developer — Full-stack</p>
    <h1>I build software<br>people actually use.</h1>
  </div>
  <div class="row">
    <div class="name"><span class="dot"></span>Alex Carmichael</div>
    <p class="stack">.NET / C# / Vue / TypeScript / MySQL / Solr</p>
  </div>
</div></body></html>
"""


def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if "/" in candidate:
            if Path(candidate).exists():
                return candidate
        elif shutil.which(candidate):
            return shutil.which(candidate)
    return None


def main() -> None:
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("no Chrome found — cannot render the card")

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "card.html"
        src.write_text(CARD, encoding="utf-8")
        shot = Path(tmp) / "card.png"
        proc = subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--hide-scrollbars", "--window-size=1200,630",
                "--virtual-time-budget=8000",
                f"--screenshot={shot}", src.as_uri(),
            ],
            capture_output=True, text=True,
        )
        if not shot.exists():
            sys.stderr.write(proc.stderr)
            raise SystemExit("Chrome did not produce the card")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shot, OUT)

    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
