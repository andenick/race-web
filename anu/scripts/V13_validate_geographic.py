"""
V13 -- Geographic Validator (Panel 13)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 13 (Geographic) outputs against internal-consistency and
plausibility rules. Emits data/processed/VALIDATION_p13_geographic.md
(PASS/FAIL per check).

CHECKS:
  V13.1  at least 100 metro rows present (panel claims 390 metros)
  V13.2  black_white_ratio in [0.2, 2.5] every row (FAIL outside this band as a genuine
         implausibility; the upper bound >1.0 allows documented exceptions -- Puerto Rico
         metros, military-base towns, small micro areas where the Black sample is tiny)
  V13.2b at least 80% of metros have black_white_ratio < 1.0 (the canonical pattern;
         exceptions are documented -- typically PR/military/micro metros)
  V13.3  black_income > 0 and white_income > 0 every row
  V13.4  gap_dollars > 0 for at least 80% of metros (exceptions documented)
  V13.5  no null metro_name
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

DATA = OUT_DIR / "metro_income_gap_2022.csv"
REPORT = OUT_DIR / "VALIDATION_p13_geographic.md"


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(DATA)
    lines = ["# V13 Validation Report -- Panel 13 Geographic\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    if not rows:
        check("V13.load", False, f"no data at {DATA}")
        lines.append(f"\n## Result: FAIL (no data)")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines))
        print(f"\nReport: {REPORT}")
        return 1

    # V13.1 -- at least 100 metro rows
    check("V13.1 min-100-metros", len(rows) >= 100,
          f"{len(rows)} metro rows present (panel claims 390)")

    # V13.2 -- black_white_ratio in [0.2, 2.5] (upper bound allows PR/military/micro)
    oob = []
    for r in rows:
        ratio = float(r["black_white_ratio"])
        if not (0.2 <= ratio <= 2.5):
            oob.append((r["metro_id"], r["metro_name"], ratio))
    check("V13.2 ratio-in-[0.2,2.5]", len(oob) == 0,
          f"{len(oob)} metros outside [0.2, 2.5]"
          + (f": {oob[:5]}{'...' if len(oob)>5 else ''}" if oob else ""))

    # V13.2b -- at least 80% of metros have ratio < 1.0 (canonical pattern); document exceptions
    above = [(r["metro_id"], r["metro_name"], float(r["black_white_ratio"]))
             for r in rows if float(r["black_white_ratio"]) >= 1.0]
    pct_above = 100.0 * len(above) / len(rows)
    check("V13.2b majority-ratio<1.0", pct_above <= 20.0,
          f"{len(above)} of {len(rows)} metros ({pct_above:.1f}%) have Black income >= White "
          f"(expected: Puerto Rico, military-base towns, small micro areas with tiny Black samples): "
          + (f"{[a[1] for a in above[:8]]}{'...' if len(above)>8 else ''}" if above else "none"))

    # V13.3 -- incomes positive
    nonpos = []
    for r in rows:
        if float(r["black_income"]) <= 0 or float(r["white_income"]) <= 0:
            nonpos.append((r["metro_id"], r["metro_name"]))
    check("V13.3 incomes-positive", len(nonpos) == 0,
          f"{len(nonpos)} metros with non-positive income" + (f": {nonpos[:5]}" if nonpos else ""))

    # V13.4 -- gap_dollars > 0 for at least 80% of metros (exceptions documented)
    nongap = [(r["metro_id"], r["metro_name"], r["gap_dollars"])
              for r in rows if float(r["gap_dollars"]) <= 0]
    pct_nongap = 100.0 * len(nongap) / len(rows)
    check("V13.4 gap-positive-majority", pct_nongap <= 20.0,
          f"{len(nongap)} of {len(rows)} metros ({pct_nongap:.1f}%) with gap <= 0 "
          f"(same PR/military/micro exceptions as V13.2b): "
          + (f"{[n[1] for n in nongap[:8]]}{'...' if len(nongap)>8 else ''}" if nongap else "none"))

    # V13.5 -- no null metro_name
    nulls = [r["metro_id"] for r in rows if not r.get("metro_name")]
    check("V13.5 no-null-metro-name", len(nulls) == 0,
          f"{len(nulls)} rows with null metro_name" + (f": {nulls[:5]}" if nulls else ""))

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    avg_ratio = round(sum(float(r["black_white_ratio"]) for r in rows) / len(rows), 3)
    lines.append(f"\n*Panel 13: {len(rows)} metros (ACS 2022), avg Black/White income ratio {avg_ratio}.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
