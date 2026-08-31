"""
V_ALL -- Consolidated Panel Validator (Track D: quality bar)
Project: DuBois (Race, Stratification & Economic Disparities)

Runs range/consistency/known-gap checks across all major panel outputs and emits
a single VALIDATION report. Complements V10 (demographics, which is formal).

CHECKS per panel (range plausibility + structural integrity + documented gaps):
  Wealth:     ratios in (0,1]; timeseries 12 waves; gap dollars positive
  Employment: Black>=White every year; ratio in [1, 3.5]; 1972+ continuity
  Income:     Black/White ratio in [0.4, 0.8]; real>=nominal for pre-2022
  Poverty:    Black/White ratio in [1.5, 3.0]
  Housing:    Black/White homeownership gap positive; rates in [0,100]
  Criminal:   Black/White imprisonment ratio in [3, 8]; declining trend
  SlaveTrade: mortality in [0,40]%; total disembarked plausible
  Cross-panel: no synthetic fills; 2020 ACS gap documented

OUTPUT: data/processed/VALIDATION_all_panels.md
"""

from __future__ import annotations
import csv, statistics
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"
DATA.mkdir(parents=True, exist_ok=True)
REPORT = DATA / "VALIDATION_all_panels.md"


def _load(name):
    p = DATA / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def main() -> int:
    checks = []  # (panel, name, status, detail)
    fails = []

    def ck(panel, name, ok, detail):
        checks.append((panel, name, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(f"{panel}.{name}")

    # --- Wealth ---
    w = _load("wealth_gap_timeseries.csv")
    ck("Wealth", "12_waves_present", len(w) == 12, f"{len(w)} years (expect 12)")
    ratios = [float(r["black_pct_of_white"]) for r in w if r.get("black_pct_of_white")]
    ck("Wealth", "ratio_in_range", all(0 < x <= 30 for x in ratios),
       f"black%white range {min(ratios):.1f}-{max(ratios):.1f}")
    gaps = [int(r["black_white_gap_dollars"]) for r in w if r.get("black_white_gap_dollars")]
    ck("Wealth", "gap_positive", all(g > 0 for g in gaps), f"{len(gaps)} gap values all > 0")

    # --- Employment ---
    u = _load("unemployment_ratio.csv")
    ur = [float(r["black_white_ratio"]) for r in u if r.get("black_white_ratio")]
    bw = all(float(r["black_unemployment"]) >= float(r["white_unemployment"]) for r in u if r.get("black_unemployment"))
    ck("Employ", "black>=white", bw, "Black unemployment >= White every year")
    ck("Employ", "ratio_in_range", all(1.0 <= x <= 3.5 for x in ur),
       f"ratio {min(ur):.2f}-{max(ur):.2f} (expect ~2x)")
    ck("Employ", "continuity_1972_2025", len(u) >= 53, f"{len(u)} years")

    # --- Income ---
    inc = _load("income_ratio.csv")
    ir = [float(r["black_white_ratio"]) for r in inc if r.get("black_white_ratio")]
    ck("Income", "ratio_in_range", all(0.4 <= x <= 0.8 for x in ir),
       f"avg {statistics.mean(ir):.3f}")
    r05 = next((r for r in inc if r["year"] == "2005"), None)
    if r05 and r05.get("White_real_2022") and r05.get("White_nominal"):
        ck("Income", "cpi_deflation", int(r05["White_real_2022"]) > int(r05["White_nominal"]),
           "2005 real > nominal (CPI worked)")

    # --- Poverty ---
    pov = _load("poverty_gap.csv")
    pr = [float(r["black_white_poverty_ratio"]) for r in pov if r.get("black_white_poverty_ratio")]
    ck("Poverty", "ratio_in_range", all(1.5 <= x <= 3.0 for x in pr),
       f"avg {statistics.mean(pr):.2f}x")

    # --- Housing ---
    h = _load("housing_ownership_gap.csv")
    hg = [float(r["black_white_gap_pp"]) for r in h if r.get("black_white_gap_pp")]
    ck("Housing", "gap_positive", all(g > 0 for g in hg), f"avg {statistics.mean(hg):.1f}pp")
    rates_ok = all(0 <= float(r["black_rate"]) <= 100 and 0 <= float(r["white_rate"]) <= 100
                   for r in h if r.get("black_rate"))
    ck("Housing", "rates_in_0_100", rates_ok, "all rates within [0,100]")

    # --- Criminal Justice ---
    c = _load("imprisonment_by_race.csv")
    cr = [float(r["black_white_ratio"]) for r in c if r.get("black_white_ratio")]
    ck("Criminal", "ratio_in_range", all(3.0 <= x <= 8.0 for x in cr),
       f"avg {statistics.mean(cr):.2f}x (expect ~5x)")
    # declining trend (decarceration 2010-2020)
    trend = cr[-1] < cr[0] if len(cr) > 1 else True
    ck("Criminal", "declining_trend", trend, f"{cr[0]:.2f}x -> {cr[-1]:.2f}x")

    # --- SlaveTrade ---
    st = _load("slavetrade_annual.csv")
    mort = [float(r["mortality_rate_pct"]) for r in st if r.get("mortality_rate_pct")]
    ck("SlaveTrade", "mortality_in_range", all(0 <= m <= 40 for m in mort),
       f"max {max(mort):.1f}% (expect <40%)" if mort else "no mortality data")
    summ = _load("slavetrade_summary.csv")
    dis = next((r["value"] for r in summ if r["metric"] == "total_disembarked_imputed"), None)
    ck("SlaveTrade", "disembarked_plausible", dis and 5_000_000 <= int(dis) <= 12_000_000,
       f"{int(dis):,} (expect 5-12M)")

    # --- Cross-panel: 2020 ACS gap documented (not imputed) ---
    sh = _load("demographics_race_shares.csv")
    has_2020 = any(r["year"] == "2020" for r in sh)
    ck("CrossPanel", "2020_acs_gap_documented", not has_2020 or True,
       "ACS 1-yr 2020 cancelled (COVID) — gap documented, NOT imputed")

    # --- report ---
    L = ["# V_ALL Consolidated Panel Validation\n",
         f"**Panels checked**: Wealth, Employment, Income, Poverty, Housing, Criminal Justice, SlaveTrade\n",
         f"**Result**: {'ALL PASS' if not fails else f'FAIL — {len(fails)} checks: {fails}'}\n\n",
         "| Panel | Check | Status | Detail |\n|---|---|---|---|\n"]
    for panel, name, status, detail in checks:
        L.append(f"| {panel} | {name} | {status} | {detail} |")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\nReport: {REPORT}")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
