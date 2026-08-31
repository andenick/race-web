"""
T2.1 -- Black-White Wealth-Gap Decomposition (FLAGSHIP analytical module)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_01_WEALTH -- the project's headline finding, now analytical (not just descriptive)

Oaxaca-Blinder decomposition of the Black-White wealth gap on Fed SCF 2022 microdata,
answering: "How much of the gap is explained by differences in income, homeownership,
education, age, and family structure -- and how much is unexplained?"

Source: Board of Governors of the Federal Reserve System, Survey of Consumer Finances 2022.
Public download: https://www.federalreserve.gov/econres/files/scfp2022.zip
Coverage: 2022 (v1). Historical-wave decomposition is a v2 refinement.

TWO decompositions (reported together for honesty about skewness):
  (A) LOG net worth -- standard wealth-gap literature approach.
      Drops households with NETWORTH <= 0 (~7% debtors; documented exclusion).
      Gap = E[ln NW_W] - E[ln NW_B], reported as % of the mean log gap.
  (B) LEVELS net worth at the mean -- dollar decomposition, ALL households.
      Tail-dominated (mean >> median); reported in dollars, flagged as such.

REFERENCE GROUP = White (race 1). The decomposition counterfactual asks: "what would
Black mean wealth be if Black households had White returns (coefficients)?"
  gap = explained [(Xbar_W - Xbar_B) . beta_W]  +  unexplained [(beta_W - beta_B) . Xbar_B]

COVARIATES: INCOME, AGE, AGE^2, education (EDCL 4-cat dummies, ref=no-HS), homeowner
(HOUSECL==1), married (MARRIED==1), KIDS, family structure (FAMSTRUCT 5-cat dummies),
labor-force (LF==1).

SCF WEIGHTING: 5 implicates per household; we use all implicates with sample weight WGT as
the analytic weight (standard for SCF point estimates). Standard errors are NOT
multiple-imputation-corrected -- we report the decomposition (point estimates), not inference.

INTEGRITY GUARDRAIL (MANDATORY -- race-economics data):
  The Oaxaca-Blinder UNEXPLAINED component is NOT a measure of discrimination. It conflates
  discrimination with omitted variables, measurement error, and selection. We report it as
  "unexplained conditional on included covariates" -- never as "discrimination = X%."
  Decomposition identifies association, not causation. (Stratification economics -- Darity,
  Hamilton, Oliver & Shapiro -- notes that intergenerational wealth transmission is itself a
  mechanism the cross-section cannot fully capture.)
"""

from __future__ import annotations

import sys
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
OUT.mkdir(parents=True, exist_ok=True)

USE = ["RACE", "WGT", "NETWORTH", "INCOME", "EDCL", "AGE", "MARRIED", "KIDS",
       "HOUSECL", "FAMSTRUCT", "LF", "HOUSES", "FIN", "ASSET", "DEBT", "EQUITY",
       "NHEQUITY"] if False else ["RACE", "WGT", "NETWORTH", "INCOME", "EDCL", "AGE",
       "MARRIED", "KIDS", "HOUSECL", "FAMSTRUCT", "LF", "HOUSES", "FIN", "ASSET",
       "DEBT", "EQUITY"]


def build_X(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Build covariate design matrix with named columns. Reference cats dropped."""
    n = len(df)
    cols = []
    cols.append(("const", np.ones(n)))
    cols.append(("income_10k", (df["INCOME"].values / 1e4)))           # scale for numerics
    cols.append(("age", df["AGE"].values.astype(float)))
    cols.append(("age_sq", (df["AGE"].values.astype(float) ** 2) / 1e3))  # scale
    # EDCL: 1=no HS(ref),2=HS,3=some coll,4=degree
    for code, label in [(2, "edu_hs"), (3, "edu_somecoll"), (4, "edu_degree")]:
        cols.append((label, (df["EDCL"].values == code).astype(float)))
    cols.append(("homeowner", (df["HOUSECL"].values == 1).astype(float)))
    cols.append(("married", (df["MARRIED"].values == 1).astype(float)))
    cols.append(("kids", df["KIDS"].values.astype(float)))
    # FAMSTRUCT: 1-5; ref=1
    for code in [2, 3, 4, 5]:
        cols.append((f"famstruct_{code}", (df["FAMSTRUCT"].values == code).astype(float)))
    cols.append(("in_labor_force", (df["LF"].values == 1).astype(float)))
    names = [c[0] for c in cols]
    X = np.column_stack([c[1] for c in cols])
    return X, names


def wols(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted OLS: beta = (X'WX)^-1 X'Wy. Returns coefficient vector."""
    sw = np.sqrt(w)
    Xw = X * sw[:, None]
    yw = y * sw
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return beta


def wmean(v: np.ndarray, w: np.ndarray) -> float:
    return float((v * w).sum() / w.sum())


def decompose(df_w: pd.DataFrame, df_b: pd.DataFrame, ycol: str,
              transform=None) -> dict:
    """Oaxaca-Blinder with White reference. transform: None (levels) or 'log'."""
    Xw, names = build_X(df_w)
    Xb, _ = build_X(df_b)
    yw_raw = df_w[ycol].values.astype(float)
    yb_raw = df_b[ycol].values.astype(float)
    ww = df_w["WGT"].values.astype(float)
    wb = df_b["WGT"].values.astype(float)
    if transform == "log":
        yw = np.log(yw_raw)
        yb = np.log(yb_raw)
    else:
        yw = yw_raw
        yb = yb_raw

    bw = wols(Xw, yw, ww)   # White returns
    bb = wols(Xb, yb, wb)   # Black returns
    Xbar_w = np.array([wmean(Xw[:, j], ww) for j in range(Xw.shape[1])])
    Xbar_b = np.array([wmean(Xb[:, j], wb) for j in range(Xb.shape[1])])

    ybar_w = wmean(yw, ww)
    ybar_b = wmean(yb, wb)
    gap = ybar_w - ybar_b

    explained_total = float(np.dot(bw, Xbar_w - Xbar_b))
    unexplained_total = float(np.dot(bw - bb, Xbar_b))

    # per-covariate explained contributions
    explained_by = {names[j]: float(bw[j] * (Xbar_w[j] - Xbar_b[j]))
                    for j in range(len(names))}
    # fit metric (weighted R^2) for White model
    resid_w = yw - Xw @ bw
    ss_res = float((ww * resid_w ** 2).sum())
    ss_tot = float((ww * (yw - ybar_w) ** 2).sum())
    r2_w = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {
        "names": names, "ybar_w": ybar_w, "ybar_b": ybar_b, "gap": gap,
        "explained": explained_total, "unexplained": unexplained_total,
        "explained_by": explained_by, "bw": bw, "bb": bb,
        "Xbar_w": Xbar_w, "Xbar_b": Xbar_b, "r2_white": r2_w,
        "n_w": len(df_w), "n_b": len(df_b),
    }


def asset_composition(df_w, df_b) -> list[dict]:
    """Mean dollar gap by asset category (direct attribution, all households)."""
    cats = {"home_equity_HOUSES": "HOUSES", "financial_FIN": "FIN",
            "business_EQUITY": "EQUITY", "total_assets_ASSET": "ASSET",
            "debt_DEBT": "DEBT"}
    rows = []
    for label, col in cats.items():
        mw = wmean(df_w[col].values, df_w["WGT"].values)
        mb = wmean(df_b[col].values, df_b["WGT"].values)
        rows.append({"category": label, "white_mean": round(mw, 0),
                     "black_mean": round(mb, 0),
                     "gap_white_minus_black": round(mw - mb, 0),
                     "black_pct_of_white": round(100 * mb / mw, 1) if mw else None})
    return rows


def _load_scf_2022(cols):
    """Read the 2022 SCF summary .dta (fetched by L01) with UPPER-case columns."""
    dta = next((RAW / "scf" / "2022").rglob("*.dta"))
    df = pd.read_stata(dta, columns=[c.lower() for c in cols])
    df.columns = [str(c).upper() for c in df.columns]
    return df


def main() -> int:
    df = _load_scf_2022(USE)
    df["WGT"] = df["WGT"].astype(float)

    w = df[df["RACE"] == 1].copy()
    b = df[df["RACE"] == 2].copy()

    # ---- (A) LOG decomposition (positive net worth only) ----
    wpos = w[w["NETWORTH"] > 0]
    bpos = b[b["NETWORTH"] > 0]
    drop_w = 1 - len(wpos) / len(w)
    drop_b = 1 - len(bpos) / len(b)
    A = decompose(wpos, bpos, "NETWORTH", transform="log")

    # ---- (B) LEVELS decomposition (all households) ----
    B = decompose(w, b, "NETWORTH", transform=None)

    # ---- asset composition ----
    comp = asset_composition(w, b)

    # ===== console summary =====
    print("=" * 72)
    print("T2.1 BLACK-WHITE WEALTH-GAP DECOMPOSITION (SCF 2022)")
    print("=" * 72)
    print(f"\n[A] LOG net worth (positive-NW households; dropped {drop_w:.1%} White / "
          f"{drop_b:.1%} Black debtors)")
    print(f"    mean ln(NW) White = {A['ybar_w']:.3f}  Black = {A['ybar_b']:.3f}")
    print(f"    LOG GAP = {A['gap']:.3f}  (geometric-mean NW White ${np.exp(A['ybar_w']):,.0f} vs "
          f"Black ${np.exp(A['ybar_b']):,.0f}; ratio {np.exp(A['ybar_w'])/np.exp(A['ybar_b']):.2f}x = exp(gap) {np.exp(A['gap']):.2f}x)")
    print(f"    White-model coefficients (key): income_10k={A['bw'][1]:+.4f}/$10K  "
          f"edu_degree={A['bw'][6]:+.3f}  homeowner={A['bw'][7]:+.3f}  age={A['bw'][2]:+.3f}")
    print(f"    EXPLAINED   = {A['explained']:.3f}  ({100*A['explained']/A['gap']:.1f}% of gap)")
    print(f"    UNEXPLAINED = {A['unexplained']:.3f}  ({100*A['unexplained']/A['gap']:.1f}% of gap)")
    print(f"    (decomposition residual from rounding: {A['gap']-A['explained']-A['unexplained']:.4f})")
    print(f"    White-model weighted R^2 = {A['r2_white']:.3f}")
    print("    Per-covariate EXPLAINED contribution (% of explained):")
    tot = sum(v for v in A["explained_by"].values())
    for name, val in sorted(A["explained_by"].items(), key=lambda kv: -abs(kv[1])):
        if abs(val) < 1e-4:
            continue
        print(f"      {name:<18} {val:>+7.3f}  ({100*val/A['gap']:+5.1f}% of gap)")

    print(f"\n[B] LEVELS net worth at the mean (ALL households; tail-dominated)")
    print(f"    mean NW White = ${B['ybar_w']:,.0f}  Black = ${B['ybar_b']:,.0f}")
    print(f"    DOLLAR GAP = ${B['gap']:,.0f}")
    print(f"    EXPLAINED   = ${B['explained']:,.0f}  ({100*B['explained']/B['gap']:.1f}% of gap)")
    print(f"    UNEXPLAINED = ${B['unexplained']:,.0f}  ({100*B['unexplained']/B['gap']:.1f}% of gap)")
    print(f"    (mean >> median gap $222K because mean is right-tail dominated)")

    print("\n[C] Asset-composition mean gap (all households, dollars):")
    for r in comp:
        print(f"    {r['category']:<22} White ${r['white_mean']:>13,.0f}  "
              f"Black ${r['black_mean']:>13,.0f}  gap ${r['gap_white_minus_black']:>+13,.0f}  "
              f"({r['black_pct_of_white']}% of White)")

    # ===== write outputs =====
    # main decomposition CSV
    rows = []
    for label, d, gap in [("A_log", A, A["gap"]), ("B_levels", B, B["gap"])]:
        rows.append({"spec": label, "metric": "gap", "value": round(d["gap"], 4)})
        rows.append({"spec": label, "metric": "explained", "value": round(d["explained"], 4),
                     "pct_of_gap": round(100 * d["explained"] / gap, 1)})
        rows.append({"spec": label, "metric": "unexplained", "value": round(d["unexplained"], 4),
                     "pct_of_gap": round(100 * d["unexplained"] / gap, 1)})
        rows.append({"spec": label, "metric": "white_model_r2", "value": round(d["r2_white"], 4)})
    for name, val in A["explained_by"].items():
        if abs(val) > 1e-4:
            rows.append({"spec": "A_log_per_covariate", "metric": name,
                         "value": round(val, 4),
                         "pct_of_gap": round(100 * val / A["gap"], 1)})
    for name, val in B["explained_by"].items():
        if abs(val) > 1e-4:
            rows.append({"spec": "B_levels_per_covariate", "metric": name,
                         "value": round(val, 2),
                         "pct_of_gap": round(100 * val / B["gap"], 1)})
    main_csv = OUT / "wealth_gap_decomposition.csv"
    pd.DataFrame(rows).to_csv(main_csv, index=False)
    print(f"\nWrote {main_csv}")

    comp_csv = OUT / "wealth_asset_composition.csv"
    pd.DataFrame(comp).to_csv(comp_csv, index=False)
    print(f"Wrote {comp_csv}")

    # methodology markdown
    md = OUT / "wealth_decomposition_methodology.md"
    md.write_text(_methodology_md(A, B, comp, drop_w, drop_b), encoding="utf-8")
    print(f"Wrote {md}")
    return 0


def _methodology_md(A, B, comp, drop_w, drop_b) -> str:
    L = []
    L.append("# T2.1 — Black–White Wealth-Gap Decomposition (SCF 2022)\n")
    L.append("*Oaxaca–Blinder decomposition of the Panel 1 headline finding. "
             "Moves the wealth gap from a descriptive ratio (18.2% median) to a "
             "decomposed explanation of *how much* of the gap is accounted for by "
             "observed covariates.*\n")
    L.append("## Method\n")
    L.append("Oaxaca–Blinder decomposition with **White as the reference group**, on Fed SCF "
             "2022 household-level microdata (5 implicates, weighted by `WGT`). Two specifications "
             "are reported together for honesty about wealth skewness:\n")
    L.append("- **(A) Log net worth** — standard wealth-gap-literature approach; drops households "
             f"with NETWORTH ≤ 0 (debtors: {drop_w:.1%} of White, {drop_b:.1%} of Black). "
             "Gap measured in log points and reported as % of the gap.\n")
    L.append("- **(B) Levels net worth at the mean** — all households; dollar decomposition. "
             "Tail-dominated (mean gap ≫ median gap $222K), flagged accordingly.\n")
    L.append("**Covariates**: household income, age (+age²), education (4-category), homeownership, "
             "marital status, number of children, family structure, labor-force status.\n")
    L.append("**Decomposition identity**: gap = explained [(X̄_W − X̄_B)·β̂_W] + unexplained "
             "[(β̂_W − β̂_B)·X̄_B]. 'Explained' = the portion due to Black households having "
             "different (lower) covariates, valued at White returns. 'Unexplained' = the portion "
             "due to Black households receiving different returns for the *same* covariates.\n")
    L.append("## Results\n")
    L.append(f"**(A) Log decomposition** — log gap = {A['gap']:.3f} → "
             f"**explained {100*A['explained']/A['gap']:.0f}%** / "
             f"**unexplained {100*A['unexplained']/A['gap']:.0f}%** "
             f"(White-model weighted R² = {A['r2_white']:.2f}).\n")
    L.append("Largest explained contributors (covariate differences valued at White returns):\n")
    L.append("| Covariate | Contribution to log gap | % of gap |\n|---|---:|---:|\n")
    for name, val in sorted(A["explained_by"].items(), key=lambda kv: -abs(kv[1])):
        if abs(val) < 1e-3:
            continue
        L.append(f"| {name} | {val:+.3f} | {100*val/A['gap']:+.1f}% |\n")
    L.append(f"\n**(B) Levels decomposition** — dollar gap = ${B['gap']:,.0f} → "
             f"**explained ${B['explained']:,.0f} ({100*B['explained']/B['gap']:.0f}%)** / "
             f"**unexplained ${B['unexplained']:,.0f} ({100*B['unexplained']/B['gap']:.0f}%)**.\n")
    L.append("## Asset-composition mean gap\n")
    L.append("| Category | White mean | Black mean | Gap (W−B) | Black % of White |\n"
             "|---|---:|---:|---:|---:|\n")
    for r in comp:
        L.append(f"| {r['category']} | ${r['white_mean']:,.0f} | ${r['black_mean']:,.0f} | "
                 f"${r['gap_white_minus_black']:+,.0f} | {r['black_pct_of_white']}% |\n")
    L.append("\n## Integrity guardrail (read this)\n")
    L.append("The **unexplained** component is **not** a measure of discrimination. It conflates "
             "discrimination with omitted variables, measurement error, and selection into the "
             "covariates themselves (e.g., income is itself partly an *outcome* of race). We report "
             "it strictly as *unexplained conditional on the included covariates.* The "
             "stratification-economics tradition (Darity, Hamilton, Oliver & Shapiro) emphasizes that "
             "intergenerational wealth transmission is a mechanism a single cross-section cannot "
             "fully capture. These results identify **associations**, not causal effects.\n")
    L.append("## Known limits\n")
    L.append("- 2022 cross-section only; the decomposition's explained/unexplained split can shift "
             "across SCF waves (v2: replicate 1989–2019).\n")
    L.append("- Log spec excludes debtor households (negative net worth); documented above.\n")
    L.append("- Standard errors are not multiple-imputation-corrected; we report point estimates, "
             "not inference.\n")
    L.append("- No wealth-region/MSA controls (SCF geography is coarse); segregation effects "
             "captured only indirectly via income/homeownership.\n")
    return "".join(L)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as e:
        print(f"ERROR: SCF source not found: {e}", file=sys.stderr)
        raise SystemExit(1)
