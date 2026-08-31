"""
V04 -- Poverty Validator (Panel 04)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 04 outputs against internal-consistency and stylized-fact rules.
Emits data/processed/VALIDATION_p04_poverty.md (PASS/FAIL per check).

CHECKS:
  V04.1  Black/White poverty ratio in [1.5, 3.0] every year
  V04.2  Black poverty rate > White poverty rate every year
  V04.3  Black-White gap (pp) strictly positive every year
  V04.4  All poverty rates in [0, 50] (plausibility bound; rates are percentages)
  V04.5  No poverty rate exceeds 100 or goes negative (hard bound)
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

POVERTY = OUT_DIR / "poverty_gap.csv"
REPORT = OUT_DIR / "VALIDATION_p04_poverty.md"

RATE_COLS = ["all_poverty_rate", "white_poverty_rate", "black_poverty_rate",
             "aian_poverty_rate", "asian_poverty_rate", "white_nh_poverty_rate",
             "hispanic_poverty_rate"]


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(POVERTY)
    lines = ["# V04 Validation Report -- Panel 04 Poverty\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V04.5 -- hard bound: rates never negative, never > 100
    bad_hard = [(r["year"], c, r[c]) for r in rows for c in RATE_COLS
                if r.get(c) and (float(r[c]) < 0 or float(r[c]) > 100)]
    check("V04.5 rates-in-[0,100]", len(bad_hard) == 0,
          f"{len(bad_hard)} rates outside [0, 100]" + (f": {bad_hard[:3]}" if bad_hard else ""))

    # V04.4 -- plausibility: all rates in [0, 50]
    bad_plaus = [(r["year"], c, r[c]) for r in rows for c in RATE_COLS
                 if r.get(c) and not (0.0 <= float(r[c]) <= 50.0)]
    check("V04.4 rates-in-[0,50]", len(bad_plaus) == 0,
          f"{len(bad_plaus)} rates outside [0, 50] plausibility band" + (f": {bad_plaus[:3]}" if bad_plaus else ""))

    # V04.1 -- Black/White poverty ratio in [1.5, 3.0]
    bad_ratio = [(r["year"], r["black_white_poverty_ratio"]) for r in rows
                 if r.get("black_white_poverty_ratio")
                 and not (1.5 <= float(r["black_white_poverty_ratio"]) <= 3.0)]
    check("V04.1 black-white-ratio-[1.5,3.0]", len(bad_ratio) == 0,
          f"{len(bad_ratio)} years with ratio outside [1.5, 3.0]" + (f": {bad_ratio[:3]}" if bad_ratio else ""))

    # V04.2 -- Black poverty rate > White poverty rate
    bad_bw = [(r["year"], r["white_poverty_rate"], r["black_poverty_rate"]) for r in rows
              if r.get("white_poverty_rate") and r.get("black_poverty_rate")
              and not (float(r["black_poverty_rate"]) > float(r["white_poverty_rate"]))]
    check("V04.2 black-rate->white-rate", len(bad_bw) == 0,
          f"{len(bad_bw)} years where Black rate not > White rate" + (f": {bad_bw[:3]}" if bad_bw else ""))

    # V04.3 -- Black-White gap (pp) strictly positive
    bad_gap = [(r["year"], r["black_white_gap_pp"]) for r in rows
               if r.get("black_white_gap_pp") and not (float(r["black_white_gap_pp"]) > 0)]
    check("V04.3 black-white-gap-positive", len(bad_gap) == 0,
          f"{len(bad_gap)} years with non-positive Black-White gap" + (f": {bad_gap[:3]}" if bad_gap else ""))

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 04: {len(rows)}-year poverty series spanning "
                 f"{rows[0]['year']}-{rows[-1]['year'] if rows else '?'}.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
