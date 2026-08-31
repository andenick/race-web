"""
V06 -- Education Validator (Panel 06)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 06 outputs against internal-consistency and stylized-fact rules.
Emits data/processed/VALIDATION_p06_education.md (PASS/FAIL per check).

CHECKS:
  V06.1  All bachelor's attainment rates in [0, 100] (hard bound)
  V06.2  White bachelor's rate > Black bachelor's rate every year
  V06.3  Asian bachelor's rate > White bachelor's rate every year (stylized fact)
  V06.4  Black-White gap (pp) strictly positive every year
  V06.5  Black/White attainment ratio in [0.4, 0.8] (Black ~60% of White)
  V06.6  Black attainment trend: last year > first year (report, not fail)
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

EDU = OUT_DIR / "education_attainment_gap.csv"
REPORT = OUT_DIR / "VALIDATION_p06_education.md"

PCT_COLS = ["White_bachelors_pct", "Black_bachelors_pct", "AIAN_bachelors_pct",
            "Asian_bachelors_pct", "White_nH_bachelors_pct", "Hispanic_bachelors_pct"]


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(EDU)
    lines = ["# V06 Validation Report -- Panel 06 Education\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V06.1 -- all attainment rates in [0, 100]
    bad_bounds = [(r["year"], c, r[c]) for r in rows for c in PCT_COLS
                  if r.get(c) and not (0.0 <= float(r[c]) <= 100.0)]
    check("V06.1 attainment-in-[0,100]", len(bad_bounds) == 0,
          f"{len(bad_bounds)} rates outside [0, 100]" + (f": {bad_bounds[:3]}" if bad_bounds else ""))

    # V06.2 -- White > Black attainment
    bad_wb = [(r["year"], r["White_bachelors_pct"], r["Black_bachelors_pct"]) for r in rows
              if r.get("White_bachelors_pct") and r.get("Black_bachelors_pct")
              and not (float(r["White_bachelors_pct"]) > float(r["Black_bachelors_pct"]))]
    check("V06.2 white->black-attainment", len(bad_wb) == 0,
          f"{len(bad_wb)} years where White attainment not > Black attainment" + (f": {bad_wb[:3]}" if bad_wb else ""))

    # V06.3 -- Asian > White attainment (stylized fact)
    bad_aw = [(r["year"], r["Asian_bachelors_pct"], r["White_bachelors_pct"]) for r in rows
              if r.get("Asian_bachelors_pct") and r.get("White_bachelors_pct")
              and not (float(r["Asian_bachelors_pct"]) > float(r["White_bachelors_pct"]))]
    check("V06.3 asian->white-attainment", len(bad_aw) == 0,
          f"{len(bad_aw)} years where Asian attainment not > White attainment" + (f": {bad_aw[:3]}" if bad_aw else ""))

    # V06.4 -- Black-White gap strictly positive
    bad_gap = [(r["year"], r["black_white_gap_pp"]) for r in rows
               if r.get("black_white_gap_pp") and not (float(r["black_white_gap_pp"]) > 0)]
    check("V06.4 black-white-gap-positive", len(bad_gap) == 0,
          f"{len(bad_gap)} years with non-positive Black-White gap" + (f": {bad_gap[:3]}" if bad_gap else ""))

    # V06.5 -- Black/White ratio in [0.4, 0.8]
    bad_ratio = [(r["year"], r["black_white_ratio"]) for r in rows
                 if r.get("black_white_ratio")
                 and not (0.4 <= float(r["black_white_ratio"]) <= 0.8)]
    check("V06.5 black-white-ratio-[0.4,0.8]", len(bad_ratio) == 0,
          f"{len(bad_ratio)} years with Black/White ratio outside [0.4, 0.8]" + (f": {bad_ratio[:3]}" if bad_ratio else ""))

    # V06.6 -- Black attainment trend: last > first (report, not fail)
    first = float(rows[0]["Black_bachelors_pct"]) if rows else 0.0
    last = float(rows[-1]["Black_bachelors_pct"]) if rows else 0.0
    trend_ok = last > first
    lines.append(f"- **V06.6 black-attainment-trend (INFO)**: "
                 f"{'rising' if trend_ok else 'NOTE'} -- "
                 f"first {rows[0]['year']}={first}, last {rows[-1]['year']}={last}, "
                 f"delta {round(last - first, 2)} pp")

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 06: {len(rows)}-year attainment series spanning "
                 f"{rows[0]['year']}-{rows[-1]['year'] if rows else '?'}.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
