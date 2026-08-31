"""
V02 -- Income Validator (Panel 02)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 02 outputs against internal-consistency and cross-source rules.
Emits data/processed/VALIDATION_p02_income.md (PASS/FAIL per check).

CHECKS:
  V02.1  black_white_ratio in [0.4, 0.8] every year
  V02.2  CPI deflation worked: some pre-2022 year has White_real_2022 > White_nominal
  V02.3  black_white_gap_dollars > 0 every year
  V02.4  No null/empty in Black_nominal or White_nominal
  V02.5  Asian income >= White income every year (asian_white_ratio >= 1.0)
         -- known stylized fact; report violations but do NOT fail
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

INCOME = OUT_DIR / "income_ratio.csv"
REPORT = OUT_DIR / "VALIDATION_p02_income.md"


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
    rows = _load(INCOME)
    lines = ["# V02 Validation Report -- Panel 02 Income\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V02.1 -- black_white_ratio in [0.4, 0.8]
    oob = []
    for r in rows:
        v = _f(r["black_white_ratio"])
        if not (0.4 <= v <= 0.8):
            oob.append((r["year"], v))
    check("V02.1 black-white-ratio-in-range", len(oob) == 0,
          f"{len(oob)} years outside [0.4,0.8]" + (f": {oob[:5]}" if oob else ""))

    # V02.2 -- CPI deflation worked (real > nominal for some pre-2022 year)
    deflated = []
    for r in rows:
        if int(r["year"]) < 2022:
            rn = _f(r["White_nominal"])
            rr = _f(r["White_real_2022"])
            if rr > rn:
                deflated.append((r["year"], rn, rr))
    check("V02.2 cpi-deflation-worked", len(deflated) > 0,
          f"{len(deflated)} pre-2022 years with real>nominal"
          + (f"; e.g. {deflated[0]}" if deflated else ""))

    # V02.3 -- black_white_gap_dollars > 0
    badgap = [(r["year"], _f(r["black_white_gap_dollars"])) for r in rows
              if not (_f(r["black_white_gap_dollars"]) > 0)]
    check("V02.3 gap-dollars-positive", len(badgap) == 0,
          f"{len(badgap)} non-positive gaps" + (f": {badgap[:5]}" if badgap else ""))

    # V02.4 -- no null/empty in Black_nominal or White_nominal
    nulls = [(r["year"], "Black_nominal" if not r.get("Black_nominal") else "White_nominal")
             for r in rows
             if not r.get("Black_nominal") or not r.get("White_nominal")]
    check("V02.4 no-null-nominal-income", len(nulls) == 0,
          f"{len(nulls)} null/empty cells" + (f": {nulls[:5]}" if nulls else ""))

    # V02.5 -- Asian >= White (report, do NOT fail)
    violations = []
    for r in rows:
        v = _f(r["asian_white_ratio"])
        if v < 1.0:
            violations.append((r["year"], v))
    if violations:
        detail = (f"{len(violations)} years with asian_white_ratio < 1.0 "
                  f"(reported, not failed): {violations[:5]}")
    else:
        detail = "asian_white_ratio >= 1.0 every year (consistent with stylized fact)"
    check("V02.5 asian-gte-white (informational)", True, detail)

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 02: {len(rows)}-year income ratio series (Census/Historical CPS).*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
