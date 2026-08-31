"""
V05 -- Housing Validator (Panel 05)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 05 outputs against internal-consistency and stylized-fact rules.
Emits data/processed/VALIDATION_p05_housing.md (PASS/FAIL per check).

CHECKS:
  V05.1  All homeownership rates in [0, 100] (hard bound)
  V05.2  Black-White gap (pp) strictly positive every year
  V05.3  White homeownership rate > Black homeownership rate every year
  V05.4  Hispanic-White gap (pp) strictly positive every year
  V05.5  Black-White gap magnitude in [15, 35] pp (stable ~25-30pp gap)
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = PROC

HOUSING = OUT_DIR / "housing_ownership_gap.csv"
REPORT = OUT_DIR / "VALIDATION_p05_housing.md"

RATE_COLS = ["white_rate", "black_rate", "hispanic_rate", "asian_rate"]


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(HOUSING)
    lines = ["# V05 Validation Report -- Panel 05 Housing\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V05.1 -- all rates in [0, 100]
    bad_bounds = [(r["year"], c, r[c]) for r in rows for c in RATE_COLS
                  if r.get(c) and not (0.0 <= float(r[c]) <= 100.0)]
    check("V05.1 rates-in-[0,100]", len(bad_bounds) == 0,
          f"{len(bad_bounds)} rates outside [0, 100]" + (f": {bad_bounds[:3]}" if bad_bounds else ""))

    # V05.2 -- Black-White gap strictly positive
    bad_gap = [(r["year"], r["black_white_gap_pp"]) for r in rows
               if r.get("black_white_gap_pp") and not (float(r["black_white_gap_pp"]) > 0)]
    check("V05.2 black-white-gap-positive", len(bad_gap) == 0,
          f"{len(bad_gap)} years with non-positive Black-White gap" + (f": {bad_gap[:3]}" if bad_gap else ""))

    # V05.3 -- White rate > Black rate
    bad_wb = [(r["year"], r["white_rate"], r["black_rate"]) for r in rows
              if r.get("white_rate") and r.get("black_rate")
              and not (float(r["white_rate"]) > float(r["black_rate"]))]
    check("V05.3 white-rate->black-rate", len(bad_wb) == 0,
          f"{len(bad_wb)} years where White rate not > Black rate" + (f": {bad_wb[:3]}" if bad_wb else ""))

    # V05.4 -- Hispanic-White gap strictly positive
    bad_hgap = [(r["year"], r["hispanic_white_gap_pp"]) for r in rows
                if r.get("hispanic_white_gap_pp") and not (float(r["hispanic_white_gap_pp"]) > 0)]
    check("V05.4 hispanic-white-gap-positive", len(bad_hgap) == 0,
          f"{len(bad_hgap)} years with non-positive Hispanic-White gap" + (f": {bad_hgap[:3]}" if bad_hgap else ""))

    # V05.5 -- Black-White gap magnitude in [15, 35] pp
    bad_mag = [(r["year"], r["black_white_gap_pp"]) for r in rows
               if r.get("black_white_gap_pp")
               and not (15.0 <= float(r["black_white_gap_pp"]) <= 35.0)]
    check("V05.5 black-white-gap-[15,35]", len(bad_mag) == 0,
          f"{len(bad_mag)} years with Black-White gap outside [15, 35] pp"
          + (f": {bad_mag[:3]}" if bad_mag else ""))

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 05: {len(rows)}-year homeownership series spanning "
                 f"{rows[0]['year']}-{rows[-1]['year'] if rows else '?'}.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
