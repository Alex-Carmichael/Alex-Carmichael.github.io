#!/usr/bin/env python3
"""Export the current Word CV to the PDF served by the portfolio site.

Run `python3 tools/cv_to_pdf.py` after changing cv-source/Alex-Carmichael-CV.docx.
Requires LibreOffice, either bundled in the Codex runtime or installed locally.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "cv-source" / "Alex-Carmichael-CV.docx"
PDF = ROOT / "public" / "Alex-Carmichael-CV.pdf"


def soffice_path() -> str:
    runtime_root = os.environ.get("CODEX_PRIMARY_RUNTIME_ROOT")
    candidates = []
    if runtime_root:
        candidates.append(Path(runtime_root) / "dependencies/bin/override/soffice")
    candidates.append(Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("soffice")
    if found:
        return found
    raise SystemExit("LibreOffice is required to export the CV PDF")


def main() -> None:
    if not DOCX.is_file():
        raise SystemExit(f"CV not found: {DOCX}")
    with tempfile.TemporaryDirectory(prefix="cv-export-") as folder:
        tmp = Path(folder)
        profile = (tmp / "profile").as_uri()
        result = subprocess.run(
            [soffice_path(), f"-env:UserInstallation={profile}", "--headless",
             "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(tmp), str(DOCX)],
            capture_output=True, text=True,
        )
        converted = tmp / f"{DOCX.stem}.pdf"
        if result.returncode != 0 or not converted.is_file():
            raise SystemExit(f"Could not export CV: {result.stderr or result.stdout}")
        shutil.copy2(converted, PDF)
    print(f"wrote {PDF.relative_to(ROOT)} ({PDF.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
