"""
T3.1 -- Reparations Counterfactual: the Aggregate Black-White Wealth Shortfall
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_14_REPARATIONS (the quantitative anchor)

Quantifies the order of magnitude of the Black-White wealth gap in aggregate dollars,
answering: "What total dollar figure does the 2022 SCF wealth gap imply?"

Method: aggregate the per-household wealth gap x the number of Black households.
Reported as a RANGE because wealth is right-skewed:
  - MEDIAN-based shortfall (conservative lower bound): uses the median per-household gap.
  - MEAN-based shortfall (upper bound, tail-inflated): uses the mean per-household gap.
  The true figure that a reparations policy would target sits between; the mean is
  dominated by the wealthy White tail, the median by the typical household.

Cross-reference: Darity & Mullen (2020) 'From Here to Equality' estimate ~$10-12T using
a HISTORICAL-COMPOUNDING counterfactual (accumulating the wage gap since Emancipation at
an assumed return). That is a DIFFERENT counterfactual than the static 2022 gap -- ours
asks 'what closes today's gap', theirs asks 'what compensates the cumulative historical
loss'. Both are legitimate; they are not the same question.

Source: Fed SCF 2022 (public download: https://www.federalreserve.gov/econres/files/scfp2022.zip)
Black households = SCF race 2 (Black non-Hispanic), WGT sum across all 5 implicates
(this extract's weights sum to the US household population; no /5).

INTEGRITY GUARDRAIL (MANDATORY):
  This is a COUNTERFACTUAL, not an observed transfer. Every assumption is labeled. The
  mean-based figure is explicitly flagged as tail-inflated. We do NOT prescribe a policy
  amount -- we report the order of magnitude the data imply, with explicit sensitivity.
  No causal claim that reparations 'would' close the gap; only that the gap, aggregated,
  equals this dollar magnitude today.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
SCF_DIR = RAW / "scf" / "2022"
OUT = PROC


def wmed(v, w):
    o = np.argsort(v); v = v[o]; w = w[o]; c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * w.sum())])


def wmean(v, w):
    return float((v * w).sum() / w.sum())


def _load_scf_2022(cols):
    """Read the 2022 SCF summary .dta (fetched by L01) with UPPER-case columns."""
    dta = next((RAW / "scf" / "2022").rglob("*.dta"))
    df = pd.read_stata(dta, columns=[c.lower() for c in cols])
    df.columns = [str(c).upper() for c in df.columns]
    return df


def main() -> int:
    df = _load_scf_2022(["RACE", "WGT", "NETWORTH"])
    df["WGT"] = df["WGT"].astype(float)
    w = df[df["RACE"] == 1]; b = df[df["RACE"] == 2]
    ww = w["WGT"].values; wb = b["WGT"].values

    white_hh = ww.sum()          # this extract: WGT sums to population across implicates
    black_hh = wb.sum()
    w_med = wmed(w["NETWORTH"].values, ww); b_med = wmed(b["NETWORTH"].values, wb)
    w_mean = wmean(w["NETWORTH"].values, ww); b_mean = wmean(b["NETWORTH"].values, wb)

    median_gap = w_med - b_med
    mean_gap = w_mean - b_mean
    median_shortfall = median_gap * black_hh
    mean_shortfall = mean_gap * black_hh

    # Darity-Mullen comparison bracket
    darity_mullen_low, darity_mullen_high = 10e12, 12e12

    print("=" * 72)
    print("T3.1 REPARATIONS COUNTERFACTUAL -- aggregate Black-White wealth shortfall (SCF 2022)")
    print("=" * 72)
    print(f"\nBlack households (SCF race 2, WGT sum): {black_hh:,.0f}  "
          f"({100*black_hh/(white_hh+black_hh+df[df.RACE==3].WGT.sum()):.1f}% of White+Black+Hispanic)")
    print(f"Per-household gap:  median ${median_gap:,.0f}   mean ${mean_gap:,.0f}")
    print(f"\nAGGREGATE SHORTFALL (gap x Black households):")
    print(f"  MEDIAN-based (conservative): ${median_shortfall/1e12:,.2f} trillion")
    print(f"  MEAN-based (tail-inflated):  ${mean_shortfall/1e12:,.2f} trillion")
    print(f"\nDarity & Mullen (2020) historical-compounding estimate: "
          f"${darity_mullen_low/1e12:.0f}-${darity_mullen_high/1e12:.0f}T "
          f"(DIFFERENT counterfactual: cumulative historical loss, not static 2022 gap)")
    print(f"\nInterpretation: a static 2022-closing transfer would be ~${median_shortfall/1e12:.1f}T "
          f"(median) to ${mean_shortfall/1e12:.0f}T (mean). The mean is dominated by the wealthy White "
          f"tail; the median better reflects the typical-household gap. CA Task Force figures "
          f"(per-capita eligible-population x payment) are a third, distinct methodology.")

    # write
    rows = [
        {"metric": "black_households_scf", "value": round(black_hh)},
        {"metric": "white_households_scf", "value": round(white_hh)},
        {"metric": "white_median_networth", "value": round(w_med)},
        {"metric": "black_median_networth", "value": round(b_med)},
        {"metric": "white_mean_networth", "value": round(w_mean)},
        {"metric": "black_mean_networth", "value": round(b_mean)},
        {"metric": "median_per_hh_gap", "value": round(median_gap)},
        {"metric": "mean_per_hh_gap", "value": round(mean_gap)},
        {"metric": "aggregate_median_shortfall_trillion_usd", "value": round(median_shortfall / 1e12, 3)},
        {"metric": "aggregate_mean_shortfall_trillion_usd", "value": round(mean_shortfall / 1e12, 3)},
        {"metric": "darity_mullen_2020_estimate_low_trillion_usd", "value": 10.0},
        {"metric": "darity_mullen_2020_estimate_high_trillion_usd", "value": 12.0},
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reparations_counterfactual.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    print(f"\nWrote {OUT/'reparations_counterfactual.csv'}")

    (OUT / "reparations_methodology.md").write_text(
        f"# T3.1 — Reparations Counterfactual: Aggregate Wealth Shortfall (SCF 2022)\n\n"
        f"## Result\nThe 2022 Black–White wealth gap, aggregated across **{black_hh/1e6:.1f}M** Black "
        f"non-Hispanic households (SCF), implies a total shortfall of **${median_shortfall/1e12:.1f}T** "
        f"(median per-household gap) to **${mean_shortfall/1e12:.0f}T** (mean per-household gap).\n\n"
        f"- Median per-household gap: **${median_gap:,.0f}** (White median ${w_med:,.0f} − Black "
        f"median ${b_med:,.0f}).\n"
        f"- Mean per-household gap: **${mean_gap:,.0f}** (White mean ${w_mean:,.0f} − Black mean "
        f"${b_mean:,.0f}).\n\n"
        f"## Why a range\nWealth is right-skewed: the mean White household is pulled up by a wealthy "
        f"tail, so the mean gap (${mean_shortfall/1e12:.0f}T) overstates the typical-household gap. "
        f"The median gap (${median_shortfall/1e12:.1f}T) better reflects the typical household but "
        f"understates the total because it ignores the upper-tail concentration. A reparations policy "
        f"targeting the full gap would land between these; Darity & Mullen (2020) estimate ~$10–12T "
        f"via a *historical-compounding* counterfactual (accumulating the post-Emancipation wage gap "
        f"at an assumed return) — a **different question** than the static 2022 gap, which is why "
        f"their figure need not equal either bound here. The CA Task Force used a third methodology "
        f"(eligible population × per-capita payment).\n\n"
        f"## Integrity guardrail\nThis is a **counterfactual**, not an observed or prescribed transfer. "
        f"The aggregate is a mechanical multiplication of the observed gap × observed household count; "
        f"it states what the gap sums to today, not what policy ought to do. The mean figure is "
        f"explicitly flagged as tail-inflated. No causal claim.\n\n"
        f"## Known limits\n- 2022 cross-section; the gap fluctuates across SCF waves.\n"
        f"- SCF race 2 = Black non-Hispanic; multiracial/Hispanic-Black households are in other "
        f"categories, so this is a lower bound on the affected population.\n"
        f"- Excludes the debtor-household dimension (Black households disproportionately have ≤0 net "
        f"worth; the median captures this as a low number but a 'shortfall' framing assumes a positive "
        f"target).\n", encoding="utf-8")
    print(f"Wrote {OUT/'reparations_methodology.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
