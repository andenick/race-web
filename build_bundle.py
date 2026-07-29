#!/usr/bin/env python3
"""Build a reproducible data bundle for DuBois (race.heterodata.org).

Packages the published CSVs + data dictionary + CITATION into a single zip for
the /data download endpoint. Run before deploy:

    python build_bundle.py

Output: app/data/dubois_data_bundle.zip

Source of truth is ``app/data/`` — the repository is self-contained, so the
bundle is reproducible from a clean checkout with no external tree mounted and
no machine-specific path. (A previous revision pointed at an absolute
workstation path, which both leaked a private filesystem layout and produced a
silently EMPTY bundle anywhere that path did not exist — e.g. inside the
container. Deriving everything from ``__file__`` removes both failure modes.)

An operator refreshing the data from an upstream publish profile can point at
it explicitly:

    DUBOIS_DATA_DIR=/path/to/web/data python build_bundle.py
"""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
APP_DATA = BASE / "app" / "data"

# Default: the repo's own self-contained data directory. Override with an env
# var for an upstream refresh; never a hardcoded absolute path.
SOURCE_DIR = Path(os.environ.get("DUBOIS_DATA_DIR", APP_DATA)).resolve()

BUNDLE = APP_DATA / "dubois_data_bundle.zip"


def build() -> int:
    """Zip every published CSV plus the citation record. Returns an exit code."""
    if not SOURCE_DIR.is_dir():
        print(f"ERROR: data directory not found: {SOURCE_DIR}", file=sys.stderr)
        return 1

    APP_DATA.mkdir(parents=True, exist_ok=True)

    files: list[tuple[Path, str]] = [
        (p, f"data/{p.name}") for p in sorted(SOURCE_DIR.glob("*.csv"))
    ]

    dd = SOURCE_DIR / "data_dictionary.csv"
    if dd.is_file():
        files.append((dd, "data_dictionary.csv"))

    for citation in (SOURCE_DIR / "CITATION.cff", SOURCE_DIR.parent / "CITATION.cff"):
        if citation.is_file():
            files.append((citation, "CITATION.cff"))
            break

    if not files:
        print(f"ERROR: no CSV files found in {SOURCE_DIR} — refusing to write an "
              f"empty bundle.", file=sys.stderr)
        return 1

    with zipfile.ZipFile(BUNDLE, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in files:
            zf.write(src, arcname)

    size_kb = BUNDLE.stat().st_size / 1024
    print(f"Bundle written: {BUNDLE.name} ({size_kb:.1f} KB, {len(files)} entries)")
    for _, arcname in files:
        print(f"  {arcname}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
