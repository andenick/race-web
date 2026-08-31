"""
L11 -- MeasuringWorth Total Population Loader (Panel 10)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Prepares the clean annual US total-population backbone (1790-2024) from the
MeasuringWorth dataset. MeasuringWorth (Samuel H. Williamson, "What Was the
U.S. GDP Then?") publishes a Population column alongside nominal/real GDP and
is the standard economic-history reference for a machine-readable annual
population series.

Source: MeasuringWorth, https://www.measuringworth.com/datasets/usgdp/
License: free for research use (cite Williamson; see the site's terms)

MANUAL DOWNLOAD REQUIRED (the site serves data through a web form):
  1. Open https://www.measuringworth.com/datasets/usgdp/
  2. Request the full US GDP series (all years, "include population")
  3. Save/export the result as CSV and place it at:
         data/raw/measuringworth/USGDP_1790-2025.csv
     The file is a CSV whose first column is Year and whose FIFTH column is
     total population (in thousands-free plain persons, comma-formatted).

This loader then extracts (year, total_population) into
data/raw/census/mw_population_us.csv for P10.

WHY MEASURINGWORTH (not raw HSUS):
  MeasuringWorth publishes a clean, annual, machine-readable population series
  derived from Census. The HSUS as-enumerated decennial values (L10) are kept
  as a cross-validation reference.

CAVEAT:
  MeasuringWorth rounds population to thousands and interpolates between
  census years. Decennial-year values agree with HSUS to ~99.8% but are NOT
  identical (documented in P10's crosscheck output). For as-enumerated census
  ground truth, use the decennial Census or HSUS.

OUTPUT:
  data/raw/census/mw_population_us.csv  -- year, total_population (annual)
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

MW_SRC = RAW / "measuringworth" / "USGDP_1790-2025.csv"
OUT = RAW / "census" / "mw_population_us.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    if not MW_SRC.exists():
        print(
            f"ERROR: MeasuringWorth CSV not found: {MW_SRC}\n"
            "  Manual download required -- see this script's docstring:\n"
            "  https://www.measuringworth.com/datasets/usgdp/  ->  save as\n"
            "  data/raw/measuringworth/USGDP_1790-2025.csv",
            file=sys.stderr)
        return 1

    rows = []
    with MW_SRC.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row or len(row) < 5:
                continue
            year = row[0].strip().strip('"')
            if year == "Year":
                continue
            if not year.isdigit():
                continue
            pop = row[4].strip().strip('"').replace(",", "")
            try:
                rows.append({"year": int(year), "total_population": int(pop)})
            except ValueError:
                continue

    rows.sort(key=lambda r: r["year"])
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "total_population"])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT} ({len(rows)} years, {rows[0]['year']}-{rows[-1]['year']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
