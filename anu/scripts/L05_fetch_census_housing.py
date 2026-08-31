"""
L05 -- Census ACS Housing Tenure by Race Loader (Panel 5)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_05_HOUSING

Pulls housing tenure (homeownership rate) by race from ACS Table B25003 (Tenure
by Race of Householder) and its race iterations. The homeownership gap is a
canonical driver of the wealth gap (home equity is the primary Black asset).

Source: U.S. Census Bureau, ACS 1-Year, Table B25003 (+ A/B/C/D/H/I)
        _001E = total occupied housing units; _002E = owner-occupied
        homeownership_rate = _002E / _001E

COVERAGE: ACS 1-Year 2005-2019, 2021, 2022 (2020 cancelled)

OUTPUT (data/raw/census/):
  housing_tenure_by_race.csv  -- total + owner-occupied + rate by race, 2005-2022
"""

from __future__ import annotations

import os
import csv, json, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT = RAW / "census"; OUT.mkdir(parents=True, exist_ok=True)
CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html
RACE = {"": "All", "A": "White alone", "B": "Black/AA alone", "C": "AIAN alone",
        "D": "Asian alone", "H": "White alone nH", "I": "Hispanic/Latino"}
YEARS = list(range(2005, 2020)) + [2021, 2022]


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    rows = []
    for y in YEARS:
        for su, label in RACE.items():
            url = (f"https://api.census.gov/data/{y}/acs/acs1"
                   f"?get=NAME,B25003{su}_001E,B25003{su}_002E&for=us:1{_key_param()}")
            try:
                d = json.loads(urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"}), timeout=30).read().decode())
                h, row = d[0], d[1]
                tot = int(row[h.index(f"B25003{su}_001E")])
                own = int(row[h.index(f"B25003{su}_002E")])
                rows.append({"year": y, "race_suffix": su or "all", "race": label,
                             "total_occupied": tot, "owner_occupied": own,
                             "homeownership_rate": round(100 * own / tot, 2)})
            except Exception:
                pass
            time.sleep(0.12)
        print(f"  {y}: done")
    p = OUT / "housing_tenure_by_race.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_suffix", "race",
                          "total_occupied", "owner_occupied", "homeownership_rate"])
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {p} ({len(rows)} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
