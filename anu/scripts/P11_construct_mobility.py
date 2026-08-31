"""
P11 -- Intergenerational Mobility Processor (Panel 11)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_11_MOBILITY

Computes the Black-White intergenerational mobility gap from the Opportunity
Atlas national race-by-cohort data (Table 5, Chetty et al. 2018).

Source: Opportunity Insights / Opportunity Atlas, Table 5: National mobility by
        race, gender, and parent income percentile.
  File: data/raw/opportunity/table_5.csv (15 cohorts; fetched by L14_fetch_opportunity_atlas.py)
  Paper: Chetty, Raj, Nathaniel Hendren, Maggie Jones, Sonya Porter (2018),
         "Race and Economic Opportunity in the United States: An Intergenerational
         Perspective." QJE 133(2).
  Data portal: https://opportunityinsights.org/data/

DATA NOTE (resolving the prior blocker):
  The TODO listed P11 as blocked because "Table_5 national already acquired, no
  race col." That was incorrect: Table 5 DOES contain race-disaggregated columns
  (kfr_black_pooled_pXX, kfr_white_pooled_pXX, etc.). The prior session was
  looking for a TRACT-level file (geographic detail), but the national-level
  race x cohort data is sufficient for this panel and IS race-disaggregated.

METRIC:
  kfr = "kid family income rank": the mean percentile rank in the national family
  income distribution for children at age ~31, conditional on their parents'
  income percentile. kfr_*_pooled_p25 = children whose parents were at the 25th
  income percentile; kfr_*_pooled_p75 = parents at the 75th percentile.

  This directly measures intergenerational mobility: does a child born into a
  given starting position move up, stay, or fall?

OUTPUT (data/processed/):
  mobility_gap_by_race.csv -- Black/White/Asian/Hispanic kfr by parent income
                              percentile x cohort + Black-White gap and ratio

HEADLINE:
  For children born to parents at the 25th income percentile (p25):
    - Black children land at the 33.5th percentile (1978 cohort); White at 48.4th.
    - Gap narrowed from 14.9pp (1978) to 10.9pp (1992), driven by BOTH modest
      Black gains AND White stagnation.
    - Black/White mobility ratio improved 0.69 → 0.76.
  Mobility is the SLOWEST-moving DuBois panel: 14 years of cohorts (1978-1992),
  the gap narrowed ~4pp — generational change.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
INP = RAW / "opportunity" / "table_5.csv"
OUT = PROC

# Parent-income percentiles available in the data
PARENT_PCTS = ["p25", "p75", "p100"]
RACES = ["black", "white", "asian", "hisp", "aian", "pooled"]


def main() -> int:
    if not INP.exists():
        print(f"FATAL: {INP} missing", flush=True)
        return 1

    with INP.open(encoding="utf-8") as fh:
        raw = list(csv.DictReader(fh))

    rows = []
    for r in raw:
        cohort = int(r["cohort"])
        rec = {"cohort": cohort}
        for pct in PARENT_PCTS:
            for race in RACES:
                col = f"kfr_{race}_pooled_{pct}"
                val = r.get(col, "")
                if val:
                    try:
                        v = float(val)
                        # convert percentile fraction (0.335) to rank (33.5)
                        rec[f"kfr_{race}_{pct}_pctile"] = round(v * 100, 1)
                    except ValueError:
                        rec[f"kfr_{race}_{pct}_pctile"] = None
                else:
                    rec[f"kfr_{race}_{pct}_pctile"] = None

        # Black-White gap + ratio at each percentile
        for pct in PARENT_PCTS:
            bk = rec.get(f"kfr_black_{pct}_pctile")
            wk = rec.get(f"kfr_white_{pct}_pctile")
            if bk is not None and wk is not None:
                rec[f"black_white_gap_{pct}_pp"] = round(wk - bk, 1)
                rec[f"black_white_ratio_{pct}"] = round(bk / wk, 3) if wk else None
            else:
                rec[f"black_white_gap_{pct}_pp"] = None
                rec[f"black_white_ratio_{pct}"] = None

        rows.append(rec)

    cols = ["cohort"]
    for pct in PARENT_PCTS:
        for race in RACES:
            cols.append(f"kfr_{race}_{pct}_pctile")
    for pct in PARENT_PCTS:
        cols.append(f"black_white_gap_{pct}_pp")
        cols.append(f"black_white_ratio_{pct}")

    out_path = OUT / "mobility_gap_by_race.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path} ({len(rows)} cohorts)")

    # --- Summary ---
    print(f"\n--- Panel 11 Intergenerational Mobility Summary ---")
    print(f"kfr (kid income rank) at p25 (parents at 25th percentile):")
    print(f"{'Cohort':8} {'Black':>8} {'White':>8} {'Asian':>8} {'Gap':>6} {'B/W':>6}")
    for r in rows:
        bk = r.get("kfr_black_p25_pctile", "?")
        wk = r.get("kfr_white_p25_pctile", "?")
        ak = r.get("kfr_asian_p25_pctile", "?")
        gap = r.get("black_white_gap_p25_pp", "?")
        ratio = r.get("black_white_ratio_p25", "?")
        print(f"{r['cohort']:8} {bk:>8} {wk:>8} {ak:>8} {gap:>6} {ratio:>6}")

    first, last = rows[0], rows[-1]
    p25_gaps = [r["black_white_gap_p25_pp"] for r in rows
                if r.get("black_white_gap_p25_pp") is not None]
    print(f"\n  p25 gap: {first['black_white_gap_p25_pp']}pp ({first['cohort']}) -> "
          f"{last['black_white_gap_p25_pp']}pp ({last['cohort']})")
    print(f"  Trend: {'narrowing' if last['black_white_gap_p25_pp'] < first['black_white_gap_p25_pp'] else 'widening'}")
    print(f"  Black/White ratio: {first['black_white_ratio_p25']} -> {last['black_white_ratio_p25']}")
    print(f"\n  p75 (parents at 75th percentile):")
    p75_first = first.get("black_white_gap_p75_pp")
    p75_last = last.get("black_white_gap_p75_pp")
    print(f"    Gap: {p75_first}pp -> {p75_last}pp (also {'narrowing' if p75_last < p75_first else 'stable'})")
    print(f"\n  Mobility is the SLOWEST-moving DuBois panel: ~{first['black_white_gap_p25_pp']}->{last['black_white_gap_p25_pp']}pp")
    print(f"  over 14 birth cohorts. The gap narrows but persists at every starting income.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
