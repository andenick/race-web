"""
P08 -- Imprisonment Rate Processor (Panel 8)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Parses the BJS "Prisoners in 2020" Figure 2 CSV (p20stf02.csv, fetched by
L08_fetch_bjs_prisoners.py): imprisonment rate per 100,000 U.S. residents by
race/ethnicity (White, Black, Hispanic, AIAN, Asian), 2010-2020.

OUTPUT (data/processed/):
  imprisonment_by_race.csv  -- rate per 100,000 by race + Black/White ratio
"""

from __future__ import annotations

import csv
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

SRC = RAW / "bjs" / "p20stf02.csv"
OUT = PROC

COLS = ["white", "black", "hispanic", "aian", "asian"]


def _to_int(s):
    s = s.strip().replace(",", "")
    return int(s) if s.isdigit() else None


def main() -> int:
    if not SRC.exists():
        print(f"FATAL: {SRC} missing -- run L08_fetch_bjs_prisoners.py first",
              flush=True)
        return 1

    rows = []
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    in_data = False
    for ln in lines:
        cells = [c.strip() for c in next(csv.reader([ln]))]  # proper quoted-comma handling
        # data rows start with a 4-digit year
        if cells and re.match(r"^\d{4}$", cells[0]) and len(cells) >= 6:
            in_data = True
            y = int(cells[0])
            rec = {"year": y}
            for i, c in enumerate(COLS):
                rec[c + "_rate"] = _to_int(cells[1 + i])
            if rec["white_rate"] and rec["black_rate"]:
                rec["black_white_ratio"] = round(rec["black_rate"] / rec["white_rate"], 2)
                rec["black_white_gap"] = rec["black_rate"] - rec["white_rate"]
            rows.append(rec)
        elif in_data and cells and not re.match(r"^\d{4}$", cells[0]):
            break
    rows.sort(key=lambda r: r["year"])
    if not rows:
        print("FATAL: no data rows parsed from p20stf02.csv", flush=True)
        return 1

    p = OUT / "imprisonment_by_race.csv"
    fields = ["year"] + [c + "_rate" for c in COLS] + ["black_white_ratio", "black_white_gap"]
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {p} ({len(rows)} years)")
    print(f"\n{'Year':<6}{'White':>8}{'Black':>8}{'AIAN':>8}{'Hispanic':>10}{'B/W':>6}")
    for r in rows:
        print(f"{r['year']:<6}{r['white_rate']:>8}{r['black_rate']:>8}{r['aian_rate']:>8}"
              f"{r['hispanic_rate']:>10}{r['black_white_ratio']:>6}")
    ratios = [r["black_white_ratio"] for r in rows if r.get("black_white_ratio")]
    print(f"\n  Black/White imprisonment ratio avg ({rows[0]['year']}-{rows[-1]['year']}): "
          f"{round(statistics.mean(ratios),2)}x (the harshest DuBois ratio)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
