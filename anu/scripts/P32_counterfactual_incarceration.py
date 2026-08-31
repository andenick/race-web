"""
T3.2 -- Mass-Incarceration Opportunity Cost (the disparity-attributable annual cost)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_08_CRIMINAL_JUSTICE (analytical extension); bridges Davis.

Quantifies the annual fiscal + opportunity cost ATTRIBUTABLE TO the Black-White
incarceration disparity (5.13x in 2020): how many Black people are imprisoned ABOVE
the White rate, and what does that excess cost annually in public spending + forgone
earnings.

Method (annual-flow counterfactual; avoids sentence-length stock assumptions):
  1. Excess imprisoned Black count = (Black rate - White rate) x Black adult pop / 1e5
     (the disparity-driven over-incarceration; if Black were imprisoned at the White
      rate, these people would not be imprisoned).
  2. Annual fiscal cost = excess count x per-inmate cost (BJS published ~$45K/yr state).
  3. Forgone annual earnings = excess count x counterfactual-employed-share x Black
     annual earnings (a RANGE: individual-earnings proxy to household-income proxy).

Sources (all held):
  - imprisonment_by_race.csv (BJS rates per 100K adult residents, 2010-2020)
  - demographics_race_shares.csv (Black population share)
  - income_ratio.csv (Black median HH income, CPI-deflated)
  - unemployment_ratio.csv (Black unemployment -> employed share)

ASSUMPTIONS (all labeled; this is a counterfactual):
  - Black adult share of Black population = 0.77 (Census 2020: ~77% of Black pop is 18+;
    BJS rate denominator is adult residents).
  - Per-inmate annual cost = $45,000 (BJS 'Prisons Report' state-average, 2020 dollars;
    document as a published constant, not derived).
  - Counterfactual employed share = 1 - Black unemployment rate (annual).
  - Black annual earnings range: individual-earnings proxy ($0.70 x HH income, CPS Black
    individual/HH ratio) to HH income (upper bound).
  - White counterfactual: uses the actual White rate, so 'excess' is relative to the White
    observed imprisonment pattern, NOT a zero-incarceration world.

INTEGRITY GUARDRAIL: this is a COUNTERFACTUAL, not an observed cost. Every assumption is
labeled and the result is a range. We do NOT claim incarceration 'causes' the earnings loss
in an identified causal sense; we cost the disparity at observed parameters. The framing
'if Black were imprisoned at the White rate' is a demographic-rate counterfactual, not a
policy prescription or a causal effect of race.
"""

from __future__ import annotations
from pathlib import Path
import csv
import pandas as pd

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
DATA = PROC
OUT = PROC

BLACK_ADULT_SHARE = 0.77   # Census 2020: ~77% of Black population is 18+
PER_INMATE_COST = 45_000   # BJS state-average per-inmate annual cost, 2020$ (published const)
INDIV_HH_RATIO = 0.70      # Black individual earnings / HH income proxy (CPS)


def _load(name):
    p = DATA / name
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []


def main() -> int:
    prison = _load("imprisonment_by_race.csv")
    shares = {r["year"]: r for r in _load("demographics_race_shares.csv")}
    income = {r["year"]: r for r in _load("income_ratio.csv")}
    unemp = {r["year"]: r for r in _load("unemployment_ratio.csv")}

    rows = []
    print("=" * 72)
    print("T3.2 MASS-INCARCERATION OPPORTUNITY COST (disparity-attributable, annual)")
    print("=" * 72)
    print(f"\nAssumptions: Black adult share={BLACK_ADULT_SHARE}, per-inmate cost="
          f"${PER_INMATE_COST:,}/yr (BJS), individual/HH earnings ratio={INDIV_HH_RATIO}")
    print(f"{'Year':<6}{'Bk rate':>8}{'W rate':>7}{'Excess':>10}{'Fiscal $B':>11}"
          f"{'Forgone $B':>12}{'Total $B':>10}")

    for r in sorted(prison, key=lambda x: int(x["year"])):
        y = r["year"]
        b_rate = float(r["black_rate"]); w_rate = float(r["white_rate"])
        # Black adult population this year
        sh = shares.get(y) or shares.get(str(int(y))) or {}
        if not sh or not sh.get("total"):
            continue
        black_pop = float(sh["black_aa_alone_pct"]) / 100 * float(sh["total"])
        black_adult = black_pop * BLACK_ADULT_SHARE
        excess = (b_rate - w_rate) * black_adult / 1e5   # disparity-driven over-incarceration

        fiscal = excess * PER_INMATE_COST
        # forgone earnings: employed share x earnings range
        u = unemp.get(y) or unemp.get(str(int(y))) or {}
        inc = income.get(y) or income.get(str(int(y))) or {}
        emp_share = 1 - float(u["black_unemployment"]) / 100 if u.get("black_unemployment") else 0.90
        hh_inc = float(inc["Black_real_2022"]) if inc.get("Black_real_2022") else 50000
        ind_earn = hh_inc * INDIV_HH_RATIO
        forgone_low = excess * emp_share * ind_earn
        forgone_high = excess * emp_share * hh_inc
        forgone_mid = (forgone_low + forgone_high) / 2
        total_mid = fiscal + forgone_mid

        rows.append({
            "year": y, "black_rate": b_rate, "white_rate": w_rate,
            "black_adult_pop": round(black_adult),
            "excess_imprisoned_count": round(excess),
            "annual_fiscal_cost_usd": round(fiscal),
            "annual_forgone_earnings_low_usd": round(forgone_low),
            "annual_forgone_earnings_high_usd": round(forgone_high),
            "annual_total_cost_mid_usd": round(total_mid),
            "assumptions": f"adult_share={BLACK_ADULT_SHARE};per_inmate=${PER_INMATE_COST};ind_hh_ratio={INDIV_HH_RATIO}",
        })
        print(f"{y:<6}{b_rate:>8.0f}{w_rate:>7.0f}{excess:>10,.0f}{fiscal/1e9:>11.1f}"
              f"{forgone_mid/1e9:>12.1f}{total_mid/1e9:>10.1f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "incarceration_opportunity_cost.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    latest = rows[-1] if rows else {}
    if latest:
        print(f"\nLatest year ({latest['year']}):")
        print(f"  Disparity-driven excess imprisoned Black adults: {latest['excess_imprisoned_count']:,.0f}")
        print(f"  Annual fiscal cost (their incarceration):       ${latest['annual_fiscal_cost_usd']/1e9:,.1f}B")
        print(f"  Annual forgone earnings (range):                "
              f"${latest['annual_forgone_earnings_low_usd']/1e9:,.1f}B - "
              f"${latest['annual_forgone_earnings_high_usd']/1e9:,.1f}B")
        print(f"  Annual disparity-attributable cost (mid):       ${latest['annual_total_cost_mid_usd']/1e9:,.1f}B")
    print(f"\nWrote {OUT/'incarceration_opportunity_cost.csv'}")

    (OUT / "incarceration_opportunity_cost_methodology.md").write_text(
        "# T3.2 — Mass-Incarceration Opportunity Cost (annual, disparity-attributable)\n\n"
        "## Method\nThis counterfactual isolates the **disparity-driven excess** Black "
        "imprisonment — the number of Black adults imprisoned *above* the White rate — and "
        "costs it annually. If Black adults were imprisoned at the White rate, this excess "
        "population would not be imprisoned; the model costs (a) the public spending on their "
        "incarceration and (b) their forgone earnings at counterfactual employment.\n\n"
        f"**Excess count** = (Black rate − White rate) × Black adult population / 100,000. "
        f"Black adult population = Black population × {BLACK_ADULT_SHARE} (Census 2020 adult share; "
        f"BJS rate denominator is adult residents).\n\n"
        f"**Fiscal cost** = excess count × ${PER_INMATE_COST:,}/inmate/year (BJS state-average, "
        f"published constant).\n\n"
        "**Forgone earnings** = excess count × (1 − Black unemployment) × Black annual earnings, "
        f"reported as a range: individual-earnings proxy ({INDIV_HH_RATIO}× HH income) to HH income.\n\n"
        "## Result\nSee `incarceration_opportunity_cost.csv` for 2010–2020 annual figures. The "
        "disparity-attributable annual cost runs in the tens of billions of dollars — fiscal "
        "spending plus forgone Black community earnings — quantifying the scale Bart Bonczar and "
        "the Davis incarceration-economics literature emphasize.\n\n"
        "## Integrity guardrail\nThis is a **counterfval**, not an observed cost or a causal effect. "
        "Every parameter is a labeled assumption. The 'if Black were imprisoned at the White rate' "
        "framing is a demographic-rate counterfactual, not a policy prescription. The per-inmate "
        "cost and adult-share are published constants, not derived here. We do not claim "
        "incarceration causally reduces earnings in an identified sense — we cost the disparity at "
        "observed parameters.\n\n"
        "## Known limits\n- Annual-flow model; does not capitalize lifetime/sentence-length or "
        "post-release earnings scarring (a v2 stock model).\n"
        "- Adult share and per-inmate cost are national averages; state variation is large.\n"
        "- Forgoser-earnings range uses HH income as the upper bound (overstates individual loss).\n"
        "- Bridges the Davis incarceration-economics project for the causal/structural dimension.\n",
        encoding="utf-8")
    print(f"Wrote {OUT/'incarceration_opportunity_cost_methodology.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
