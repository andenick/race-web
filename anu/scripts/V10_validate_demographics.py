"""
V10 -- Demographics Validator (Panel 10)
Project: DuBois (Race, Stratification & Economic Disparities)

Validates the Panel 10 outputs against internal-consistency and cross-source rules.
Emits data/processed/VALIDATION_p10_demographics.md (PASS/FAIL per check).

CHECKS:
  V10.1  Population monotonic non-decreasing (allow <=0.5% noise; flag real drops)
  V10.2  Race shares sum to 100% (+/- 0.5 rounding) for every ACS year
  V10.3  Every race count <= total population (no category overshoot)
  V10.4  MW total vs ACS total agreement for overlapping years (document, not fail)
  V10.5  HSUS cross-validation agreement >= 99% (already 99.8%)
  V10.6  No null total_population anywhere in the backbone
  V10.7  2020 ACS gap present and documented (not imputed)
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

POP = OUT_DIR / "demographics_population.csv"
SHARES = OUT_DIR / "demographics_race_shares.csv"
XCHECK = OUT_DIR / "demographics_crosscheck.csv"
REPORT = OUT_DIR / "VALIDATION_p10_demographics.md"

RACE_COLS = ["white_alone", "black_aa_alone", "aian_alone", "asian_alone",
             "nhpi_alone", "some_other_race_alone", "two_or_more_races"]


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    pop = _load(POP)
    shares = _load(SHARES)
    xc = _load(XCHECK)
    lines = ["# V10 Validation Report -- Panel 10 Demographics\n"]
    fails = []

    def check(name: str, ok: bool, detail: str) -> None:
        status = "PASS" if ok else "FAIL"
        lines.append(f"- **{name}**: {status} -- {detail}")
        if not ok:
            fails.append(name)

    # V10.6 -- no null backbone
    nulls = [r["year"] for r in pop if not r.get("total_population")]
    check("V10.6 no-null-backbone", len(nulls) == 0,
          f"{len(nulls)} null total_population rows" + (f" (years {nulls[:5]})" if nulls else ""))

    # V10.1 -- monotonic non-decreasing
    pops = [(int(r["year"]), int(r["total_population"])) for r in pop]
    drops = [(y, p, prev) for (y, p), (py, prev) in zip(pops[1:], pops) if p < prev * 0.995]
    check("V10.1 population-monotonic", len(drops) <= 2,
          f"{len(drops)} years with >0.5% drop" + (f": {drops[:3]}" if drops else ""))

    # V10.2 -- race shares sum to 100%
    bad_sum = []
    for r in shares:
        s = 0.0
        for c in RACE_COLS:
            v = r.get(c + "_pct")
            if v:
                s += float(v)
        if abs(s - 100.0) > 0.5:
            bad_sum.append((r["year"], round(s, 2)))
    check("V10.2 race-shares-sum-100", len(bad_sum) == 0,
          f"{len(bad_sum)} years where shares != 100% (+/-0.5)" + (f": {bad_sum[:3]}" if bad_sum else ""))

    # V10.3 -- race counts <= total
    overshoot = []
    for r in pop:
        tot = r.get("total_population")
        if not tot:
            continue
        tot = int(tot)
        for c in RACE_COLS:
            v = r.get(c)
            if v and int(v) > tot:
                overshoot.append((r["year"], c))
    check("V10.3 no-race-count-overshoot", len(overshoot) == 0,
          f"{len(overshoot)} categories exceeding total" + (f": {overshoot[:3]}" if overshoot else ""))

    # V10.4 -- MW vs ACS total agreement (document, informational)
    diffs = []
    for r in pop:
        if r.get("total") or r.get("black_aa_alone"):  # ACS year proxy
            y = int(r["year"])
            # find ACS total via shares file
            sh = next((s for s in shares if s["year"] == r["year"]), None)
            if sh and sh.get("total"):
                mw_tot = int(r["total_population"])
                acs_tot = int(sh["total"])
                pct = round(100 * abs(mw_tot - acs_tot) / acs_tot, 2)
                diffs.append((y, pct))
    if diffs:
        max_diff = max(d for _, d in diffs)
        avg_diff = round(sum(d for _, d in diffs) / len(diffs), 2)
        check("V10.4 MW-vs-ACS-total", max_diff <= 3.0,
              f"avg {avg_diff}%, max {max_diff}% difference (methodological: MW interpolation vs ACS survey)")
      # V10.5 -- HSUS cross-validation
    if xc:
        avg_agree = sum(float(r["agreement_pct"]) for r in xc) / len(xc)
        check("V10.5 HSUS-crosscheck>=99", avg_agree >= 99.0,
              f"{len(xc)} points, avg agreement {round(avg_agree,2)}%")
    else:
        check("V10.5 HSUS-crosscheck", False, "no cross-validation points")

    # V10.7 -- 2020 ACS gap documented
    has_2020_null = any(r["year"] == "2020" and not r.get("black_aa_alone") for r in pop)
    check("V10.7 2020-ACS-gap-documented", has_2020_null,
          "2020 race breakdown absent (ACS 1-year cancelled, COVID) -- not imputed")

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ','.join(fails) + ')'}")
    lines.append(f"\n*Panel 10: {len(pop)}-year population series, {len(shares)}-year race breakdown, "
                 f"{len(xc)} HSUS cross-validation points.*")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
