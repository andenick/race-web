"""
V03 -- Employment Validator (Panel 03)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 03 outputs against internal-consistency and cross-source rules.
Emits data/processed/VALIDATION_p03_employment.md (PASS/FAIL per check).

CHECKS:
  V03.1  black_unemployment >= white_unemployment EVERY year (the ~2x regularity)
  V03.2  black_white_ratio in [1.0, 3.5] every year
  V03.3  Ratio file spans >= 53 years (1972-2025)
  V03.4  Annual file has all 4 races for modern years (no expected 2020+ year
         missing White/Black/Hispanic/Asian)
  V03.5  Recession peaks file present and non-empty (informational)
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

RATIO = OUT_DIR / "unemployment_ratio.csv"
ANNUAL = OUT_DIR / "unemployment_annual.csv"
PEAKS = OUT_DIR / "unemployment_recession_peaks.csv"
REPORT = OUT_DIR / "VALIDATION_p03_employment.md"

# Canonical BLS race labels as they appear in the annual file
EXPECTED_RACES = {"White", "Black or African American",
                  "Hispanic or Latino", "Asian"}


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v) -> float:
    if v is None or v == "":
        return float("nan")
    return float(v)


def main() -> int:
    ratio = _load(RATIO)
    annual = _load(ANNUAL)
    peaks = _load(PEAKS)
    lines = ["# V03 Validation Report -- Panel 03 Employment\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V03.1 -- black_unemployment >= white_unemployment every year
    viol = []
    for r in ratio:
        b = _f(r["black_unemployment"])
        w = _f(r["white_unemployment"])
        if not (b >= w):
            viol.append((r["year"], w, b))
    check("V03.1 black-gte-white-every-year", len(viol) == 0,
          f"{len(viol)} years violating black>=white" + (f": {viol[:5]}" if viol else ""))

    # V03.2 -- black_white_ratio in [1.0, 3.5]
    oob = []
    for r in ratio:
        v = _f(r["black_white_ratio"])
        if not (1.0 <= v <= 3.5):
            oob.append((r["year"], v))
    check("V03.2 ratio-in-range", len(oob) == 0,
          f"{len(oob)} years outside [1.0,3.5]" + (f": {oob[:5]}" if oob else ""))

    # V03.3 -- ratio file spans >= 53 years (1972-2025)
    yr = sorted(int(r["year"]) for r in ratio)
    span = (yr[-1] - yr[0] + 1) if yr else 0
    check("V03.3 ratio-span-53-years", len(yr) >= 53,
          f"{len(yr)} years ({yr[0]}-{yr[-1]})" if yr else "empty")

    # V03.4 -- annual file has all 4 races for modern years (2020+)
    modern = [y for y in range(2020, (max(int(r["year"]) for r in annual) if annual else 2020) + 1)]
    by_year = {}
    for r in annual:
        by_year.setdefault(int(r["year"]), set()).add(r["race"])
    missing_races = []
    for y in modern:
        present = by_year.get(y, set())
        if not EXPECTED_RACES.issubset(present):
            missing_races.append((y, sorted(EXPECTED_RACES - present)))
    check("V03.4 annual-modern-4-races", len(missing_races) == 0,
          f"{len(modern)} modern years checked; {len(missing_races)} missing a race"
          + (f": {missing_races[:5]}" if missing_races else ""))

    # V03.5 -- recession peaks present and non-empty (informational)
    check("V03.5 recession-peaks-present (informational)", len(peaks) > 0,
          f"{len(peaks)} recession peaks recorded" + (f" ({peaks[0]['recession']} ... "
                  f"{peaks[-1]['recession']})" if peaks else ""))

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 03: {len(ratio)}-year ratio series, {len(annual)} annual rows, "
                 f"{len(peaks)} recession peaks.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
