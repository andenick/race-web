"""
P06 -- Education Attainment Processor (Panel 6)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_06_EDUCATION

Computes the bachelor's-degree-or-higher attainment GAP by race from ACS C15002
race iterations, plus the Black/White attainment ratio (the education-gap headline).

Source: L06 (ACS C15002 race iterations, 2006-2022)

OUTPUT (data/processed/):
  education_attainment_gap.csv  -- bachelor's+ % by race + Black/White + Hispanic/White gaps

HEADLINE (to confirm):
  Black bachelor's+ ~25% vs White ~37%; gap has NARROWED over 2006-2022 (college
  enrollment gains). Education gap is narrower than the income gap, consistent
  with education as a partial (not full) equalizer.
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
INP = RAW / "census" / "education_attainment_by_race.csv"
OUT = PROC


def main() -> int:
    if not INP.exists():
        print(f"FATAL: {INP} missing", flush=True); return 1
    by_year = defaultdict(dict)  # year -> race_suffix -> {total, bach, pct}
    with INP.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by_year[int(r["year"])][r["race_suffix"]] = {
                "total": int(r["total_25plus"]),
                "bach": int(r["bachelors_plus"]),
                "pct": float(r["bachelors_pct"])}

    RACE_MAP = {"A": "White", "B": "Black", "C": "AIAN", "D": "Asian",
                "H": "White_nH", "I": "Hispanic"}
    rows = []
    for y in sorted(by_year):
        d = by_year[y]
        rec = {"year": y}
        for su, lab in RACE_MAP.items():
            rec[lab + "_bachelors_pct"] = d.get(su, {}).get("pct")
        white = d.get("A", {}).get("pct")
        black = d.get("B", {}).get("pct")
        hisp = d.get("I", {}).get("pct")
        asian = d.get("D", {}).get("pct")
        if white and black:
            rec["black_white_gap_pp"] = round(white - black, 2)
            rec["black_white_ratio"] = round(black / white, 3)
        if white and hisp:
            rec["hispanic_white_gap_pp"] = round(white - hisp, 2)
        if white and asian:
            rec["asian_white_gap_pp"] = round(asian - white, 2)  # Asian often EXCEEDS White
        rows.append(rec)

    cols = ["year"] + [f"{l}_bachelors_pct" for l in
            ["White", "Black", "AIAN", "Asian", "White_nH", "Hispanic"]] + \
           ["black_white_gap_pp", "black_white_ratio",
            "hispanic_white_gap_pp", "asian_white_gap_pp"]
    out_path = OUT / "education_attainment_gap.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {out_path} ({len(rows)} years)")

    if rows:
        ratios = [r["black_white_ratio"] for r in rows if r.get("black_white_ratio")]
        first, last = rows[0], rows[-1]
        print(f"\n--- Panel 6 Education Summary ---")
        print(f"  Black/White bachelor's+ ratio ({first['year']}-{last['year']}): "
              f"avg {round(statistics.mean(ratios), 3)}")
        print(f"  {first['year']}: White {first['White_bachelors_pct']}% | Black {first['Black_bachelors_pct']}% | "
              f"gap {first['black_white_gap_pp']}pp")
        print(f"  {last['year']}: White {last['White_bachelors_pct']}% | Black {last['Black_bachelors_pct']}% | "
              f"gap {last['black_white_gap_pp']}pp | Asian {last['Asian_bachelors_pct']}%")
        # trend: has the gap narrowed?
        dw = last["White_bachelors_pct"] - first["White_bachelors_pct"]
        db = last["Black_bachelors_pct"] - first["Black_bachelors_pct"]
        print(f"  Change {first['year']}->{last['year']}: White +{dw:.1f}pp, Black +{db:.1f}pp "
              f"-> gap {'narrowed' if db > dw else 'widened'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
