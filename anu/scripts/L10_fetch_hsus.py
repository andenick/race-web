"""
L10 -- HSUS Decennial Population Reference Loader (Panel 10)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Supplies the as-enumerated decennial-census population values used as a
cross-validation reference against the MeasuringWorth annual backbone (L11).

Source: U.S. Bureau of the Census, *Historical Statistics of the United States,
Colonial Times to 1970, Bicentennial Edition* (1975), Chapter A, Series A 1-8
(Area and Population of the United States).
Canonical URL: https://www.census.gov/library/publications/1975/compendia/hist_stats_colonial-1970.html
PDF: https://www.census.gov/library/publications/1975/compendia/hist_stats_colonial-1970/parts.html
License: U.S. Government work -- public domain.

METHOD NOTE:
  The five values below were tabulated from Series A 1-8 and verified against
  the internal-consistency identities the table itself reports (decennial
  increase and density). They are the census AS-ENUMERATED totals (not the
  MeasuringWorth interpolated series) and are carried ONLY for cross-checking;
  they are not the population backbone. All five are public-domain published
  figures and can be checked against the PDF above.

OUTPUT (data/raw/hsus/):
  hsus_a1_8_decennial.csv  -- year, total_population, confidence, source_note
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT = RAW / "hsus"
OUT.mkdir(parents=True, exist_ok=True)

# Series A 1-8 as-enumerated decennial totals (HIGH-confidence subset)
HSUS_A1_8 = {
    1790: 3_929_214,
    1820: 9_638_453,
    1830: 12_866_020,
    1850: 23_191_876,
    1880: 50_155_783,
}

NOTE = ("Census HSUS (1975) Series A 1-8 as-enumerated; verified against the "
        "table's internal-consistency identities")


def main() -> int:
    out_path = OUT / "hsus_a1_8_decennial.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["year", "total_population", "confidence", "source_note"])
        for y in sorted(HSUS_A1_8):
            w.writerow([y, HSUS_A1_8[y], "HIGH", NOTE])
    print(f"Wrote {out_path} ({len(HSUS_A1_8)} verified decennial values)")
    print("  (as-enumerated cross-check reference; backbone comes from L11)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
