"""
L03 -- BLS Race Unemployment Loader (Panel 3)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads the canonical race-disaggregated unemployment-rate series from the
BLS Current Population Survey (CPS) via FRED's public keyless CSV endpoint
(fredgraph.csv). No API key is required.

Source: U.S. Bureau of Labor Statistics, Current Population Survey (CPS)
        via Federal Reserve Economic Data (FRED)
Endpoint: https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}
License: Public domain (US Government)

SERIES (monthly, seasonally adjusted, percent):
  LNS14000003  Unemployment Rate - White           (1954-01 onward)
  LNS14000006  Unemployment Rate - Black/AA        (1972-01 onward)
  LNS14000009  Unemployment Rate - Hispanic/Latino (1973-03 onward)
  LNS14032183  Unemployment Rate - Asian           (2000-07 onward)

These are THE series behind the "Black unemployment runs ~2x the white rate"
finding -- one of the most documented regularities in US labor economics.

OUTPUT (data/raw/fred/):
  unemployment_monthly.csv  -- long: date, series_id, race, value (monthly SA)

KNOWN LIMITATIONS:
  - Pre-1972 Black, pre-1973 Hispanic, pre-2000 Asian: not collected (BLS began
    race disaggregation later). Left absent, NOT back-imputed.
  - CPS is a survey; small-sample volatility in monthly race rates (esp. Asian).
    Annual averages (computed in P03) smooth this.
  - 1954-1971 White-only is the earliest continuous US unemployment series.
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

SERIES = {
    "LNS14000003": "White",
    "LNS14000006": "Black or African American",
    "LNS14000009": "Hispanic or Latino",
    "LNS14032183": "Asian",
}

ENDPOINT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
USER_AGENT = "race-anu-replication/1.0"


def _fetch(sid: str) -> list[tuple[str, str]]:
    url = ENDPOINT.format(sid=sid)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
    lines = raw.splitlines()
    header = lines[0].split(",")
    if header[:2] != ["observation_date", sid]:
        raise ValueError(f"unexpected fredgraph header for {sid}: {header[:3]}")
    obs = []
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) == 2 and parts[1] not in ("", "."):
            obs.append((parts[0], parts[1]))
    return obs


def main() -> int:
    out_path = OUT / "unemployment_monthly.csv"
    total = 0
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "series_id", "race", "value"])
        for sid, race in SERIES.items():
            try:
                obs = _fetch(sid)
            except Exception as e:
                print(f"  {sid} ({race}): FAILED {repr(e)[:100]}", file=sys.stderr)
                return 1
            for date, value in obs:
                w.writerow([date, sid, race, value])
            total += len(obs)
            print(f"  {sid} {race}: {len(obs)} obs  [{obs[0][0]} .. {obs[-1][0]}]")
    print(f"\nWrote {out_path} ({total} observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
