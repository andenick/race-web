"""
P02 -- Income & Poverty Processor (Panels 2 & 4)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Transforms ACS income-by-race and poverty-by-race (L02) into analytical panels:
  - income ratios (Black/White, Hispanic/White, Asian/White)
  - REAL (CPI-deflated to 2022$) median income by race
  - poverty rate gaps (Black - White, Hispanic - White) and ratios

Inputs:
  data/raw/census/income_by_race.csv   (L02: ACS B19013 + race iterations)
  data/raw/census/poverty_by_race.csv  (L02: ACS B17001 + race iterations)
  data/raw/fred/cpi_monthly.csv        (L04: CPIAUCSL, FRED fredgraph)

OUTPUT (data/processed/):
  income_ratio.csv  -- median HH income by race + ratios (nominal + real 2022$)
  poverty_gap.csv   -- poverty rate by race + Black/White + Hispanic/White gaps

HEADLINE FINDINGS:
  - Black median household income ~60% of White (persistent ~40% income gap)
  - Black poverty rate ~2x White rate
  - Income gap NARROWER than wealth gap (~18%) -- wealth compounds disadvantages
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

INP = RAW / "census"
OUT = PROC
CPI_CSV = RAW / "fred" / "cpi_monthly.csv"


def _cpi_annual():
    """Annual average CPIAUCSL -> {year: avg}. Deflator base = 2022."""
    if not CPI_CSV.exists():
        print("WARN: CPI file missing (run L04_fetch_fred_cpi.py); "
              "real-income columns will be skipped", flush=True)
        return {}, None
    monthly = defaultdict(list)
    with CPI_CSV.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                monthly[int(r["date"][:4])].append(float(r["cpi"]))
            except (ValueError, TypeError, KeyError):
                continue
    annual = {y: statistics.mean(v) for y, v in monthly.items() if len(v) >= 6}
    base = annual.get(2022)  # deflate to 2022 dollars
    return annual, base


def main() -> int:
    inc_path = INP / "income_by_race.csv"
    pov_path = INP / "poverty_by_race.csv"
    if not inc_path.exists() or not pov_path.exists():
        print("FATAL: L02 outputs missing", flush=True); return 1

    cpi_annual, cpi_base = _cpi_annual()
    print(f"CPI base (2022): {round(cpi_base, 1) if cpi_base else 'unavailable'}")

    # income by year/race
    inc = defaultdict(dict)  # year -> race_suffix -> median
    with inc_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["median_household_income"]:
                inc[int(r["year"])][r["race_suffix"]] = int(r["median_household_income"])

    # income ratio panel (nominal + real)
    inc_ratio_rows = []
    for y in sorted(inc):
        rec = {"year": y}
        deflator = cpi_base / cpi_annual[y] if (cpi_base and y in cpi_annual) else None
        for su, label in [("all", "All"), ("A", "White alone"), ("B", "Black/AA alone"),
                          ("C", "AIAN alone"), ("D", "Asian alone"),
                          ("H", "White nH"), ("I", "Hispanic")]:
            v = inc[y].get(su)
            if v:
                rec[label.replace(" alone", "").replace("/AA", "") + "_nominal"] = v
                if deflator:
                    rec[label.replace(" alone", "").replace("/AA", "") + "_real_2022"] = int(v * deflator)
        white = inc[y].get("A")
        black = inc[y].get("B")
        hisp = inc[y].get("I")
        asian = inc[y].get("D")
        if white and black:
            rec["black_white_ratio"] = round(black / white, 3)
            rec["black_white_gap_dollars"] = white - black
        if white and hisp:
            rec["hispanic_white_ratio"] = round(hisp / white, 3)
        if white and asian:
            rec["asian_white_ratio"] = round(asian / white, 3)
        inc_ratio_rows.append(rec)

    inc_cols = ["year"]
    for lab in ["All", "White", "Black", "AIAN", "Asian", "White nH", "Hispanic"]:
        inc_cols += [f"{lab}_nominal", f"{lab}_real_2022"]
    inc_cols += ["black_white_ratio", "black_white_gap_dollars",
                 "hispanic_white_ratio", "asian_white_ratio"]
    out_inc = OUT / "income_ratio.csv"
    with out_inc.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=inc_cols, extrasaction="ignore")
        w.writeheader(); w.writerows(inc_ratio_rows)
    print(f"Wrote {out_inc} ({len(inc_ratio_rows)} years)")

    # poverty gap panel
    pov = defaultdict(dict)  # year -> race_suffix -> {total, below, rate}
    with pov_path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pov[int(r["year"])][r["race_suffix"]] = {
                "total": int(r["total_pop"]) if r["total_pop"] else None,
                "rate": float(r["poverty_rate_pct"]) if r["poverty_rate_pct"] else None}
    pov_rows = []
    for y in sorted(pov):
        rec = {"year": y}
        for su, lab in [("all", "all"), ("A", "white"), ("B", "black"),
                        ("C", "aian"), ("D", "asian"), ("H", "white_nh"), ("I", "hispanic")]:
            rate = pov[y].get(su, {}).get("rate")
            rec[lab + "_poverty_rate"] = rate
        white = pov[y].get("A", {}).get("rate")
        black = pov[y].get("B", {}).get("rate")
        hisp = pov[y].get("I", {}).get("rate")
        if white and black:
            rec["black_white_gap_pp"] = round(black - white, 2)
            rec["black_white_poverty_ratio"] = round(black / white, 2)
        if white and hisp:
            rec["hispanic_white_gap_pp"] = round(hisp - white, 2)
        pov_rows.append(rec)
    pov_cols = ["year"] + [f"{l}_poverty_rate" for l in
                ["all", "white", "black", "aian", "asian", "white_nh", "hispanic"]] +\
               ["black_white_gap_pp", "black_white_poverty_ratio", "hispanic_white_gap_pp"]
    out_pov = OUT / "poverty_gap.csv"
    with out_pov.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=pov_cols, extrasaction="ignore")
        w.writeheader(); w.writerows(pov_rows)
    print(f"Wrote {out_pov} ({len(pov_rows)} years)")

    # summary
    if inc_ratio_rows:
        ratios = [r["black_white_ratio"] for r in inc_ratio_rows if r.get("black_white_ratio")]
        print(f"\n--- Income (Panel 2) Summary ---")
        print(f"  Black/White median income ratio ({inc_ratio_rows[0]['year']}-{inc_ratio_rows[-1]['year']}): "
              f"avg {round(statistics.mean(ratios),3)}")
        last = inc_ratio_rows[-1]
        print(f"  {last['year']}: White ${last.get('White_nominal'):,} (real ${last.get('White_real_2022'):,}) | "
              f"Black ${last.get('Black_nominal'):,} (real ${last.get('Black_real_2022'):,}) "
              f"= {last.get('black_white_ratio')}")
    if pov_rows:
        pr = [r["black_white_poverty_ratio"] for r in pov_rows if r.get("black_white_poverty_ratio")]
        print(f"\n--- Poverty (Panel 4) Summary ---")
        print(f"  Black/White poverty ratio avg: {round(statistics.mean(pr),2)}x")
        last = pov_rows[-1]
        print(f"  {last['year']}: White {last.get('white_poverty_rate')}% | "
              f"Black {last.get('black_poverty_rate')}% | Hispanic {last.get('hispanic_poverty_rate')}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
