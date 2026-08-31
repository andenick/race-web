"""
P03 -- Employment/Unemployment Processor (Panel 3)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_03_EMPLOYMENT

Transforms monthly BLS race-unemployment rates into the analytical panel:
  - annual averages (smooths CPS small-sample volatility)
  - Black/White and Hispanic/White unemployment RATIOS (the canonical ~2x finding)
  - percentage-point gaps
  - recession-peak identification

Source: L03 output (data/raw/fred/unemployment_monthly.csv) from BLS CPS via FRED

OUTPUT (data/processed/):
  unemployment_annual.csv     -- annual avg rate by race (long)
  unemployment_ratio.csv      -- Black/White + Hispanic/White ratio (wide, the headline)
  unemployment_recession_peaks.csv -- peak unemployment by race across NBER recessions

HEADLINE FINDING (to be confirmed by the data):
  The Black unemployment rate runs ~2x the White rate across the full 1972-2025
  series -- through booms and recessions alike. This ratio is one of the most
  stable regularities in US labor economics.
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
INP = RAW / "fred" / "unemployment_monthly.csv"
OUT = PROC

# NBER recessions (peak-to-trough) overlapping the data window
NBER_RECESSIONS = [
    ("1973-11", "1975-03", "1973-75 oil crisis"),
    ("1980-01", "1980-07", "1980 recession"),
    ("1981-07", "1982-11", "1981-82 double-dip (Volcker)"),
    ("1990-07", "1991-03", "1990-91"),
    ("2001-03", "2001-11", "2001 dot-com"),
    ("2007-12", "2009-06", "2008-09 Great Recession"),
    ("2020-02", "2020-04", "2020 COVID"),
]


def main() -> int:
    if not INP.exists():
        print(f"FATAL: {INP} missing", flush=True)
        return 1

    # load monthly -> {race: {year: [values]}}
    monthly = defaultdict(lambda: defaultdict(list))
    with INP.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            year = int(r["date"][:4])
            try:
                monthly[r["race"]][year].append(float(r["value"]))
            except (ValueError, KeyError):
                continue

    # --- 1. annual averages ------------------------------------------------
    races = sorted(monthly.keys())
    years = sorted({y for r in monthly for y in monthly[r]})
    ann_rows = []
    ann_index = {r: {} for r in races}  # race -> {year: avg}
    for y in years:
        for r in races:
            vals = monthly[r].get(y)
            if vals and len(vals) >= 6:  # require >=6 months for a valid annual avg
                avg = round(statistics.mean(vals), 2)
                ann_rows.append({"year": y, "race": r, "unemployment_rate": avg,
                                 "n_months": len(vals)})
                ann_index[r][y] = avg
    ann_path = OUT / "unemployment_annual.csv"
    with ann_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race", "unemployment_rate", "n_months"])
        w.writeheader(); w.writerows(ann_rows)
    print(f"Wrote {ann_path} ({len(ann_rows)} rows)")

    # --- 2. ratio panel (headline) -----------------------------------------
    white = ann_index.get("White", {})
    black = ann_index.get("Black or African American", {})
    hisp = ann_index.get("Hispanic or Latino", {})
    asian = ann_index.get("Asian", {})
    ratio_rows = []
    for y in years:
        if y in white and y in black:
            ratio_rows.append({
                "year": y,
                "white_unemployment": white[y],
                "black_unemployment": black[y],
                "black_white_ratio": round(black[y] / white[y], 2),
                "black_white_gap_pp": round(black[y] - white[y], 2),
                "hispanic_unemployment": hisp.get(y),
                "hispanic_white_ratio": round(hisp[y] / white[y], 2) if y in hisp else None,
                "asian_unemployment": asian.get(y),
            })
    ratio_path = OUT / "unemployment_ratio.csv"
    with ratio_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "white_unemployment",
                          "black_unemployment", "black_white_ratio",
                          "black_white_gap_pp", "hispanic_unemployment",
                          "hispanic_white_ratio", "asian_unemployment"])
        w.writeheader(); w.writerows(ratio_rows)
    print(f"Wrote {ratio_path} ({len(ratio_rows)} years)")

    # --- 3. recession peaks -------------------------------------------------
    # reload monthly for peak detection
    monthly_all = defaultdict(lambda: defaultdict(list))
    with INP.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ym = r["date"][:7]
            try:
                monthly_all[r["race"]][ym].append(float(r["value"]))
            except (ValueError, KeyError):
                continue
    peak_rows = []
    for start, end, label in NBER_RECESSIONS:
        rec = {"recession": label, "peak": start, "trough": end}
        for r in races:
            vals = [statistics.mean(monthly_all[r][ym]) for ym in monthly_all[r]
                    if start <= ym <= end]
            if vals:
                rec[r.replace(" or African American", "").replace(" or Latino", "") + "_peak"] = round(max(vals), 1)
        peak_rows.append(rec)
    peak_path = OUT / "unemployment_recession_peaks.csv"
    fields = ["recession", "peak", "trough"] + [
        r.replace(" or African American", "").replace(" or Latino", "") + "_peak" for r in races]
    with peak_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(peak_rows)
    print(f"Wrote {peak_path} ({len(peak_rows)} recessions)")

    # --- summary -----------------------------------------------------------
    if ratio_rows:
        ratios = [r["black_white_ratio"] for r in ratio_rows if r["black_white_ratio"]]
        avg_ratio = round(statistics.mean(ratios), 2)
        min_ratio = round(min(ratios), 2)
        max_ratio = round(max(ratios), 2)
        print(f"\n--- Panel 3 Employment Summary ---")
        print(f"  Black/White unemployment ratio ({ratio_rows[0]['year']}-{ratio_rows[-1]['year']}):")
        print(f"    average {avg_ratio}x | range {min_ratio}x (tightest) .. {max_ratio}x (loosest)")
        latest = ratio_rows[-1]
        print(f"  {latest['year']}: White {latest['white_unemployment']}%, "
              f"Black {latest['black_unemployment']}% ({latest['black_white_ratio']}x)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
