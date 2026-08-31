"""
L18 -- IRS SOI Tax Loader + ACS Income-by-Race for Imputation (Panel 18)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_18_TAXATION

Downloads two sources for the tax-by-imputed-race panel:

1. IRS Statistics of Income (SOI) Table 1.4 — All Returns by Size of AGI
   https://www.irs.gov/pub/irs-soi/21in14ar.xls  (Tax Year 2021)
   Provides: number of returns, AGI amount, taxable income, income tax before
   credits — all by AGI bracket. NO KEY NEEDED (public download).
   License: U.S. Government work — public domain.

2. Census ACS B19001A/B — Household income distribution by race (White/Black)
   https://api.census.gov/data/2022/acs/acs1
   Provides: household counts by income bracket, separately for White alone and
   Black alone. Used for the race IMPUTATION (see P18 processor).

RACE IMPUTATION (MANDATORY CAVEAT):
  The IRS does NOT collect race on tax returns. This panel IMPUTES race using
  Census ACS income distributions: for each AGI bracket, the racial composition
  of households is estimated from ACS B19001A/B, then applied to the IRS tax
  amounts. This is a standard demographic imputation (used by Tax Policy Center,
  ITEP, etc.) but it is an APPROXIMATION, not an observation. Key limitations:
    - ACS household income != IRS AGI (different universes, definitions)
    - Households != tax returns (filing units differ)
    - Within-bracket racial composition is assumed uniform (no interaction)
  Every imputed value is flagged. The IRS SOI data itself is REAL; only the
  race attribution is imputed.

OUTPUT:
  data/raw/irs/soi_table14_2021.csv  -- IRS SOI tax by AGI bracket (real)
  data/raw/census/acs_income_dist_by_race.csv  -- ACS B19001A/B by bracket (real)
"""

from __future__ import annotations

import os

import csv
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_SOI = RAW / "irs"
OUT_CENSUS = RAW / "census"
OUT_SOI.mkdir(parents=True, exist_ok=True)
OUT_CENSUS.mkdir(parents=True, exist_ok=True)

CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html

# IRS SOI Table 1.4 column indices (discovered by parsing the .xls)
SOI_COLS = {
    0: "agi_bracket",
    1: "n_returns",
    2: "agi_amount",
    131: "n_taxable_income",
    132: "taxable_income_amount",
    137: "n_income_tax",
    138: "income_tax_amount",
}


def _download_soi() -> list[dict]:
    """Download and parse IRS SOI Table 1.4 from the .xls file."""
    import pandas as pd

    xls_path = OUT_SOI / "21in14ar.xls"
    if not xls_path.exists():
        url = "https://www.irs.gov/pub/irs-soi/21in14ar.xls"
        print(f"  Downloading IRS SOI from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        xls_path.write_bytes(urllib.request.urlopen(req, timeout=60).read())

    df = pd.read_excel(xls_path, header=None)
    rows = []
    # AGI bracket rows are 8-27 (All returns + brackets + Taxable returns)
    for i in range(8, 28):
        bracket = str(df.iloc[i, 0]).strip()
        if not bracket or bracket == "nan":
            continue
        rec = {"agi_bracket": bracket}
        for col, name in SOI_COLS.items():
            if name == "agi_bracket":
                continue
            val = df.iloc[i, col]
            rec[name] = int(val) if pd.notna(val) else 0
        rows.append(rec)
    return rows


def _query_acs_income_dist() -> dict[str, list]:
    """Pull ACS B19001A (White) and B19001B (Black) household income distribution."""
    results = {"white": [], "black": []}
    for suffix, race_key in [("A", "white"), ("B", "black")]:
        # B19001{suffix}: 16 income brackets (_001E total, _002E through _017E brackets)
        vars_list = ",".join([f"B19001{suffix}_{i:03d}E" for i in range(1, 18)])
        url = (f"https://api.census.gov/data/2022/acs/acs1"
               f"?get={vars_list}&for=us:1{_key_param()}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
            raw = urllib.request.urlopen(req, timeout=30).read().decode()
            data = json.loads(raw)
            header = data[0]
            row = data[1]
            for i in range(2, 18):
                results[race_key].append({
                    "bracket_var": f"B19001{suffix}_{i:03d}E",
                    "households": int(row[header.index(f"B19001{suffix}_{i:03d}E")]),
                })
        except Exception as e:
            print(f"  ACS B19001{suffix} failed: {repr(e)[:100]}", file=sys.stderr)
    return results


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    print("=== L18: IRS SOI + ACS income-by-race ===")

    # --- IRS SOI ---
    print("  Parsing IRS SOI Table 1.4...")
    soi_rows = _download_soi()
    soi_path = OUT_SOI / "soi_table14_2021.csv"
    soi_cols = ["agi_bracket", "n_returns", "agi_amount",
                "n_taxable_income", "taxable_income_amount",
                "n_income_tax", "income_tax_amount"]
    with soi_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=soi_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(soi_rows)
    print(f"  Wrote {soi_path} ({len(soi_rows)} brackets)")
    # sanity
    total_row = soi_rows[0]
    total_tax_t = total_row["income_tax_amount"] / 1e9  # thousands -> trillions
    total_agi_t = total_row["agi_amount"] / 1e9
    print(f"    Total: {total_row['n_returns']:,} returns, "
          f"AGI ${total_agi_t:.1f}T, tax ${total_tax_t:.2f}T "
          f"({100*total_tax_t/total_agi_t:.1f}% eff rate)")

    # --- ACS income distribution by race ---
    print("  Pulling ACS B19001A/B income distributions...")
    acs = _query_acs_income_dist()
    if acs["white"] and acs["black"]:
        # Map bracket indices to labels
        BRACKET_LABELS = [
            "<$10K", "$10-15K", "$15-20K", "$20-25K", "$25-30K", "$30-35K",
            "$35-40K", "$40-45K", "$45-50K", "$50-60K", "$60-75K", "$75-100K",
            "$100-125K", "$125-150K", "$150-200K", "$200K+"
        ]
        acs_path = OUT_CENSUS / "acs_income_dist_by_race.csv"
        with acs_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["bracket_label", "white_households", "black_households"])
            for i, label in enumerate(BRACKET_LABELS):
                wh = acs["white"][i]["households"] if i < len(acs["white"]) else 0
                bl = acs["black"][i]["households"] if i < len(acs["black"]) else 0
                w.writerow([label, wh, bl])
        print(f"  Wrote {acs_path} ({len(BRACKET_LABELS)} brackets)")
        w_total = sum(r["households"] for r in acs["white"])
        b_total = sum(r["households"] for r in acs["black"])
        print(f"    White households: {w_total:,} | Black households: {b_total:,}")
    else:
        print("  WARNING: ACS data incomplete", file=sys.stderr)

    print("\nL18 complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
