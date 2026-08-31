"""
P18 -- Taxation by Race Processor (Panel 18, IMPUTED)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_18_TAXATION

Computes federal income-tax burden by imputed race from IRS SOI data + ACS
income distributions. The IRS data is REAL; the race attribution is IMPUTED.

SOURCES:
  1. IRS SOI Table 1.4 (2021): tax returns, AGI, taxable income, income tax
     by AGI bracket. Real data, public domain.
     https://www.irs.gov/pub/irs-soi/21in14ar.xls
  2. Census ACS B19001A/B (2022): household income distribution by race.
     Used to estimate the racial composition of each AGI bracket. Real data.
     https://api.census.gov/data/2022/acs/acs1

IMPUTATION METHOD (transparent, standard public-finance approach):
  For each IRS AGI bracket, we estimate the Black and White share of filers
  using ACS household income distributions. Then:
    imputed_black_tax[bracket] = black_share[bracket] x total_tax[bracket]
    imputed_white_tax[bracket] = white_share[bracket] x total_tax[bracket]
  We aggregate across brackets to get total imputed tax by race, then compute
  the effective rate (tax / AGI) by imputed race.

  AGI-bracket-to-ACS-bracket mapping is approximate (different universes:
  tax returns vs households; AGI vs household income). Within-bracket racial
  composition is assumed uniform. This is a first-order approximation.

INTEGRITY:
  - The IRS data is OBSERVED (real counts and dollar amounts).
  - The race attribution is IMPUTED (flagged in every output row).
  - No causal claim. The effective rate by imputed race reflects the
    PROGRESSIVE tax system's interaction with the racial income distribution,
    NOT differential treatment of races by the tax code.

OUTPUT (data/processed/):
  taxation_by_agi_bracket.csv       -- real IRS data by bracket (no race)
  taxation_imputed_by_race.csv      -- imputed tax by race (flagged)
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
INP_SOI = RAW / "irs" / "soi_table14_2021.csv"
INP_ACS = RAW / "census" / "acs_income_dist_by_race.csv"
OUT = PROC

# Mapping: IRS AGI bracket label -> ACS bracket label(s)
# (Approximate; IRS AGI brackets and ACS household income brackets differ.)
IRS_TO_ACS = [
    ("No adjusted gross income", ["<$10K"]),
    ("$1 under $5,000", ["<$10K"]),
    ("$5,000 under $10,000", ["<$10K"]),
    ("$10,000 under $15,000", ["$10-15K"]),
    ("$15,000 under $20,000", ["$15-20K"]),
    ("$20,000 under $25,000", ["$20-25K"]),
    ("$25,000 under $30,000", ["$25-30K"]),
    ("$30,000 under $40,000", ["$30-35K", "$35-40K"]),
    ("$40,000 under $50,000", ["$40-45K", "$45-50K"]),
    ("$50,000 under $75,000", ["$50-60K", "$60-75K"]),
    ("$75,000 under $100,000", ["$75-100K"]),
    ("$100,000 under $200,000", ["$100-125K", "$125-150K", "$150-200K"]),
    ("$200,000 under $500,000", ["$200K+"]),
    ("$500,000 under $1,000,000", ["$200K+"]),
    ("$1,000,000 under $1,500,000", ["$200K+"]),
    ("$1,500,000 under $2,000,000", ["$200K+"]),
    ("$2,000,000 under $5,000,000", ["$200K+"]),
    ("$5,000,000 under $10,000,000", ["$200K+"]),
    ("$10,000,000 or more", ["$200K+"]),
]


def _load_acs() -> dict[str, dict]:
    """Load ACS income distribution; return {bracket_label: {white, black}}."""
    dist = {}
    with INP_ACS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            dist[r["bracket_label"]] = {
                "white": int(r["white_households"]),
                "black": int(r["black_households"]),
            }
    return dist


def _black_share(acs_labels: list[str], dist: dict) -> float:
    """Compute the Black share of households in the given ACS bracket(s)."""
    w = sum(dist[l]["white"] for l in acs_labels if l in dist)
    b = sum(dist[l]["black"] for l in acs_labels if l in dist)
    total = w + b
    return b / total if total > 0 else 0.0


def main() -> int:
    if not INP_SOI.exists() or not INP_ACS.exists():
        print("FATAL: IRS SOI or ACS input missing", flush=True)
        return 1

    # Load IRS SOI
    with INP_SOI.open(encoding="utf-8") as fh:
        soi = list(csv.DictReader(fh))
    # Convert to ints
    for r in soi:
        for k in ["n_returns", "agi_amount", "n_taxable_income",
                  "taxable_income_amount", "n_income_tax", "income_tax_amount"]:
            r[k] = int(r[k])

    acs_dist = _load_acs()

    # --- Part 1: real IRS data by bracket (no race) ---
    bracket_rows = []
    for r in soi:
        if "total" in r["agi_bracket"].lower() or "Taxable returns" in r["agi_bracket"]:
            continue  # skip summary rows for the per-bracket table
        agi = r["agi_amount"]
        tax = r["income_tax_amount"]
        eff_rate = 100 * tax / agi if agi > 0 else 0.0
        bracket_rows.append({
            "agi_bracket": r["agi_bracket"],
            "n_returns": r["n_returns"],
            "agi_amount_thousands": agi,
            "income_tax_thousands": tax,
            "effective_rate_pct": round(eff_rate, 2),
        })

    bcols = ["agi_bracket", "n_returns", "agi_amount_thousands",
             "income_tax_thousands", "effective_rate_pct"]
    bpath = OUT / "taxation_by_agi_bracket.csv"
    with bpath.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=bcols, extrasaction="ignore")
        w.writeheader()
        w.writerows(bracket_rows)
    print(f"Wrote {bpath} ({len(bracket_rows)} brackets)")

    # --- Part 2: imputed tax by race ---
    # For each IRS bracket, compute Black/White share from ACS, apply to tax
    imputed = {"black": {"agi": 0, "tax": 0, "returns": 0},
               "white": {"agi": 0, "tax": 0, "returns": 0}}
    imputed_detail = []
    for r in soi:
        bracket = r["agi_bracket"]
        if "total" in bracket.lower() or "Taxable returns" in bracket:
            continue
        # find ACS mapping
        mapping = None
        for irs_label, acs_labels in IRS_TO_ACS:
            if bracket.strip() == irs_label.strip():
                mapping = acs_labels
                break
        if mapping is None:
            continue
        b_share = _black_share(mapping, acs_dist)
        w_share = 1.0 - b_share  # ACS only has white + black; other races omitted

        agi = r["agi_amount"]
        tax = r["income_tax_amount"]
        returns = r["n_returns"]

        imputed["black"]["agi"] += agi * b_share
        imputed["black"]["tax"] += tax * b_share
        imputed["black"]["returns"] += returns * b_share
        imputed["white"]["agi"] += agi * w_share
        imputed["white"]["tax"] += tax * w_share
        imputed["white"]["returns"] += returns * w_share

        imputed_detail.append({
            "agi_bracket": bracket,
            "imputed_black_share_pct": round(100 * b_share, 1),
            "imputed_white_share_pct": round(100 * w_share, 1),
            "agi_thousands": agi,
            "income_tax_thousands": tax,
            "imputed_black_tax_thousands": int(tax * b_share),
            "imputed_white_tax_thousands": int(tax * w_share),
            "data_type": "IMPUTED",
        })

    # Aggregate by race
    race_rows = []
    for race in ["white", "black"]:
        d = imputed[race]
        agi = d["agi"]
        tax = d["tax"]
        eff = 100 * tax / agi if agi > 0 else 0
        race_rows.append({
            "imputed_race": race.capitalize(),
            "imputed_n_returns": int(d["returns"]),
            "imputed_agi_thousands": int(agi),
            "imputed_income_tax_thousands": int(tax),
            "imputed_effective_rate_pct": round(eff, 2),
            "imputed_avg_tax_per_return": int(tax / d["returns"]) if d["returns"] else 0,
            "imputed_avg_agi_per_return": int(agi / d["returns"]) if d["returns"] else 0,
            "data_type": "IMPUTED_RACE (IRS data real; race attribution imputed from ACS income dist)",
        })

    rcols = ["imputed_race", "imputed_n_returns", "imputed_agi_thousands",
             "imputed_income_tax_thousands", "imputed_effective_rate_pct",
             "imputed_avg_tax_per_return", "imputed_avg_agi_per_return",
             "data_type"]
    rpath = OUT / "taxation_imputed_by_race.csv"
    with rpath.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rcols, extrasaction="ignore")
        w.writeheader()
        w.writerows(race_rows)
    print(f"Wrote {rpath} ({len(race_rows)} imputed races)")

    # Detail file
    dcols = ["agi_bracket", "imputed_black_share_pct", "imputed_white_share_pct",
             "agi_thousands", "income_tax_thousands",
             "imputed_black_tax_thousands", "imputed_white_tax_thousands",
             "data_type"]
    dpath = OUT / "taxation_imputed_by_bracket.csv"
    with dpath.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=dcols, extrasaction="ignore")
        w.writeheader()
        w.writerows(imputed_detail)
    print(f"Wrote {dpath} ({len(imputed_detail)} brackets)")

    # --- Summary ---
    print(f"\n--- Panel 18 Taxation by Race (IMPUTED) Summary ---")
    print(f"{'Race':8} {'Returns(M)':>10} {'AGI($T)':>8} {'Tax($T)':>8} {'EffRate%':>8}")
    for r in race_rows:
        agi_t = r["imputed_agi_thousands"] / 1e9
        tax_t = r["imputed_income_tax_thousands"] / 1e9
        ret_m = r["imputed_n_returns"] / 1e6
        print(f"{r['imputed_race']:8} {ret_m:>10.1f} {agi_t:>8.2f} {tax_t:>8.2f} "
              f"{r['imputed_effective_rate_pct']:>8.1f}")
    w_eff = race_rows[0]["imputed_effective_rate_pct"]
    b_eff = race_rows[1]["imputed_effective_rate_pct"]
    print(f"\n  Imputed effective rate: White {w_eff}% vs Black {b_eff}%")
    print(f"  The rate difference reflects the PROGRESSIVE tax code interacting with")
    print(f"  the racial income distribution, NOT differential treatment of races.")
    print(f"\n  CAVEAT: Race is IMPUTED from ACS income distributions. The IRS does not")
    print(f"  collect race. AGI brackets mapped to ACS brackets approximately.")
    print(f"  Households != tax returns. Within-bracket race composition assumed uniform.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
