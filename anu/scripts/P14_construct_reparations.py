"""
P14 -- Reparations Comparison Processor (Panel 14)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Assembles a curated comparison of reparations estimates from distinct
methodological approaches, positioning the SCF-static counterfactual (P31)
alongside the major published estimates.

This is a CURATED panel -- no API. Every figure is a real, published number
with a full citation. The methodologies are fundamentally different questions:

  A. STATIC WEALTH-GAP (this project, P31):
     "What dollar amount closes today's observed Black-White wealth gap?"
     Computed from Fed SCF 2022 microdata: median/mean gap x Black households.
     Source: data/processed/reparations_counterfactual.csv (P31 output)

  B. NATIONAL WEALTH-GAP (Darity & Mullen 2020):
     "What is the federal cost of eliminating the Black-White wealth disparity?"
     ~$10-12 trillion. Uses per-capita Black-White wealth gap x eligible population.
     Source: Darity & Mullen, 'From Here to Equality' (2020); Brookings (2023).
     https://www.brookings.edu/articles/black-reparations-and-the-racial-wealth-gap/

  C. HISTORICAL-COMPOUNDING (Craemer et al. 2020):
     "What is the cumulative cost of slavery + discrimination, compounded?"
     Slavery-era: ~$12-13T (price-based, Marketti method).
     Wage-based at 3% interest: ~$18.6T.
     Source: Craemer, Smith, Harrison, Logan, Bellamy, Darity (2020), Review of
     Black Political Economy; also Darity & Mullen, JEP 36(2), 2022.
     https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.36.2.99

  D. PER-HARM METHODOLOGY (California Reparations Task Force, AB 3121, 2023):
     State-level, per-year-of-residency payments by harm category. Did NOT
     publish a single total; POLITICO reported the maximum could exceed $1.2M
     per eligible lifelong California resident.
     Source: CA DOJ / AB 3121 final report (June 2023); POLITICO (Aug 2023).
     https://oag.ca.gov/ab3121/report

CA TASK FORCE PER-YEAR AMOUNTS (from POLITICO reporting on Ch. 17):
  - Health disparities (1850-present):     $13,600/year
  - Mass incarceration/over-policing (1971-present): $2,400/year
  - Housing discrimination/redlining (1933-1977):    $3,000/year
  - Business devaluation (1850-present):   $77,000 one-time
  - Eminent domain / unjust takings:        no dollar estimate (2 methods proposed)
  Eligibility: descendants of enslaved persons or free Black persons in US before 1900.
  Max per-person framing: >$1.2M (lifelong CA resident).

OUTPUT (data/processed/):
  reparations_comparison.csv        -- method comparison
  reparations_ca_taskforce_by_harm.csv -- CA per-harm breakdown

INTEGRITY: this is a comparison of PUBLISHED ESTIMATES and a computed
counterfactual, NOT a policy prescription. Each figure is labeled with its
methodology and source. No causal or normative claims.
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

OUT = PROC
T31_CSV = PROC / "reparations_counterfactual.csv"


def _load_t31() -> dict[str, float]:
    """Read the P31 SCF-static counterfactual output."""
    vals = {}
    if T31_CSV.exists():
        with T31_CSV.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                try:
                    vals[r["metric"]] = float(r["value"])
                except (ValueError, KeyError):
                    pass
    return vals


def main() -> int:
    t31 = _load_t31()
    if not t31:
        print("WARNING: P31 counterfactual CSV not found; using documented figures",
              flush=True)
        median_t = 3.786
        mean_t = 19.009
    else:
        median_t = t31.get("aggregate_median_shortfall_trillion_usd", 3.786)
        mean_t = t31.get("aggregate_mean_shortfall_trillion_usd", 19.009)

    # --- Part 1: National-level method comparison ---
    comparison = [
        {
            "method": "DuBois SCF-static (P31): median gap x Black households",
            "scope": "national (US)",
            "amount_low_trillion_usd": round(median_t, 2),
            "amount_high_trillion_usd": round(mean_t, 2),
            "base_year": 2022,
            "source": "Fed SCF 2022 microdata (this project, P31)",
            "url": "scripts/P31_counterfactual_reparations.py (this package)",
            "note": ("closes TODAY's gap; median=$%.1fT (typical hh), "
                     "mean=$%.1fT (tail-inflated)") % (median_t, mean_t),
        },
        {
            "method": "Darity & Mullen (2020): per-capita wealth gap x eligible pop",
            "scope": "national (US)",
            "amount_low_trillion_usd": 10.0,
            "amount_high_trillion_usd": 12.0,
            "base_year": 2019,
            "source": "Darity & Mullen, 'From Here to Equality' (2020); Brookings (2023)",
            "url": "https://www.brookings.edu/articles/black-reparations-and-the-racial-wealth-gap/",
            "note": "targets full elimination of Black-White per-capita wealth gap",
        },
        {
            "method": "Craemer et al. (2020): slavery-era, Marketti price-based",
            "scope": "national (US)",
            "amount_low_trillion_usd": 12.0,
            "amount_high_trillion_usd": 13.0,
            "base_year": 2018,
            "source": "Craemer et al. (2020), Rev. Black Pol. Economy",
            "url": "https://journals.sagepub.com/doi/10.1177/0034644620926516",
            "note": "price-based valuation of enslaved labor; Darity land-method similar",
        },
        {
            "method": "Craemer et al. (2020): wage-based, compounded at 3%",
            "scope": "national (US)",
            "amount_low_trillion_usd": 18.6,
            "amount_high_trillion_usd": 18.6,
            "base_year": 2018,
            "source": "Craemer et al. (2020); Darity & Mullen JEP 36(2) 2022",
            "url": "https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.36.2.99",
            "note": "unpaid wages from slavery compounded at 3% interest; higher bound",
        },
    ]

    # --- Part 2: CA Task Force per-harm breakdown ---
    ca_harms = [
        {
            "harm_category": "Health disparities",
            "period": "1850-present",
            "per_year_usd": 13600,
            "basis": ("Black vs White non-Hispanic life-expectancy gap in CA; "
                      "estimates cumulative health discrimination"),
            "source": "CA AB 3121 Task Force, Ch. 17 (2023); POLITICO (Aug 2023)",
            "url": "https://oag.ca.gov/ab3121/report",
        },
        {
            "harm_category": "Mass incarceration / over-policing",
            "period": "1971-present",
            "per_year_usd": 2400,
            "basis": ("lost wages (avg sentence length) + lost freedom (benchmarked to "
                      "Japanese-American internment reparations)"),
            "source": "CA AB 3121 Task Force, Ch. 17 (2023); POLITICO (Aug 2023)",
            "url": "https://oag.ca.gov/ab3121/report",
        },
        {
            "harm_category": "Housing discrimination / redlining",
            "period": "1933-1977",
            "per_year_usd": 3000,
            "basis": ("homeownership gap attributable to redlining, FHA discrimination, "
                      "zoning; 1933-77 federal redlining era"),
            "source": "CA AB 3121 Task Force, Ch. 17 (2023); POLITICO (Aug 2023)",
            "url": "https://oag.ca.gov/ab3121/report",
        },
        {
            "harm_category": "Business devaluation",
            "period": "1850-present",
            "per_year_usd": 0,
            "basis": ("$77,000 one-time per person; based on ~59,951 'missing' "
                      "Black-owned firms in CA vs expected absent discrimination"),
            "source": "CA AB 3121 Task Force, Ch. 17 (2023); POLITICO (Aug 2023)",
            "url": "https://oag.ca.gov/ab3121/report",
        },
        {
            "harm_category": "Unjust property takings (eminent domain)",
            "period": "1850-present",
            "per_year_usd": 0,
            "basis": ("no dollar estimate; two methods proposed (appreciation or "
                      "current-value of seized property). e.g. I-10, I-105 construction"),
            "source": "CA AB 3121 Task Force, Ch. 17 (2023); POLITICO (Aug 2023)",
            "url": "https://oag.ca.gov/ab3121/report",
        },
    ]

    # Write comparison CSV
    comp_cols = ["method", "scope", "amount_low_trillion_usd",
                 "amount_high_trillion_usd", "base_year", "source", "url", "note"]
    comp_path = OUT / "reparations_comparison.csv"
    with comp_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=comp_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(comparison)
    print(f"Wrote {comp_path} ({len(comparison)} methods)")

    # Write CA per-harm CSV
    ca_cols = ["harm_category", "period", "per_year_usd", "basis", "source", "url"]
    ca_path = OUT / "reparations_ca_taskforce_by_harm.csv"
    with ca_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ca_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(ca_harms)
    print(f"Wrote {ca_path} ({len(ca_harms)} harm categories)")

    # --- Summary ---
    print(f"\n--- Panel 14 Reparations Comparison Summary ---")
    print(f"{'Method':60} {'$T low':>7} {'$T high':>7}")
    for r in comparison:
        print(f"{r['method'][:60]:60} {r['amount_low_trillion_usd']:>7.1f} "
              f"{r['amount_high_trillion_usd']:>7.1f}")
    print(f"\nCA Task Force per-harm (annual / one-time):")
    for h in ca_harms:
        amt = f"${h['per_year_usd']:,}/yr" if h['per_year_usd'] else "no $ estimate"
        print(f"  {h['harm_category']:45} {h['period']:14} {amt}")
    print(f"\nMax per eligible lifelong CA resident: >$1.2M (POLITICO, 2023)")
    print(f"Eligibility: descendants of enslaved persons or free Black persons in")
    print(f"  the US before 1900 (lineage-based, per AB 3121)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
