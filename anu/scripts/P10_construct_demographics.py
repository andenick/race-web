"""
P10 -- Demographics Processor (Panel 10)
Project: DuBois (Race, Stratification & Economic Disparities)

Merges three clean data streams into the Panel 10 demographics output:
  L11 MeasuringWorth  -- total_population, annual 1790-2024 (backbone)
  L10 HSUS            -- as-enumerated decennial 1790-1880 (HIGH-confidence subset;
                         cross-validation reference vs MeasuringWorth)
  L12 Census ACS      -- race counts/shares + Hispanic cross-tab, annual 2005-2022

OUTPUT (to data/processed/):
  demographics_population.csv   -- merged annual panel (1790-2024)
  demographics_race_shares.csv  -- race population shares (2005-2022, ACS)
  demographics_crosscheck.csv   -- MW vs HSUS decennial agreement audit

CONVENTIONS (per DPR_P10_DEMOGRAPHICS):
  - Race is "alone" universe (Census B02001): White, Black/AA, AIAN, Asian,
    NHPI, Some Other, Two or More. Hispanic is a separate ethnicity (B03002).
  - No synthetic/interpolated data. 2020 ACS gap is left null + documented.
  - HSUS as-enumerated carried ONLY for HIGH-confidence years (per L10 finding);
    REVIEW years are excluded from the cross-validation (not trustworthy).

KNOWN LIMITATIONS:
  - Pre-2005 race breakdown: NOT in this panel (requires HDARP HSUS re-extraction
    of series A 91-104; slated Wave 1 v2).
  - HSUS cross-validation covers only 1790, 1820, 1830, 1850, 1880 (the 5 years
    that parsed at HIGH confidence from the 2026 OCR).
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

MW_CSV = RAW / "census" / "mw_population_us.csv"
HSUS_CSV = RAW / "hsus" / "hsus_a1_8_decennial.csv"
ACS_RACE = RAW / "census" / "acs_race_us.csv"
ACS_HISP = RAW / "census" / "acs_hispanic_us.csv"


def _load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"WARN: {path.name} not found -- skipping")
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    mw = _load(MW_CSV)
    hsus = _load(HSUS_CSV)
    acs = _load(ACS_RACE)
    hisp = _load(ACS_HISP)

    if not mw:
        print("FATAL: no MeasuringWorth backbone data", flush=True)
        return 1

    # index lookups
    mw_by_year = {int(r["year"]): int(r["total_population"]) for r in mw}
    hsus_high = {int(r["year"]): int(r["total_population"])
                 for r in hsus if r.get("confidence") == "HIGH" and r.get("total_population")}
    acs_by_year = {int(r["year"]): r for r in acs if r.get("total")}
    hisp_by_year = {int(r["year"]): r for r in hisp if r.get("total")}

    RACE_COLS = ["white_alone", "black_aa_alone", "aian_alone", "asian_alone",
                 "nhpi_alone", "some_other_race_alone", "two_or_more_races"]

    # --- 1. merged population panel ----------------------------------------
    pop_path = OUT_DIR / "demographics_population.csv"
    pop_fields = ["year", "total_population", "source",
                  "hsus_as_enumerated", "hsus_agreement_pct"] + RACE_COLS + ["hispanic_total"]
    pop_rows = []
    for y in sorted(mw_by_year):
        rec = {"year": y, "total_population": mw_by_year[y], "source": "MeasuringWorth"}
        if y in hsus_high:
            hpop = hsus_high[y]
            rec["hsus_as_enumerated"] = hpop
            # agreement = how close MW is to the as-enumerated census value
            if mw_by_year[y]:
                rec["hsus_agreement_pct"] = round(100 * min(hpop, mw_by_year[y]) /
                                                  max(hpop, mw_by_year[y]), 3)
        if y in acs_by_year:
            a = acs_by_year[y]
            for c in RACE_COLS:
                v = a.get(c)
                rec[c] = int(v) if v else None
        if y in hisp_by_year:
            ht = hisp_by_year[y].get("hispanic_total")
            rec["hispanic_total"] = int(ht) if ht else None
        pop_rows.append(rec)

    with pop_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=pop_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(pop_rows)
    print(f"Wrote {pop_path} ({len(pop_rows)} years)")

    # --- 2. race shares panel (ACS years only) -----------------------------
    shares_path = OUT_DIR / "demographics_race_shares.csv"
    share_fields = ["year", "total"] + [c + "_pct" for c in RACE_COLS] + ["hispanic_pct"]
    share_rows = []
    for y in sorted(acs_by_year):
        a = acs_by_year[y]
        rec = {"year": y, "total": a.get("total")}
        for c in RACE_COLS:
            rec[c + "_pct"] = a.get(c + "_pct")
        if y in hisp_by_year:
            ht = hisp_by_year[y]
            tot = ht.get("total")
            ht_tot = ht.get("hispanic_total")
            rec["hispanic_pct"] = round(100 * int(ht_tot) / int(tot), 2) if (tot and ht_tot) else None
        share_rows.append(rec)
    with shares_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=share_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(share_rows)
    print(f"Wrote {shares_path} ({len(share_rows)} years)")

    # --- 3. cross-validation audit -----------------------------------------
    xcheck_path = OUT_DIR / "demographics_crosscheck.csv"
    xc_rows = []
    for y in sorted(hsus_high):
        hpop = hsus_high[y]
        mwpop = mw_by_year.get(y)
        if mwpop:
            diff = mwpop - hpop
            pct_diff = round(100 * diff / hpop, 3)
            agree = round(100 * min(hpop, mwpop) / max(hpop, mwpop), 3)
            xc_rows.append({"year": y, "hsus_as_enumerated": hpop,
                            "measuringworth": mwpop, "difference": diff,
                            "pct_difference": pct_diff, "agreement_pct": agree})
    with xcheck_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "hsus_as_enumerated",
                                           "measuringworth", "difference",
                                           "pct_difference", "agreement_pct"])
        w.writeheader()
        w.writerows(xc_rows)
    print(f"Wrote {xcheck_path} ({len(xc_rows)} cross-validation points)")
    if xc_rows:
        avg_agree = round(sum(r["agreement_pct"] for r in xc_rows) / len(xc_rows), 2)
        print(f"  MW vs HSUS average agreement: {avg_agree}%")

    # --- summary -----------------------------------------------------------
    print("\n--- Panel 10 Demographics Summary ---")
    print(f"  Population series: 1790-{max(mw_by_year)} ({len(mw_by_year)} years)")
    print(f"  Race breakdown: {min(acs_by_year)}-{max(acs_by_year)} ({len(acs_by_year)} yrs; 2020 gap)")
    latest = max(acs_by_year)
    a = acs_by_year[latest]
    print(f"  {latest} total: {int(a['total']):,}  "
          f"Black/AA: {int(a['black_aa_alone']):,} ({a.get('black_aa_alone_pct')}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
