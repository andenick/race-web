"""
L09 -- Census ABS Business Ownership by Race Loader (Panel 9)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_09_BUSINESS

Pulls employer firms, employees, and payroll by owner race from the Census
Annual Business Survey Company Summary (abscs).

Source: U.S. Census Bureau, ABS Company Summary
        https://api.census.gov/data/{year}/abscs
License: Public domain

RACE_GROUP codes: 00=All, 30=White, 40=Black/AA, 50=AIAN, 60=Asian,
                 70=NHPI, 91=Hispanic

COVERAGE: ABS published 2018-2021 (annual; replaces old Survey of Business Owners)

OUTPUT (data/raw/census/):
  business_ownership_by_race.csv  -- firms, employees, payroll by owner race
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
RACE = {"30": "White", "40": "Black/AA", "50": "AIAN", "60": "Asian",
        "70": "NHPI", "91": "Hispanic"}
YEARS = [2018, 2019, 2020, 2021]


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
        url = (f"https://api.census.gov/data/{y}/abscs"
               f"?get=NAME,FIRMPDEMP,EMP,PAYANN,RACE_GROUP&for=us:1{_key_param()}")
        try:
            d = json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"}), timeout=40).read().decode())
            h, data = d[0], d[1:]
            # total firms for share calc
            total = next((int(r[h.index("FIRMPDEMP")]) for r in data
                          if r[h.index("RACE_GROUP")] == "00"), None)
            for r in data:
                code = r[h.index("RACE_GROUP")]
                if code in RACE:
                    firms = int(r[h.index("FIRMPDEMP")])
                    rows.append({
                        "year": y, "race_group": code, "race": RACE[code],
                        "firms": firms,
                        "employees": int(r[h.index("EMP")]),
                        "payroll_thousands": int(r[h.index("PAYANN")]),
                        "share_of_firms_pct": round(100 * firms / total, 2) if total else None})
            print(f"  {y}: total firms {total:,}")
        except Exception as e:
            print(f"  {y}: FAILED {repr(e)[:80]}")
        time.sleep(0.3)
    p = OUT / "business_ownership_by_race.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "race_group", "race",
                          "firms", "employees", "payroll_thousands", "share_of_firms_pct"])
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {p} ({len(rows)} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
