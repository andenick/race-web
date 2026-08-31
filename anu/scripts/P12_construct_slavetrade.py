"""
P12 -- Trans-Atlantic Slave Trade Processor (Panel 12)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Builds the forced-migration series from the SlaveVoyages Trans-Atlantic Slave
Trade Database (2019 release), fetched by L12b_fetch_slavevoyages.py.

Source: SlaveVoyages.org, Trans-Atlantic Slave Trade Database (tastdb-exp-2019)
License: CC-BY (SlaveVoyages)

OUTPUT (data/processed/):
  slavetrade_annual.csv    -- annual embarked/disembarked/mortality, total + NA
  slavetrade_by_region.csv -- cumulative disembarked by arrival region
  slavetrade_summary.csv   -- headline totals
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

SRC = RAW / "slavevoyages" / "tastdb-exp-2019.csv"
OUT = PROC

REGION_NAMES = {
    1: "Europe", 2: "Mainland North America", 3: "British Caribbean",
    4: "French Americas", 5: "Spanish Americas", 6: "Dutch/Danish/Other Caribbean",
    7: "Brazil", 8: "Africa (intra-American)",
}


def _region_group(regarr):
    """Map hierarchical REGARR code to broad region number 1-8."""
    if pd.isna(regarr):
        return None
    r = int(regarr)
    if 10000 <= r < 20000: return 1
    if 20000 <= r < 30000: return 2  # Mainland North America
    if 30000 <= r < 40000: return 3  # Caribbean (British/French/Dutch)
    if 40000 <= r < 50000: return 5  # Spanish Americas
    if 50000 <= r < 60000: return 7  # Brazil
    if 60000 <= r < 70000: return 8  # Africa
    if 80000 <= r < 90000: return 6
    return None


def main() -> int:
    if not SRC.exists():
        print(f"FATAL: {SRC} missing -- run L12b_fetch_slavevoyages.py first",
              flush=True)
        return 1

    df = pd.read_csv(SRC, encoding="latin-1",
                     usecols=["VOYAGEID", "YEARAM", "SLAXIMP", "SLAMIMP", "REGARR"])
    df = df.dropna(subset=["YEARAM"])
    df["year"] = df["YEARAM"].astype(int)
    df["region"] = df["REGARR"].apply(_region_group)
    df["embarked"] = df["SLAXIMP"].fillna(0)
    df["disembarked"] = df["SLAMIMP"].fillna(0)

    # --- annual series (total + North America) ---
    annual = df.groupby("year").agg(
        voyages=("VOYAGEID", "count"),
        embarked_total=("embarked", "sum"),
        disembarked_total=("disembarked", "sum"),
    ).reset_index()
    na = df[df["region"] == 2].groupby("year").agg(
        disembarked_na=("disembarked", "sum"),
        voyages_na=("VOYAGEID", "count"),
    ).reset_index()
    annual = annual.merge(na, on="year", how="left").fillna(0)
    annual["disembarked_na"] = annual["disembarked_na"].astype(int)
    annual["voyages_na"] = annual["voyages_na"].astype(int)
    # mortality = embarked - disembarked (middle passage deaths)
    annual["mortality_total"] = (annual["embarked_total"] - annual["disembarked_total"]).clip(lower=0)
    annual["mortality_rate_pct"] = annual.apply(
        lambda r: round(100 * r["mortality_total"] / r["embarked_total"], 2)
        if r["embarked_total"] > 0 else None, axis=1)

    p = OUT / "slavetrade_annual.csv"
    annual.to_csv(p, index=False)
    print(f"Wrote {p} ({len(annual)} years, {annual['year'].min()}-{annual['year'].max()})")

    # --- by region (cumulative disembarked) ---
    byreg = df.dropna(subset=["region"]).groupby("region").agg(
        voyages=("VOYAGEID", "count"),
        embarked=("embarked", "sum"),
        disembarked=("disembarked", "sum"),
    ).reset_index()
    byreg["region_name"] = byreg["region"].map(REGION_NAMES)
    byreg = byreg.sort_values("disembarked", ascending=False)
    p2 = OUT / "slavetrade_by_region.csv"
    byreg[["region", "region_name", "voyages", "embarked", "disembarked"]].to_csv(p2, index=False)
    print(f"Wrote {p2}")

    # --- summary ---
    total_emb = int(df["embarked"].sum())
    total_dis = int(df["disembarked"].sum())
    total_na = int(df[df["region"] == 2]["disembarked"].sum())
    overall_mort = round(100 * (total_emb - total_dis) / total_emb, 1) if total_emb else None
    p3 = OUT / "slavetrade_summary.csv"
    summary = pd.DataFrame([
        {"metric": "total_voyages", "value": int(len(df))},
        {"metric": "total_embarked_imputed", "value": total_emb},
        {"metric": "total_disembarked_imputed", "value": total_dis},
        {"metric": "overall_middle_passage_mortality_pct", "value": overall_mort},
        {"metric": "mainland_north_america_disembarked", "value": total_na},
        {"metric": "year_range", "value": f"{int(df['year'].min())}-{int(df['year'].max())}"},
    ])
    summary.to_csv(p3, index=False)
    print(f"Wrote {p3}")
    print(f"\nSummary: {len(df):,} voyages; {total_emb:,} embarked; "
          f"{total_dis:,} disembarked; NA mainland {total_na:,}; mortality {overall_mort}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
