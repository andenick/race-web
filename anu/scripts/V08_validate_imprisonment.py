"""
V08 -- Imprisonment Validator (Panel 08)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 08 (Criminal Justice) outputs against internal-consistency
and plausibility rules. Emits data/processed/VALIDATION_p08_imprisonment.md
(PASS/FAIL per check).

CHECKS:
  V08.1  black_white_ratio in [3.0, 8.0] every year (FAIL outside)
  V08.2  black_rate > white_rate every year
  V08.3  all rates non-negative; black_rate <= 2500 (per-100K plausibility)
  V08.4  black_white_gap > 0 every year
  V08.5  decarceration trend -- last-year ratio < first-year (report, not fail)
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

DATA = OUT_DIR / "imprisonment_by_race.csv"
REPORT = OUT_DIR / "VALIDATION_p08_imprisonment.md"


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = _load(DATA)
    lines = ["# V08 Validation Report -- Panel 08 Imprisonment\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    if not rows:
        check("V08.load", False, f"no data at {DATA}")
        lines.append(f"\n## Result: FAIL (no data)")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines))
        print(f"\nReport: {REPORT}")
        return 1

    # V08.1 -- black_white_ratio in [3.0, 8.0]
    bad_ratio = []
    for r in rows:
        ratio = float(r["black_white_ratio"])
        if not (3.0 <= ratio <= 8.0):
            bad_ratio.append((r["year"], ratio))
    check("V08.1 ratio-in-[3,8]", len(bad_ratio) == 0,
          f"{len(bad_ratio)} years outside [3.0, 8.0]" + (f": {bad_ratio[:5]}" if bad_ratio else ""))

    # V08.2 -- black_rate > white_rate
    inv = []
    for r in rows:
        if float(r["black_rate"]) <= float(r["white_rate"]):
            inv.append((r["year"], r["black_rate"], r["white_rate"]))
    check("V08.2 black>white", len(inv) == 0,
          f"{len(inv)} years where black_rate <= white_rate" + (f": {inv[:5]}" if inv else ""))

    # V08.3 -- non-negative rates; black_rate <= 2500
    neg = []
    over = []
    rate_cols = ["white_rate", "black_rate", "hispanic_rate", "aian_rate", "asian_rate"]
    for r in rows:
        for c in rate_cols:
            v = float(r[c])
            if v < 0:
                neg.append((r["year"], c, v))
        if float(r["black_rate"]) > 2500:
            over.append((r["year"], r["black_rate"]))
    check("V08.3 rates-plausible", len(neg) == 0 and len(over) == 0,
          f"{len(neg)} negative rates, {len(over)} black_rate>2500"
          + (f": neg {neg[:3]} over {over[:3]}" if (neg or over) else ""))

    # V08.4 -- black_white_gap > 0
    gaps = [(r["year"], r["black_white_gap"]) for r in rows
            if float(r["black_white_gap"]) <= 0]
    check("V08.4 gap-positive", len(gaps) == 0,
          f"{len(gaps)} years with gap <= 0" + (f": {gaps[:5]}" if gaps else ""))

    # V08.5 -- decarceration trend (report, not fail)
    first = float(rows[0]["black_white_ratio"])
    last = float(rows[-1]["black_white_ratio"])
    declined = last < first
    check("V08.5 decarceration-trend", declined,
          f"first-year {first} -> last-year {last} ({'declined' if declined else 'NOT declined'})")

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 08: {len(rows)}-year BJS imprisonment series "
                 f"({rows[0]['year']}-{rows[-1]['year']}), avg Black/White ratio "
                 f"{round(sum(float(r['black_white_ratio']) for r in rows)/len(rows), 2)}.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
