"""
L02 -- Census ACS Income & Poverty by Race Loader (Panels 2 & 4)
Project: DuBois (Race, Stratification & Economic Disparities)
Panels: PANEL_02_INCOME, PANEL_04_POVERTY

Pulls median household income by race (ACS Table B19013) and poverty status by
race (ACS Table B17001) for the United States, via the Census ACS 1-Year API.

Source: U.S. Census Bureau, American Community Survey 1-Year Estimates
        B19013 (Median Household Income) + race iterations A/B/C/D/H/I
        B17001 (Poverty Status by Sex by Age) + race iterations A/B/C/D/H/I
API: https://api.census.gov/data/{year}/acs/acs1
License: Public domain (US Government)

RACE ITERATION SUFFIXES (Census):
  (base) = all races   A = White alone   B = Black/AA alone   C = AIAN alone
  D = Asian alone      E = NHPI alone     H = White alone NOT Hispanic
  I = Hispanic/Latino

INCOME VARIABLES (B19013_xxx_001E = median household income):
  total, White, Black, AIAN, Asian, White-nH, Hispanic

POVERTY VARIABLES (per race iteration):
  _001E = total population for whom poverty determined
  _002E = population below poverty
  poverty_rate = _002E / _001E

COVERAGE: ACS 1-Year 2005-2019, 2021, 2022 (2020 cancelled, COVID -- documented gap)

OUTPUT (data/raw/census/):
  income_by_race.csv   -- median HH income by race, US, 2005-2022
  poverty_by_race.csv  -- poverty count + rate by race, US, 2005-2022

KNOWN LIMITATIONS:
  - Median income is a dollar figure (current dollars, not CPI-adjusted);
    P02 will deflate to real terms using CPI.
  - ACS race "alone" universe; Hispanic is separate ethnicity (H vs I suffixes).
  - 2020 gap (no ACS 1-year) left null, not imputed.
"""

from __future__ import annotations

import os

import csv
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT = RAW / "census"
OUT.mkdir(parents=True, exist_ok=True)
CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html

RACE_ITER = {  # suffix -> label
    "": "All races", "A": "White alone", "B": "Black/AA alone",
    "C": "AIAN alone", "D": "Asian alone", "H": "White alone nH",
    "I": "Hispanic/Latino",
}
ACS1_YEARS = list(range(2005, 2020)) + [2021, 2022]


def _income_query(year: int):
    """Median household income by race (B19013 + iterations)."""
    codes = [f"B19013{su}_001E" for su in RACE_ITER]
    url = (f"https://api.census.gov/data/{year}/acs/acs1"
           f"?get=NAME,{','.join(codes)}&for=us:1{_key_param()}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        header, row = data[0], data[1]
        return {su: (int(row[header.index(f"B19013{su}_001E")])
                     if row[header.index(f"B19013{su}_001E")] not in ("", "-", None) else None)
                for su in RACE_ITER}
    except Exception as e:
        print(f"  [{year}] income query failed: {repr(e)[:100]}", flush=True)
        return None


def _poverty_query(year: int):
    """Poverty by race (B17001 + iterations: _001E total, _002E below)."""
    codes = []
    for su in RACE_ITER:
        codes += [f"B17001{su}_001E", f"B17001{su}_002E"]
    url = (f"https://api.census.gov/data/{year}/acs/acs1"
           f"?get=NAME,{','.join(codes)}&for=us:1{_key_param()}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        header, row = data[0], data[1]
        out = {}
        for su in RACE_ITER:
            tot = row[header.index(f"B17001{su}_001E")]
            bel = row[header.index(f"B17001{su}_002E")]
            tot = int(tot) if tot not in ("", "-", None) else None
            bel = int(bel) if bel not in ("", "-", None) else None
            out[su] = {"total": tot, "below_poverty": bel,
                       "poverty_rate": round(100 * bel / tot, 2) if (tot and bel) else None}
        return out
    except Exception as e:
        print(f"  [{year}] poverty query failed: {repr(e)[:100]}", flush=True)
        return None


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    print(f"Pulling ACS income + poverty by race, US, {ACS1_YEARS[0]}-{ACS1_YEARS[-1]}...")
    inc_rows, pov_rows = [], []
    for y in ACS1_YEARS:
        inc = _income_query(y)
        pov = _poverty_query(y)
        if inc:
            for su, label in RACE_ITER.items():
                inc_rows.append({"year": y, "race_suffix": su or "all", "race": label,
                                 "median_household_income": inc[su]})
        if pov:
            for su, label in RACE_ITER.items():
                p = pov[su]
                pov_rows.append({"year": y, "race_suffix": su or "all", "race": label,
                                 "total_pop": p["total"],
                                 "below_poverty": p["below_poverty"],
                                 "poverty_rate_pct": p["poverty_rate"]})
        ok = "ok" if (inc and pov) else "PARTIAL"
        print(f"  {y}: {ok}")
        time.sleep(0.3)

    inc_path = OUT / "income_by_race.csv"
    with inc_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_suffix", "race", "median_household_income"])
        w.writeheader(); w.writerows(inc_rows)
    pov_path = OUT / "poverty_by_race.csv"
    with pov_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_suffix", "race",
                          "total_pop", "below_poverty", "poverty_rate_pct"])
        w.writeheader(); w.writerows(pov_rows)
    print(f"\nWrote {inc_path} ({len(inc_rows)} rows)")
    print(f"Wrote {pov_path} ({len(pov_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
