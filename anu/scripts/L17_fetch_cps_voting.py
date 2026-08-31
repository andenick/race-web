"""
L17 -- CPS Voter Supplement Loader (Panel 17)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_17_POLITICAL

Pulls voter-turnout microdata from the Census Current Population Survey (CPS)
Voting and Registration Supplement via the Census API, then computes weighted
turnout-by-race for the major election years.

Source: U.S. Census Bureau, Current Population Survey, Voting and Registration
        Supplement (November of even-numbered years)
API: https://api.census.gov/data/{year}/cps/voting/nov
License: U.S. Government work -- public domain

ENDPOINT DISCOVERY NOTE:
  Prior sessions tried 4 endpoint variants and all failed. The WORKING format is:
    https://api.census.gov/data/{year}/cps/voting/nov?get=PES1,PTDTRACE,PWCMPWGT&for=state:*
  The key insight: CPS microdata requires `for=state:*` (NOT `for=us:1`, which
  returns "unknown/unsupported geography hierarchy"). The API returns individual-
  level microdata (~60-100K records per year) that must be aggregated.

CPS VARIABLES:
  PES1      = "Did you vote?"  (1=Yes, 2=No, -1=Not in Universe, -2=DK, -3=Refused)
  PES2      = "Registered to vote?"  (same codes)
  PTDTRACE  = race of respondent (1=White only, 2=Black only, 3=AIAN only,
              4=Asian only, 5=HP only, 6-26=multiracial combos)
  PWCMPWGT  = composited final weight (used for population-weighted turnout)

TURNOUT METHODOLOGY:
  Turnout % = weighted sum(PES1==1) / weighted sum(PES1 in [1,2])  per race group.
  The universe is citizens 18+ who answered Yes or No (PES1=-1 "Not in Universe"
  are non-citizens/under-18 and are EXCLUDED from the denominator).

CAVEAT -- CPS turnout overstates actual turnout:
  The CPS is a self-report survey; social desirability bias inflates turnout by
  ~5-10pp above actual ballot counts. The Census itself notes this. This panel
  reports CPS-REPORTED turnout (consistent across years/races), NOT validated
  turnout. The RACIAL GAP is the analytically meaningful metric, not the level.

COVERAGE:
  Biennial election years: 2010, 2012, 2014, 2016, 2018, 2020, 2022.
  (Presidential years: 2012, 2016, 2020; midterm: 2010, 2014, 2018, 2022.)

OUTPUT:
  data/raw/cps/cps_voter_turnout_by_race.csv  -- weighted turnout by race x year

KNOWN LIMITATIONS:
  - Self-report bias (see above); levels inflated, gaps are real.
  - PTDTRACE is "race of respondent" (observer-coded in some years), not
    self-identification; pre-2003 used a different race coding scheme.
  - Small sample sizes for AIAN and multiracial groups (wide CIs).
  - 2022 used a redesigned CPS weight system; slight break in series.
"""

from __future__ import annotations

import os

import csv
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = RAW / "cps"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html

# Election years to query (biennial even years 2010-2022)
YEARS = [2010, 2012, 2014, 2016, 2018, 2020, 2022]

# Race code -> label (collapse multiracial into "Other/Multiracial")
RACE_MAP = {
    "1": "White only",
    "2": "Black only",
    "3": "AIAN only",
    "4": "Asian only",
    "5": "HP only",
}


def _race_label(code: str) -> str:
    return RACE_MAP.get(code, "Other/Multiracial")


def _require_key() -> None:
    if not CENSUS_KEY:
        raise SystemExit(
            "CPS microdata endpoints require a Census API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")


def _query_year(year: int) -> list[dict] | None:
    """Query CPS voting supplement microdata for one year, return list of dicts."""
    url = (f"https://api.census.gov/data/{year}/cps/voting/nov"
           f"?get=PES1,PTDTRACE,PWCMPWGT&for=state:*{_key_param()}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
        raw = urllib.request.urlopen(req, timeout=60).read().decode()
        data = json.loads(raw)
        if len(data) < 2:
            return None
        hdr = data[0]
        i_pes1 = hdr.index("PES1")
        i_race = hdr.index("PTDTRACE")
        i_w = hdr.index("PWCMPWGT")
        records = []
        for row in data[1:]:
            try:
                w = float(row[i_w])
            except (ValueError, IndexError):
                continue
            if w <= 0:
                continue
            pes1 = row[i_pes1]
            race = row[i_race]
            records.append({"pes1": pes1, "race": race, "weight": w})
        return records
    except Exception as e:
        print(f"  [{year}] query failed: {repr(e)[:120]}", file=sys.stderr)
        return None


def _compute_turnout(records: list[dict]) -> list[dict]:
    """Aggregate microdata into weighted turnout by race."""
    agg = defaultdict(lambda: {"voted_w": 0.0, "eligible_w": 0.0, "n": 0})
    for rec in records:
        pes1 = rec["pes1"]
        if pes1 not in ("1", "2"):
            continue  # skip Not-in-Universe, DK, Refused
        label = _race_label(rec["race"])
        w = rec["weight"]
        agg[label]["eligible_w"] += w
        agg[label]["n"] += 1
        if pes1 == "1":
            agg[label]["voted_w"] += w
    rows = []
    for label in ["White only", "Black only", "Asian only",
                   "AIAN only", "HP only", "Other/Multiracial"]:
        d = agg.get(label)
        if d and d["eligible_w"] > 0:
            turnout = 100.0 * d["voted_w"] / d["eligible_w"]
            pop = d["eligible_w"] / 1e6
            rows.append({
                "race": label,
                "turnout_pct": round(turnout, 1),
                "eligible_population_millions": round(pop, 2),
                "sample_n": d["n"],
            })
    return rows


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    _require_key()
    print("=== L17: CPS Voter Supplement — turnout by race ===")
    all_rows = []
    for year in YEARS:
        print(f"  Querying {year}...", end=" ", flush=True)
        records = _query_year(year)
        if records is None:
            print("FAILED")
            continue
        turnout = _compute_turnout(records)
        for t in turnout:
            t["year"] = year
            all_rows.append(t)
        white = next((t for t in turnout if t["race"] == "White only"), None)
        black = next((t for t in turnout if t["race"] == "Black only"), None)
        w_t = white["turnout_pct"] if white else "?"
        b_t = black["turnout_pct"] if black else "?"
        print(f"{len(records):,} records | White {w_t}% | Black {b_t}%")
        time.sleep(0.5)

    if not all_rows:
        print("FATAL: no data retrieved", file=sys.stderr)
        return 1

    out_path = OUT_DIR / "cps_voter_turnout_by_race.csv"
    cols = ["year", "race", "turnout_pct", "eligible_population_millions", "sample_n"]
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        # sort by year then race
        all_rows.sort(key=lambda r: (r["year"], r["race"]))
        w.writerows(all_rows)
    print(f"\nWrote {out_path} ({len(all_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
