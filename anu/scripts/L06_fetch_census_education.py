"""
L06 -- Census ACS Educational Attainment by Race Loader (Panel 6)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_06_EDUCATION

Pulls educational attainment (population 25+) by race from Census ACS Table
B15002 (Sex by Educational Attainment) and its race iterations. Computes the
bachelor's-degree-or-higher rate by race -- the canonical education-gap series.

Source: U.S. Census Bureau, ACS 1-Year Estimates, Table B15002 (+ A/B/C/D/H/I)
URL: https://api.census.gov/data/{year}/acs/acs1
License: Public domain (US Government)

BACHELOR'S+ COLUMNS (confirmed via Census variables metadata, identical across
race iterations A/B/C/D/H/I):
  _001E  = total population 25+
  Male:   _015E Bachelor's, _016E Master's, _017E Professional, _018E Doctorate
  Female: _032E Bachelor's, _033E Master's, _034E Professional, _035E Doctorate
  bachelor's+ = sum of the 8 degree columns

RACE ITERATIONS: (base)=All, A=White, B=Black/AA, C=AIAN, D=Asian, H=White nH, I=Hispanic

COVERAGE: ACS 1-Year 2005-2019, 2021, 2022 (2020 cancelled, COVID -- documented gap)

OUTPUT (data/raw/census/):
  education_attainment_by_race.csv  -- bachelor's+ count + % by race, 2005-2022

KNOWN LIMITATIONS:
  - "Bachelor's degree or higher" only (HS, some-college not split here; v2).
  - ACS race "alone" universe; Hispanic separate (H vs I).
  - 2020 gap left null.
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

RACE_ITER = {"A": "White alone", "B": "Black/AA alone",
             "C": "AIAN alone", "D": "Asian alone", "H": "White alone nH",
             "I": "Hispanic/Latino"}
# C15002 race iterations use a MORE-COLLAPSED structure than the base table
# (confirmed via Census group metadata). Bachelor's+ is PRE-SUMMED per sex:
#   _001E = total 25+    _006E = Male bachelor's+    _011E = Female bachelor's+
TOTAL_COL = "001"
MALE_BACH = "006"
FEMALE_BACH = "011"
ACS1_YEARS = list(range(2005, 2020)) + [2021, 2022]


def _query(year: int):
    """Pull C15002 race iterations; return {race_suffix: {total, bachelors, pct}}."""
    out = {}
    for su in RACE_ITER:
        codes = [f"C15002{su}_{TOTAL_COL}E",
                 f"C15002{su}_{MALE_BACH}E",
                 f"C15002{su}_{FEMALE_BACH}E"]
        url = (f"https://api.census.gov/data/{year}/acs/acs1"
               f"?get=NAME,{','.join(codes)}&for=us:1{_key_param()}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
            header, row = data[0], data[1]
            total = int(row[header.index(f"C15002{su}_{TOTAL_COL}E")])
            bach = int(row[header.index(f"C15002{su}_{MALE_BACH}E")]) + \
                   int(row[header.index(f"C15002{su}_{FEMALE_BACH}E")])
            out[su] = {"total_25plus": total, "bachelors_plus": bach,
                       "bachelors_pct": round(100 * bach / total, 2)}
        except Exception as e:
            print(f"  [{year} {su}] failed: {repr(e)[:80]}", flush=True)
        time.sleep(0.15)
    return out


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    print(f"Pulling ACS education attainment by race, {ACS1_YEARS[0]}-{ACS1_YEARS[-1]}...")
    rows = []
    for y in ACS1_YEARS:
        res = _query(y)
        for su, label in RACE_ITER.items():
            if su in res:
                rows.append({"year": y, "race_suffix": su, "race": label, **res[su]})
        print(f"  {y}: {'ok' if res else 'PARTIAL'} ({len(res)} races)")

    out_path = OUT / "education_attainment_by_race.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_suffix", "race",
                          "total_25plus", "bachelors_plus", "bachelors_pct"])
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {out_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
