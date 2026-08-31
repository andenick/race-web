"""
L04 -- CPI Deflator Loader (support series for Panel 2: Income)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads the CPI-U (all urban consumers, all items, not seasonally adjusted,
index 1982-84=100) from FRED's public keyless CSV endpoint. P02 uses annual
averages of this series to deflate Census ACS median incomes to 2022 dollars.

Source: U.S. Bureau of Labor Statistics, Consumer Price Index for All Urban
        Consumers (CPI-U), via Federal Reserve Economic Data (FRED), CPIAUCSL
Endpoint: https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
License: Public domain (US Government)

OUTPUT (data/raw/fred/):
  cpi_monthly.csv  -- date, cpi (monthly index, 1982-84=100)

NOTE: CPIAUCSL as republished by FRED carries periodic historical revisions;
P02 uses annual averages, which are stable to rounding for deflation purposes.
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT = RAW / "fred"
OUT.mkdir(parents=True, exist_ok=True)

SID = "CPIAUCSL"
ENDPOINT = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SID}"
USER_AGENT = "race-anu-replication/1.0"


def main() -> int:
    print(f"Fetching {SID} from FRED fredgraph.csv ...")
    req = urllib.request.Request(ENDPOINT, headers={"User-Agent": USER_AGENT})
    try:
        raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"ERROR: FRED fetch failed: {repr(e)[:120]}", file=sys.stderr)
        return 1
    lines = raw.splitlines()
    header = lines[0].split(",")
    if header[:2] != ["observation_date", SID]:
        print(f"ERROR: unexpected header: {header[:3]}", file=sys.stderr)
        return 1
    out_path = OUT / "cpi_monthly.csv"
    n = 0
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "cpi"])
        for ln in lines[1:]:
            parts = ln.split(",")
            if len(parts) == 2 and parts[1] not in ("", "."):
                w.writerow(parts)
                n += 1
    print(f"Wrote {out_path} ({n} observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
