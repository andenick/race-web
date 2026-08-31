"""
L13 -- ACS Income by Race by Metro Loader (Panel 13: Geographic Disparities)
Pulls median household income by race (B19013A White / B19013B Black) for all
metro areas, 2022. Computes the Black-White income gap by metro.
"""
from __future__ import annotations

import os
import csv, json, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT = RAW / "census"; OUT.mkdir(parents=True, exist_ok=True)
CENSUS_KEY = os.environ.get("CENSUS_API_KEY", "")  # free key required: api.census.gov/data/key_signup.html


def _pull(var, year=2022):
    url = (f"https://api.census.gov/data/{year}/acs/acs1"
           f"?get=NAME,{var}&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:*{_key_param()}")
    d = json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"}), timeout=60).read().decode())
    h, rows = d[0], d[1:]
    return {r[h.index("metropolitan statistical area/micropolitan statistical area")]:
            (r[h.index(var)], r[h.index("NAME")]) for r in rows}


def _key_param() -> str:
    """Census API key URL fragment. The Census API requires a (free) key."""
    if not CENSUS_KEY:
        raise SystemExit(
            "The Census API requires an API key. Get a free key at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY.")
    return f"&key={CENSUS_KEY}"


def main() -> int:
    print("Pulling B19013A (White) + B19013B (Black) income by metro, 2022...")
    white = _pull("B19013A_001E")
    black = _pull("B19013B_001E")
    rows = []
    for metro_id, (wv, name) in white.items():
        if metro_id in black:
            bv, _ = black[metro_id]
            try:
                w = int(wv); b = int(bv)
                # only metros (codes ending 00000 are... actually metro codes vary); keep if both present
                if w > 0 and b > 0:
                    rows.append({"metro_id": metro_id, "metro_name": name,
                                 "white_income": w, "black_income": b,
                                 "black_white_ratio": round(b / w, 3),
                                 "gap_dollars": w - b})
            except (ValueError, TypeError):
                pass
    rows.sort(key=lambda r: r["gap_dollars"], reverse=True)
    p = OUT / "metro_income_by_race_raw.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["metro_id", "metro_name", "white_income",
                          "black_income", "black_white_ratio", "gap_dollars"])
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {p} ({len(rows)} metros with both races); run P13 to build the panel")
    print("\nTop 10 widest Black-White income gaps (large metros):")
    print(f"{'Metro':<40}{'White':>10}{'Black':>10}{'Ratio':>7}")
    for r in rows[:10]:
        print(f"{r['metro_name'][:39]:<40}{r['white_income']:>10,}{r['black_income']:>10,}{r['black_white_ratio']:>7}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
