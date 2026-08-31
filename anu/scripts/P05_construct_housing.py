"""
P05 -- Housing Gap Processor (Panel 5)
Computes the Black/White homeownership gap (the canonical ~28pp gap).
"""
from __future__ import annotations
import csv, statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
INP = RAW / "census" / "housing_tenure_by_race.csv"
OUT = PROC


def main() -> int:
    by_year = defaultdict(dict)
    with INP.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by_year[int(r["year"])][r["race_suffix"]] = float(r["homeownership_rate"])
    rows = []
    for y in sorted(by_year):
        d = by_year[y]
        rec = {"year": y, "white_rate": d.get("A"), "black_rate": d.get("B"),
               "hispanic_rate": d.get("I"), "asian_rate": d.get("D")}
        if d.get("A") and d.get("B"):
            rec["black_white_gap_pp"] = round(d["A"] - d["B"], 2)
        if d.get("A") and d.get("I"):
            rec["hispanic_white_gap_pp"] = round(d["A"] - d["I"], 2)
        rows.append(rec)
    p = OUT / "housing_ownership_gap.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "white_rate", "black_rate",
                          "hispanic_rate", "asian_rate", "black_white_gap_pp",
                          "hispanic_white_gap_pp"])
        w.writeheader(); w.writerows(rows)
    gaps = [r["black_white_gap_pp"] for r in rows if r.get("black_white_gap_pp")]
    last = rows[-1]
    print(f"Wrote {p} ({len(rows)} yrs)")
    print(f"  Black/White homeownership gap: avg {round(statistics.mean(gaps),1)}pp "
          f"({rows[0]['year']}-{rows[-1]['year']})")
    print(f"  {last['year']}: White {last['white_rate']}% | Black {last['black_rate']}% "
          f"| gap {last['black_white_gap_pp']}pp | Hispanic {last['hispanic_rate']}%")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
