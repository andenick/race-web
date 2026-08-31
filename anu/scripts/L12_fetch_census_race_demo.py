"""
L12 -- Census ACS Race Demographics Loader (Panel 10)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_10_DEMOGRAPHICS

Pulls clean, authoritative race/ethnicity population counts for the United States
from the Census Bureau ACS (American Community Survey) API.

Source: U.S. Census Bureau, American Community Survey, 1-Year Estimates
        Table B02001 (Race) and B03002 (Hispanic or Latino Origin by Race)
API: https://api.census.gov/data/{year}/acs/acs1
License: U.S. Government work -- public domain

Census API key: set CENSUS_API_KEY (free signup: https://api.census.gov/data/key_signup.html).
  Note: free tier is rate-limited (~500 req/day); this loader makes <= 2 calls/year.

COVERAGE:
  ACS 1-Year is available 2005-2019, 2021, 2022 (the 2020 1-year was cancelled
  due to COVID-19 -- documented gap, not filled with synthetic data).

RACE-CATEGORY CONVENTION (Census B02001 "alone" universe):
  White, Black/AA, AIAN, Asian, NHPI, Some Other, Two or More Races
  Hispanic is a SEPARATE ethnicity question (B03002); reported as a cross-tab,
  NOT merged into race -- per DuBois race-category-harmonization rule (DPR §5.2).

OUTPUT:
  data/raw/census/acs_race_us.csv         -- B02001 race counts, US, 2005-2022
  data/raw/census/acs_hispanic_us.csv     -- B03002 Hispanic cross-tab, US, 2005-2022

KNOWN LIMITATIONS:
  - ACS 1-year excludes small geographies; national US totals are reliable.
  - 2020 gap (no ACS 1-year) -- left as NaN, documented in notes, NOT imputed.
  - Race "alone" excludes multiracial (captured separately in "Two or more races").
  - ACS coverage: ACS is a survey; decennial census (every 10 yrs) is the
    enumeration ground truth. For pre-2005, see HSUS / MeasuringWorth (L10).
"""

from __future__ import annotations

import os

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

# -- Paths ----------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
INPUT_CENSUS = RAW / "census"
INPUT_CENSUS.mkdir(parents=True, exist_ok=True)

# Census API key (free signup: https://api.census.gov/data/key_signup.html)
CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html

# B02001 (Race) variables -- "alone" categories + total + two-or-more
B02001 = {
    "B02001_001E": "total",
    "B02001_002E": "white_alone",
    "B02001_003E": "black_aa_alone",
    "B02001_004E": "aian_alone",
    "B02001_005E": "asian_alone",
    "B02001_006E": "nhpi_alone",
    "B02001_007E": "some_other_race_alone",
    "B02001_008E": "two_or_more_races",
}

# B03002 (Hispanic or Latino by Race) -- total + Hispanic + not-Hispanic white
B03002 = {
    "B03002_001E": "total",
    "B03002_012E": "hispanic_total",
    "B03002_003E": "not_hispanic_white_alone",
}

# ACS 1-year available years (2020 cancelled)
ACS1_YEARS = list(range(2005, 2020)) + [2021, 2022]


def _query(year: int, variables: dict) -> dict | None:
    """Query Census ACS 1-year for US totals. Returns {varname: value} or None."""
    codes = list(variables.keys())
    get_clause = ",".join(["NAME"] + codes)
    url = (f"https://api.census.gov/data/{year}/acs/acs1"
           f"?get={get_clause}&for=us:1{_key_param()}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
        raw = urllib.request.urlopen(req, timeout=30).read().decode()
        data = json.loads(raw)
        if len(data) < 2:
            return None
        header, row = data[0], data[1]
        out = {}
        for code, name in variables.items():
            idx = header.index(code)
            val = row[idx]
            out[name] = int(val) if val not in (None, "", "-") else None
        return out
    except Exception as e:
        print(f"  [{year}] query failed: {repr(e)[:120]}", file=sys.stderr)
        return None


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    print(f"Pulling ACS 1-year race data, US, years {ACS1_YEARS[0]}-{ACS1_YEARS[-1]}...")

    race_rows = []
    hisp_rows = []
    for y in ACS1_YEARS:
        r = _query(y, B02001)
        h = _query(y, B03002)
        if r:
            r_rec = {"year": y, **r}
            # compute shares
            tot = r.get("total")
            if tot:
                for cat in ["white_alone", "black_aa_alone", "aian_alone",
                            "asian_alone", "nhpi_alone", "some_other_race_alone",
                            "two_or_more_races"]:
                    v = r.get(cat)
                    r_rec[cat + "_pct"] = round(100 * v / tot, 2) if v is not None else None
            race_rows.append(r_rec)
            print(f"  {y}: total={tot:,}  black={r.get('black_aa_alone'):,}")
        else:
            race_rows.append({"year": y, "note": "ACS1_unavailable"})
        if h:
            hisp_rows.append({"year": y, **h})
        time.sleep(0.3)  # be polite to the API

    # write race CSV
    race_cols = ["year", "total", "white_alone", "black_aa_alone", "aian_alone",
                 "asian_alone", "nhpi_alone", "some_other_race_alone",
                 "two_or_more_races",
                 "white_alone_pct", "black_aa_alone_pct", "aian_alone_pct",
                 "asian_alone_pct", "nhpi_alone_pct", "some_other_race_alone_pct",
                 "two_or_more_races_pct"]
    race_path = INPUT_CENSUS / "acs_race_us.csv"
    with race_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=race_cols, extrasaction="ignore")
        w.writeheader()
        for rec in race_rows:
            w.writerow(rec)

    # write Hispanic CSV
    hisp_cols = ["year", "total", "hispanic_total", "not_hispanic_white_alone"]
    hisp_path = INPUT_CENSUS / "acs_hispanic_us.csv"
    with hisp_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=hisp_cols, extrasaction="ignore")
        w.writeheader()
        for rec in hisp_rows:
            tot = rec.get("total")
            htot = rec.get("hispanic_total")
            rec["hispanic_pct"] = round(100 * htot / tot, 2) if (tot and htot) else None
            w.writerow(rec)

    print(f"\nWrote {race_path} ({len(race_rows)} years)")
    print(f"Wrote {hisp_path} ({len(hisp_rows)} years)")
    ok = sum(1 for r in race_rows if r.get("total"))
    print(f"  successful years: {ok}/{len(ACS1_YEARS)}  (2020 = ACS1 cancelled, expected gap)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
