"""
M01 -- Data Dictionary Generator
Project: DuBois (Race, Stratification & Economic Disparities)

Introspects the data/processed/ CSV panels and emits a machine-readable
data_dictionary.csv (Anu Framework requirement) documenting every series:
filename, series_name, units, year_span, source, panel, notes.

OUTPUT: data/processed/data_dictionary.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROC
OUT = DATA_DIR / "data_dictionary.csv"

# Manual catalog of each panel's series (more accurate than blind introspection)
SERIES = [
    # Panel 10 - Demographics
    ("demographics_population.csv", "total_population", "persons", "1790-2024",
     "MeasuringWorth (Williamson)", "P10", "Annual total US population (backbone)"),
    ("demographics_population.csv", "hsus_as_enumerated", "persons", "1790,1820,1830,1850,1880",
     "HSUS bicentennial OCR (HIGH-conf subset)", "P10", "As-enumerated census, 5 yrs only (OCR-limited)"),
    ("demographics_population.csv", "black_aa_alone", "persons", "2005-2022",
     "Census ACS B02001_003E", "P10", "Black/AA alone (2020 gap: ACS1 cancelled)"),
    ("demographics_population.csv", "hispanic_total", "persons", "2005-2022",
     "Census ACS B03002_012E", "P10", "Hispanic (ethnicity, any race)"),
    ("demographics_race_shares.csv", "*_pct", "percent of total", "2005-2022",
     "Census ACS B02001/B03002", "P10", "Race population shares (sum to 100)"),
    ("demographics_crosscheck.csv", "agreement_pct", "percent", "1790,1820,1830,1850,1880",
     "derived (MW vs HSUS)", "P10", "Cross-source validation (avg 99.8%)"),

    # Panel 1 - Wealth
    ("wealth_by_race_timeseries.csv", "median_networth", "2022 USD", "1989-2022",
     "Fed SCF (12 waves)", "P1", "Weighted median net worth by race"),
    ("wealth_by_race_timeseries.csv", "mean_networth", "2022 USD", "1989-2022",
     "Fed SCF", "P1", "Weighted mean net worth by race"),
    # households_est is a POPULATION estimate, not a sample count: it is the sum of
    # the SCF weight WGT over all 5 implicates, which in these extracts already sums
    # to the household population (no /5). It was documented here 2026-07-31 after a
    # stale web export shipped the column 5x too low; the 2022 total in the notes is
    # the cross-surface assertion that guards against that regression recurring.
    ("wealth_by_race_timeseries.csv", "households_est", "households (weighted)", "1989-2022",
     "Fed SCF (12 waves)", "P1", "Sum of SCF WGT by race; 2022 total 131,306,387 (Census 2022: 131.2M)"),
    ("wealth_gap_timeseries.csv", "black_pct_of_white", "percent", "1989-2022",
     "derived (SCF)", "P1", "Black median wealth as % of White (HEADLINE)"),
    ("wealth_by_race_2022.csv", "median_*", "2022 USD", "2022",
     "Fed SCF 2022", "P1", "Asset composition by race (home/fin/debt)"),
    ("wealth_by_race_2022.csv", "households_est", "households (weighted)", "2022",
     "Fed SCF 2022", "P1", "Sum of SCF WGT by race; total 131,306,387 (Census 2022: 131.2M)"),

    # Panel 3 - Employment
    ("unemployment_annual.csv", "unemployment_rate", "percent (SA)", "1954-2025",
     "BLS CPS via FRED", "P3", "Annual avg unemployment by race"),
    ("unemployment_ratio.csv", "black_white_ratio", "ratio", "1972-2025",
     "derived (BLS CPS)", "P3", "Black/White unemployment ratio (HEADLINE ~2x)"),
    ("unemployment_ratio.csv", "black_white_gap_pp", "percentage points", "1972-2025",
     "derived (BLS CPS)", "P3", "Black minus White unemployment rate"),
    ("unemployment_recession_peaks.csv", "*_peak", "percent", "1973-2020",
     "BLS CPS + NBER", "P3", "Peak unemployment by race across 7 NBER recessions"),

    # Panel 2 - Income
    ("income_ratio.csv", "*_nominal", "current USD", "2005-2022",
     "Census ACS B19013", "P2", "Median household income by race (nominal)"),
    ("income_ratio.csv", "*_real_2022", "2022 USD", "2005-2022",
     "Census ACS B19013, CPIAUCSL-deflated", "P2", "Median HH income real (2022$)"),
    ("income_ratio.csv", "black_white_ratio", "ratio", "2005-2022",
     "derived (ACS)", "P2", "Black/White median income ratio (HEADLINE ~0.63)"),

    # Panel 4 - Poverty
    ("poverty_gap.csv", "*_poverty_rate", "percent", "2005-2022",
     "Census ACS B17001", "P4", "Poverty rate by race"),
    ("poverty_gap.csv", "black_white_poverty_ratio", "ratio", "2005-2022",
     "derived (ACS)", "P4", "Black/White poverty ratio (HEADLINE ~2.2x)"),
    ("poverty_gap.csv", "black_white_gap_pp", "percentage points", "2005-2022",
     "derived (ACS)", "P4", "Black minus White poverty rate"),

    # Panel 6 - Education
    ("education_attainment_gap.csv", "*_bachelors_pct", "percent of 25+", "2006-2022",
     "Census ACS C15002 race iterations", "P6", "Bachelor's+ attainment by race"),
    ("education_attainment_gap.csv", "black_white_ratio", "ratio", "2006-2022",
     "derived (ACS)", "P6", "Black/White bachelor's+ ratio (~0.63 ~= income ratio)"),
    ("education_attainment_gap.csv", "asian_white_gap_pp", "percentage points", "2006-2022",
     "derived (ACS)", "P6", "Asian exceeds White (positive = Asian > White)"),
]


def main() -> int:
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["panel", "filename", "series_name", "units", "year_span",
                    "source", "notes"])
        for fname, series, units, span, source, panel, notes in SERIES:
            w.writerow([panel, fname, series, units, span, source, notes])
    print(f"Wrote {OUT} ({len(SERIES)} series across 5 panels)")
    # panel summary
    from collections import Counter
    pc = Counter(s[5] for s in SERIES)
    for p, n in sorted(pc.items()):
        print(f"  {p}: {n} series")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
