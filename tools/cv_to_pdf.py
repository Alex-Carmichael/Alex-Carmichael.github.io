#!/usr/bin/env python3
"""Render public/Alex-Carmichael-CV.docx to a matching PDF.

macOS `textutil` mis-reads Word's explicit "off" run properties
(`<w:b w:val="0"/>`, `<w:strike w:val="0"/>`) as *on*, so its output comes
out bold, underlined and struck through. This walks the docx XML directly,
honouring the val attribute, and prints the result with headless Chrome.

Layout mirrors the Word document: name, contact line, uppercase section
headings, role/date rows split by the right tab stop, employer line, bullets.

Usage:
    python3 tools/cv_to_pdf.py
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "cv-source" / "Alex-Carmichael-CV.docx"
PDF = ROOT / "public" / "Alex-Carmichael-CV.pdf"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ACCENT = "#1F3D6B"
MUTED = "#444444"

CSS = f"""
@page {{ size: A4; margin: 14mm 15mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; color: #000;
        font-size: 10.5pt; line-height: 1.34; }}
h1 {{ font-size: 20pt; font-weight: bold; margin: 0 0 2pt; letter-spacing: -0.01em; }}
.contact {{ font-size: 10pt; color: {ACCENT}; margin: 0 0 2pt; }}
.contact a {{ color: {ACCENT}; text-decoration: none; }}
h2 {{ font-size: 12pt; color: {ACCENT}; margin: 13pt 0 5pt; font-weight: bold;
      letter-spacing: 0.02em; border-bottom: 0.6pt solid {ACCENT}; padding-bottom: 2pt; }}
p {{ margin: 0 0 3pt; }}
.row {{ display: flex; justify-content: space-between; align-items: baseline;
        gap: 12pt; margin: 8pt 0 0; }}
.row .date {{ font-size: 10pt; color: {MUTED}; white-space: nowrap; }}
.employer {{ font-size: 10pt; color: {MUTED}; margin: 0 0 4pt; }}
ul {{ margin: 0 0 2pt; padding-left: 14pt; }}
li {{ margin: 0 0 3pt; }}
.skills b {{ font-weight: bold; }}
"""


def run_text(run: ET.Element) -> str:
    """Inline HTML for one run, honouring explicitly-disabled properties."""
    parts = []
    for node in run:
        tag = node.tag.split("}", 1)[1]
        if tag == "t":
            parts.append(html.escape(node.text or ""))
        elif tag == "br":
            parts.append("<br>")
    text = "".join(parts)
    if not text:
        return ""

    rpr = run.find("w:rPr", NS)
    if rpr is None:
        return text

    def on(name: str) -> bool:
        el = rpr.find(f"w:{name}", NS)
        if el is None:
            return False
        # Word writes val="0"/"false"/"none" to switch a property OFF.
        return el.get(f"{{{W}}}val") not in ("0", "false", "none")

    if on("b"):
        text = f"<b>{text}</b>"
    if on("i"):
        text = f"<i>{text}</i>"
    if on("u"):
        text = f"<u>{text}</u>"
    if on("strike"):
        text = f"<s>{text}</s>"
    return text


MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
DATE_RANGE = re.compile(
    rf"^\s*(?:{MONTH}\s+)?\d{{4}}\s*[\u2013\u2014-]\s*"
    rf"(?:Present|(?:{MONTH}\s+)?\d{{4}})\s*$"
)


def para_parts(p: ET.Element) -> list[str]:
    """Split a paragraph into title / date columns.

    The document defines a right tab stop at 9746 twips but never emits a tab
    character, so Word itself runs the two together ("Junior Software
    DeveloperMay 2024 - Present"). Split on an explicit tab where one exists,
    otherwise on the first run whose text is a bare date range.
    """
    runs = []
    for run in p.findall("w:r", NS):
        has_tab = any(node.tag == f"{{{W}}}tab" for node in run)
        raw = "".join(n.text or "" for n in run.iter(f"{{{W}}}t"))
        runs.append((run_text(run), raw, has_tab))

    split_at = None
    for i, (_, raw, has_tab) in enumerate(runs):
        if has_tab or DATE_RANGE.match(raw):
            split_at = i
            break

    if split_at is None:
        return ["".join(t for t, _, _ in runs).strip()]

    left = "".join(t for t, _, _ in runs[:split_at])
    right = "".join(t for t, _, _ in runs[split_at:])
    # A trailing soft break was the document's stand-in for the missing tab.
    left = re.sub(r"(?:<br>)+(?=(?:</[bius]>)*$)", "", left.strip())
    return [left.strip(), right.strip()]


def is_bullet(p: ET.Element) -> bool:
    ppr = p.find("w:pPr", NS)
    return ppr is not None and ppr.find("w:numPr", NS) is not None


def linkify(text: str) -> str:
    text = text.replace(
        "alexcarmichael857@gmail.com",
        '<a href="mailto:alexcarmichael857@gmail.com">alexcarmichael857@gmail.com</a>',
    )
    text = text.replace(
        "linkedin.com/in/alexcarmichael12",
        '<a href="https://www.linkedin.com/in/alexcarmichael12/">linkedin.com/in/alexcarmichael12</a>',
    )
    return text


def build_html(paras: list[ET.Element]) -> str:
    out: list[str] = []
    open_list = False

    def close_list() -> None:
        nonlocal open_list
        if open_list:
            out.append("</ul>")
            open_list = False

    for index, p in enumerate(paras):
        cols = para_parts(p)
        plain = "".join(cols)
        raw = "".join(n.text or "" for n in p.iter(f"{{{W}}}t")).strip()
        if not raw:
            continue

        if is_bullet(p):
            if not open_list:
                out.append("<ul>")
                open_list = True
            out.append(f"<li>{plain}</li>")
            continue

        close_list()

        if index == 0:
            out.append(f"<h1>{raw}</h1>")
        elif index == 1:
            out.append(f'<p class="contact">{linkify(html.escape(raw))}</p>')
        elif raw.isupper() and len(cols) == 1 and len(raw) < 30:
            out.append(f"<h2>{raw}</h2>")
        elif len(cols) == 2:
            out.append(
                f'<div class="row"><div>{cols[0]}</div>'
                f'<div class="date">{cols[1]}</div></div>'
            )
        elif raw.startswith(("Styletech", "StyleTech", "Baltic", "Ron Dearing")):
            out.append(f'<p class="employer">{plain}</p>')
        elif ":" in raw and raw.split(":", 1)[0].strip() in {
            "Languages & Frameworks",
            "Databases",
            "Tools & Practices",
        }:
            head, tail = raw.split(":", 1)
            out.append(
                f'<p class="skills"><b>{html.escape(head)}:</b>{html.escape(tail)}</p>'
            )
        else:
            out.append(f"<p>{plain}</p>")

    close_list()
    return "\n".join(out)


def main() -> None:
    if not DOCX.exists():
        raise SystemExit(f"CV not found: {DOCX}")
    if not Path(CHROME).exists():
        raise SystemExit(f"Chrome not found at {CHROME} — cannot print the PDF")

    with zipfile.ZipFile(DOCX) as zf:
        xml = zf.read("word/document.xml")
    body = ET.fromstring(xml).find("w:body", NS)
    paras = body.findall("w:p", NS)

    page = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Alex Carmichael — CV</title>"
        f"<style>{CSS}</style></head><body>{build_html(paras)}</body></html>"
    )

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "cv.html"
        src.write_text(page, encoding="utf-8")
        out = Path(tmp) / "cv.pdf"
        proc = subprocess.run(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={out}",
                src.as_uri(),
            ],
            capture_output=True,
            text=True,
        )
        if not out.exists():
            sys.stderr.write(proc.stderr)
            raise SystemExit("Chrome did not produce a PDF")
        shutil.copy2(out, PDF)

    print(f"wrote {PDF.relative_to(ROOT)} ({PDF.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
