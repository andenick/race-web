"""
P01 -- SCF Wealth-by-Race Processor (Panels 1 + support for analytical layer)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Assembles the Black-white / Hispanic-white wealth gap as a time series,
1989-2022 (triennial, 12 SCF waves), from the Federal Reserve SCF summary
files downloaded by L01_fetch_fed_scf.py.

Sources:
  1989-2019: data/raw/scf/{year}/scfp{year}s.dta (Stata summary files)
  2022:      data/raw/scf/2022/scfp2022s.dta (scfp2022s.zip, same convention as historical waves)
  All from https://www.federalreserve.gov/econres/scfindex.htm (public domain)

RACE-CODING HARMONIZATION (CRITICAL):
  - SCF RACE coding changed over time:
      1989-2019: 1=White nH, 2=Black nH, 3=Hispanic, 5=Other (no separate Asian)
      2022:      1=White nH, 2=Black nH, 3=Hispanic, 4=Asian, 5=Other
  - Asian is reported ONLY for 2022 (marked null for prior years -- NOT back-imputed).
  - The 4 consistently-comparable groups across all waves: White, Black, Hispanic, Other.

OUTPUT (data/processed/):
  wealth_by_race_2022.csv       -- 2022 wave detail: medians/means + asset comp by race
  wealth_gap_summary_2022.csv   -- 2022 Black/Hispanic/Asian-to-White ratios
  wealth_by_race_timeseries.csv -- long: year, race, median_nw, mean_nw, households_est
  wealth_gap_timeseries.csv     -- wide: year, white/black medians, black_pct_of_white

METHODOLOGY:
  - Weighted medians/means using SCF sample weight (wgt); 5 implicates included.
  - Weighted median = value at 50th percentile of weight-cumulative distribution.
  - Values are in CURRENT dollars of each survey wave (compare ratios across waves,
    not nominal levels).
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

SCF_DIR = RAW / "scf"
OUT_DIR = PROC

RACE_LABELS = {1: "White non-Hispanic", 2: "Black non-Hispanic",
               3: "Hispanic", 4: "Asian", 5: "Other"}
SCF_YEARS = [1989, 1992, 1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019]


def wmedian(values, weights):
    order = sorted(range(len(values)), key=lambda i: values[i])
    v = [values[i] for i in order]; w = [weights[i] for i in order]
    total = sum(w); cum = 0.0; target = 0.5 * total
    for vi, wi in zip(v, w):
        cum += wi
        if cum >= target:
            return vi
    return v[-1]


def _load_wave(year: int):
    """Read one extracted SCF wave directory (.dta or .csv) into a DataFrame."""
    import pandas as pd
    wave_dir = SCF_DIR / str(year)
    if not wave_dir.exists():
        return None
    dtas = list(wave_dir.rglob("*.dta"))
    csvs = list(wave_dir.rglob("*.csv"))
    if dtas:
        df = pd.read_stata(str(dtas[0]),
                           columns=["race", "wgt", "networth", "asset", "fin", "debt",
                                    "hhouses"] if year >= 2004 else
                          ["race", "wgt", "networth", "asset", "fin", "debt"])
        df["wgt"] = df["wgt"].astype(float)
        if "hhouses" not in df.columns:
            df["hhouses"] = float("nan")
        return df
    if csvs:
        df = pd.read_csv(csvs[0], encoding="latin-1")
        df.columns = [str(c).lower() for c in df.columns]
        keep = ["race", "wgt", "networth", "asset", "fin", "debt", "hhouses"]
        df = df[[c for c in keep if c in df.columns]]
        df["wgt"] = df["wgt"].astype(float)
        for c in ["asset", "fin", "debt", "hhouses"]:
            if c not in df.columns:
                df[c] = float("nan")
        return df
    return None


def _by_race_stats(df, detail: bool = False):
    """Compute weighted median/mean net worth by race (+ asset detail for 2022)."""
    out = {}
    for race, grp in df.groupby("race"):
        w = grp["wgt"].values; nw = grp["networth"].values
        tot_w = float(w.sum())
        rec = {
            "households_est": int(tot_w),  # WGT sums to population across all 5 implicates (verified 131.3M = US HH count); no /5
            "median_networth": int(wmedian(nw.tolist(), w.tolist())),
            "mean_networth": int((grp["networth"] * grp["wgt"]).sum() / tot_w),
        }
        if detail and grp["hhouses"].notna().any():
            for col, key in [("asset", "median_assets"), ("fin", "median_financial"),
                             ("hhouses", "median_home_equity"), ("debt", "median_debt")]:
                vals = grp[col].values
                rec[key] = int(wmedian(vals.tolist(), w.tolist()))
        out[int(race)] = rec
    return out


def main() -> int:
    ts_rows = []
    all_stats = {}
    detail22 = None

    for y in SCF_YEARS + [2022]:
        try:
            df = _load_wave(y)
            if df is None:
                print(f"  {y}: no extracted wave in {SCF_DIR / str(y)} (run L01 first)")
                continue
            detail = (y == 2022)
            stats = _by_race_stats(df, detail=detail)
            if detail:
                detail22 = stats
            all_stats[y] = stats
            for race, s in stats.items():
                ts_rows.append({"year": y, "race_code": race,
                                "race": RACE_LABELS.get(race, f"code {race}"), **s})
            b = stats.get(2, {}).get("median_networth")
            w = stats.get(1, {}).get("median_networth")
            print(f"  {y}: White med ${w:,}  Black med ${b:,}"
                  + (f"  Black={100*b/w:.1f}% of White" if (b and w) else ""))
        except Exception as e:
            print(f"  {y}: FAILED {repr(e)[:100]}", file=sys.stderr)

    if not all_stats:
        print("FATAL: no SCF waves processed -- run L01_fetch_fed_scf.py first",
              file=sys.stderr)
        return 1

    # --- 2022 detail tables (from the 2022 wave) ---
    if detail22:
        detail_rows = []
        for race in sorted(detail22):
            s = detail22[race]
            detail_rows.append({"race_code": race,
                                "race": RACE_LABELS.get(race, f"code {race}"), **s})
        detail_fields = ["race_code", "race", "households_est", "median_networth",
                         "mean_networth", "median_assets", "median_financial",
                         "median_home_equity", "median_debt"]
        detail_path = OUT_DIR / "wealth_by_race_2022.csv"
        with detail_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=detail_fields, extrasaction="ignore")
            w.writeheader(); w.writerows(detail_rows)
        print(f"\nWrote {detail_path}")

        white = detail22.get(1, {})
        wn = white.get("median_networth")
        if wn:
            gaps = []
            for race, s in detail22.items():
                if race == 1:
                    continue
                rn = s["median_networth"]
                gaps.append({
                    "race": s and RACE_LABELS.get(race, f"code {race}"),
                    "median_networth": rn,
                    "white_median_networth": wn,
                    "ratio_to_white": round(rn / wn, 3) if wn else None,
                    "absolute_gap": wn - rn,
                    "pct_of_white_wealth": round(100 * rn / wn, 1) if wn else None,
                })
            gpath = OUT_DIR / "wealth_gap_summary_2022.csv"
            with gpath.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["race", "median_networth",
                              "white_median_networth", "ratio_to_white",
                              "absolute_gap", "pct_of_white_wealth"])
                w.writeheader(); w.writerows(gaps)
            print(f"Wrote {gpath}")

    # --- long time series ---
    ts_rows.sort(key=lambda r: (r["year"], r["race_code"]))
    tspath = OUT_DIR / "wealth_by_race_timeseries.csv"
    with tspath.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_code", "race",
                          "households_est", "median_networth", "mean_networth"],
                          extrasaction="ignore")
        w.writeheader(); w.writerows(ts_rows)
    print(f"\nWrote {tspath} ({len(ts_rows)} rows)")

    # --- wide gap time series ---
    gap_path = OUT_DIR / "wealth_gap_timeseries.csv"
    gap_rows = []
    for y in sorted(all_stats):
        s = all_stats[y]
        white = s.get(1, {}).get("median_networth")
        black = s.get(2, {}).get("median_networth")
        hisp = s.get(3, {}).get("median_networth")
        gap_rows.append({
            "year": y,
            "white_median_networth": white,
            "black_median_networth": black,
            "black_pct_of_white": round(100 * black / white, 1) if (black and white) else None,
            "black_white_gap_dollars": (white - black) if (white and black) else None,
            "hispanic_median_networth": hisp,
            "hispanic_pct_of_white": round(100 * hisp / white, 1) if (hisp and white) else None,
        })
    with gap_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "white_median_networth",
                          "black_median_networth", "black_pct_of_white",
                          "black_white_gap_dollars", "hispanic_median_networth",
                          "hispanic_pct_of_white"])
        w.writeheader(); w.writerows(gap_rows)
    print(f"Wrote {gap_path} ({len(gap_rows)} years)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
