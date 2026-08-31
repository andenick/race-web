"""
V01 -- Wealth Validator (Panel 01)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 01 outputs against internal-consistency and cross-source rules.
Emits data/processed/VALIDATION_p01_wealth.md (PASS/FAIL per check).

CHECKS:
  V01.1  Gap timeseries has 12 SCF waves (years 1989,1992,...,2022)
  V01.2  Every black_pct_of_white in (0, 35] and finite (1989 ~6.0 suspect but valid)
  V01.3  Every black_white_gap_dollars > 0 (wealth gap must be positive)
  V01.4  black_median_networth < white_median_networth every year
  V01.5  Long file has race_code {1,2,3} minimum every wave; 2022 also has 4 (Asian)
  V01.6  2022 values plausible (white median > 200000; black median in (0, 100000))
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = PROC

GAP = OUT_DIR / "wealth_gap_timeseries.csv"
LONG = OUT_DIR / "wealth_by_race_timeseries.csv"
REPORT = OUT_DIR / "VALIDATION_p01_wealth.md"

EXPECTED_YEARS = list(range(1989, 2023, 3))  # 1989, 1992, ..., 2022 -> 12 waves


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v) -> float:
    """Parse a CSV cell to float; treat empty as nan."""
    if v is None or v == "":
        return float("nan")
    return float(v)


def main() -> int:
    gap = _load(GAP)
    longf = _load(LONG)
    lines = ["# V01 Validation Report -- Panel 01 Wealth\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V01.1 -- 12 SCF waves
    years = sorted(int(r["year"]) for r in gap)
    missing = [y for y in EXPECTED_YEARS if y not in years]
    extra = [y for y in years if y not in EXPECTED_YEARS]
    check("V01.1 twelve-scf-waves", years == EXPECTED_YEARS,
          f"{len(years)} waves ({years[0] if years else '?'}-{years[-1] if years else '?'})"
          + (f"; missing {missing}" if missing else "")
          + (f"; extra {extra}" if extra else ""))

    # V01.2 -- black_pct_of_white in (0, 35] and finite; flag 1989 suspect
    oob = []
    suspect = []
    for r in gap:
        v = _f(r["black_pct_of_white"])
        if math.isnan(v) or v <= 0 or v > 35:
            oob.append((r["year"], v))
        if int(r["year"]) == 1989:
            suspect.append((r["year"], v))
    detail = f"{len(oob)} out-of-range values"
    if oob:
        detail += f": {oob[:5]}"
    if suspect:
        detail += f"; 1989 value {suspect[0][1]} flagged suspect (anomalously low but >0, not failed)"
    check("V01.2 black-pct-in-range", len(oob) == 0, detail)

    # V01.3 -- black_white_gap_dollars > 0
    badgap = [(r["year"], _f(r["black_white_gap_dollars"])) for r in gap
              if not (_f(r["black_white_gap_dollars"]) > 0)]
    check("V01.3 gap-dollars-positive", len(badgap) == 0,
          f"{len(badgap)} non-positive gaps" + (f": {badgap[:5]}" if badgap else ""))

    # V01.4 -- black_median < white_median every year
    inv = []
    for r in gap:
        w = _f(r["white_median_networth"])
        b = _f(r["black_median_networth"])
        if not (b < w):
            inv.append((r["year"], b, w))
    check("V01.4 black-lt-white-median", len(inv) == 0,
          f"{len(inv)} years where black >= white" + (f": {inv[:5]}" if inv else ""))

    # V01.5 -- race codes present
    by_year = {}
    for r in longf:
        by_year.setdefault(int(r["year"]), set()).add(int(r["race_code"]))
    min_ok = all({1, 2, 3}.issubset(by_year.get(y, set())) for y in EXPECTED_YEARS)
    has_2022_asian = 4 in by_year.get(2022, set())
    missing_min = [y for y in EXPECTED_YEARS if not {1, 2, 3}.issubset(by_year.get(y, set()))]
    detail = f"race_codes per wave checked; missing-min in {missing_min[:5]}" if missing_min \
        else "White(1)/Black(2)/Hispanic(3) present every wave"
    detail += "; 2022 Asian(4) " + ("present" if has_2022_asian else "MISSING")
    check("V01.5 race-codes-present", min_ok and has_2022_asian, detail)

    # V01.6 -- 2022 plausible values
    g22 = next((r for r in gap if int(r["year"]) == 2022), None)
    if g22:
        w22 = _f(g22["white_median_networth"])
        b22 = _f(g22["black_median_networth"])
        check("V01.6 2022-plausible", w22 > 200000 and 0 < b22 < 100000,
              f"white median ${w22:,.0f} (>200k), black median ${b22:,.0f} (in 0-100k)")
    else:
        check("V01.6 2022-plausible", False, "no 2022 row in gap file")

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 01: {len(gap)}-wave SCF wealth gap series, "
                 f"{len(longf)} rows in long race file.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
