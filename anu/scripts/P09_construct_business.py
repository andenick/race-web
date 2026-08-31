"""
P09 -- Business Ownership Processor (Panel 9)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Promotes the Census ABS Company Summary pull (employer firms, employees,
payroll, and share of firms by owner race, fetched by L09_fetch_census_abs.py
into data/raw/census/) to the panel output table.

OUTPUT (data/processed/):
  business_ownership_by_race.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

INP = RAW / "census" / "business_ownership_by_race.csv"
OUT = PROC / "business_ownership_by_race.csv"


def main() -> int:
    if not INP.exists():
        print(f"FATAL: {INP} missing -- run L09_fetch_census_abs.py first", flush=True)
        return 1
    rows = list(csv.DictReader(INP.open(encoding="utf-8")))
    fields = list(rows[0].keys()) if rows else []
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
