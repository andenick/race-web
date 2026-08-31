"""
P13 -- Metro Income Gap Processor (Panel 13: Geographic Disparities)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Builds the 2022 Black-White median-household-income gap table by metro from
the raw ACS B19013A/B pull (L13_fetch_census_metro.py).

INPUT:  data/raw/census/metro_income_by_race_raw.csv
OUTPUT: data/processed/metro_income_gap_2022.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

INP = RAW / "census" / "metro_income_by_race_raw.csv"
OUT = PROC / "metro_income_gap_2022.csv"


def main() -> int:
    if not INP.exists():
        print(f"FATAL: {INP} missing -- run L13_fetch_census_metro.py first", flush=True)
        return 1
    rows = [r for r in csv.DictReader(INP.open(encoding="utf-8")) if r.get("gap_dollars")]
    for r in rows:
        r["gap_dollars"] = int(r["gap_dollars"])
        r["white_income"] = int(r["white_income"])
        r["black_income"] = int(r["black_income"])
        r["black_white_ratio"] = float(r["black_white_ratio"])
    rows.sort(key=lambda r: r["gap_dollars"], reverse=True)
    fields = ["metro_id", "metro_name", "white_income",
              "black_income", "black_white_ratio", "gap_dollars"]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {OUT} ({len(rows)} metros with both races)")
    print("\nTop 10 widest Black-White income gaps (metros):")
    print(f"{'Metro':<40}{'White':>10}{'Black':>10}{'Ratio':>7}")
    for r in rows[:10]:
        print(f"{r['metro_name'][:39]:<40}{r['white_income']:>10,}{r['black_income']:>10,}{r['black_white_ratio']:>7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
