"""
V09 -- Business Ownership Validator (Panel 09)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 09 (Business) outputs against internal-consistency and
plausibility rules. Emits data/processed/VALIDATION_p09_business.md
(PASS/FAIL per check). Source CSV lives under data/processed/.

CHECKS:
  V09.1  firms all positive integers
  V09.2  share_of_firms_pct in [0, 100]
  V09.3  shares sum to [90, 101]% per year (NOT exactly 100: Census ABS race groups
         overlap Hispanic ethnicity, and 'some other race'/'two or more' are partly
         omitted from the owner-race breakdown, so the 6 reported groups legitimately
         sum to ~97-99%. A sum <90 or >101 would indicate a real error.)
  V09.4  White share is the largest share each year
  V09.5  employees and payroll_thousands positive for employer firms
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
DATA_DIR = PROC

DATA = DATA_DIR / "business_ownership_by_race.csv"
REPORT = OUT_DIR / "VALIDATION_p09_business.md"


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(DATA)
    lines = ["# V09 Validation Report -- Panel 09 Business\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    if not rows:
        check("V09.load", False, f"no data at {DATA}")
        lines.append(f"\n## Result: FAIL (no data)")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines))
        print(f"\nReport: {REPORT}")
        return 1

    # V09.1 -- firms all positive integers
    bad_firms = []
    for r in rows:
        try:
            f = int(r["firms"])
            if f <= 0:
                bad_firms.append((r["year"], r["race"], r["firms"]))
        except (ValueError, TypeError):
            bad_firms.append((r["year"], r["race"], r["firms"]))
    check("V09.1 firms-positive-int", len(bad_firms) == 0,
          f"{len(bad_firms)} rows with non-positive/non-integer firms"
          + (f": {bad_firms[:5]}" if bad_firms else ""))

    # V09.2 -- share_of_firms_pct in [0, 100]
    oob = []
    for r in rows:
        s = float(r["share_of_firms_pct"])
        if not (0.0 <= s <= 100.0):
            oob.append((r["year"], r["race"], s))
    check("V09.2 share-in-[0,100]", len(oob) == 0,
          f"{len(oob)} rows outside [0, 100]" + (f": {oob[:5]}" if oob else ""))

    # V09.3 -- shares sum to [90, 101]% per year (ABS race groups overlap Hispanic;
    #          'some other race'/'two or more' partly omitted -> legitimate ~97-99%)
    year_sums: dict[str, float] = {}
    for r in rows:
        year_sums[r["year"]] = year_sums.get(r["year"], 0.0) + float(r["share_of_firms_pct"])
    bad_sums = [(y, round(s, 2)) for y, s in sorted(year_sums.items())
                if not (90.0 <= s <= 101.0)]
    sum_detail = ", ".join(f"{y}={round(s,2)}" for y, s in sorted(year_sums.items()))
    check("V09.3 shares-sum-[90,101]", len(bad_sums) == 0,
          f"{len(bad_sums)} years outside [90,101] (ABS race/ethnicity overlap is expected; "
          f"a sum <90 or >101 would be a real error)"
          + (f": {bad_sums}" if bad_sums else f" ({sum_detail})"))

    # V09.4 -- White share is the largest share each year
    not_largest = []
    black_share_detail: dict[str, float] = {}
    for y in sorted(year_sums):
        yr_rows = [r for r in rows if r["year"] == y]
        white = next((float(r["share_of_firms_pct"]) for r in yr_rows
                      if r["race"].lower().startswith("white")), 0.0)
        black = next((float(r["share_of_firms_pct"]) for r in yr_rows
                      if r["race"].lower().startswith("black")), 0.0)
        black_share_detail[y] = black
        if any(float(r["share_of_firms_pct"]) > white for r in yr_rows
               if not r["race"].lower().startswith("white")):
            not_largest.append(y)
    black_str = ", ".join(f"{y}={round(v,2)}" for y, v in black_share_detail.items())
    check("V09.4 white-largest", len(not_largest) == 0,
          f"{len(not_largest)} years where White is not largest"
          + (f": {not_largest}" if not_largest else f" (Black share: {black_str})"))

    # V09.5 -- employees and payroll positive
    bad_emp = []
    for r in rows:
        emp = float(r["employees"])
        pay = float(r["payroll_thousands"])
        if emp <= 0 or pay <= 0:
            bad_emp.append((r["year"], r["race"], emp, pay))
    check("V09.5 employees-payroll-positive", len(bad_emp) == 0,
          f"{len(bad_emp)} rows with non-positive employees/payroll"
          + (f": {bad_emp[:5]}" if bad_emp else ""))

    years = sorted(year_sums)
    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 09: {len(rows)} rows, {len(years)} years "
                 f"({years[0]}-{years[-1]}), {len(set(r['race'] for r in rows))} race groups.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
