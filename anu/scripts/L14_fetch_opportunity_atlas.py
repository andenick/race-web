"""
L14 -- Opportunity Atlas National Mobility Loader (Panel 11)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads Table 5 of the Opportunity Atlas: national-level outcomes by birth
cohort, parental income percentile, race, and gender (kfr = kid family income
rank). 15 cohorts, 1978-1992.

Source: Opportunity Insights / Opportunity Atlas, Table 5
        (Chetty, Hendren, Jones, Porter 2018, QJE 133(2))
Download: https://www2.census.gov/ces/opportunity/national_estimates_by_cohort_primary_outcomes.csv
Data portal: https://opportunityinsights.org/data/
Census landing page: https://www.census.gov/programs-surveys/ces/data/public-use-data/opportunity-atlas-data-tables.html
License: Public domain (US Census Bureau)

OUTPUT (data/raw/opportunity/):
  table_5.csv  -- the national cohort x race x parent-percentile table
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = RAW / "opportunity"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www2.census.gov/ces/opportunity/national_estimates_by_cohort_primary_outcomes.csv"
DEST = OUT_DIR / "table_5.csv"
USER_AGENT = "race-anu-replication/1.0"


def main() -> int:
    if DEST.exists() and DEST.stat().st_size > 10_000:
        print(f"{DEST.name} already present, skipping")
        return 0
    print(f"Downloading Opportunity Atlas Table 5 from www2.census.gov ...")
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    try:
        DEST.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    except Exception as e:
        print(f"ERROR: download failed: {repr(e)[:120]}\n"
              "  Fallback: download Table 5 manually from\n"
              "  https://www.census.gov/programs-surveys/ces/data/public-use-data/opportunity-atlas-data-tables.html",
              file=sys.stderr)
        return 1
    head = DEST.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    if not head.startswith("cohort,kfr_"):
        print(f"WARNING: unexpected header: {head[:80]}", file=sys.stderr)
    print(f"Wrote {DEST} ({DEST.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
