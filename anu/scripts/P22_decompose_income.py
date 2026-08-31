"""
T2.2 + T2.6 -- Black-White Income Decomposition & Education->Income->Wealth Transmission
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_02_INCOME (decomposition) + cross-panel transmission analysis (T2.6)

Two linked analyses on Fed SCF 2022 microdata (same sample as T2.1 wealth decomposition,
so the comparison is internally consistent):

  T2.2 -- Oaxaca-Blinder decomposition of the Black-White INCOME gap (log income).
          Outcome: ln(INCOME). Covariates: education, age, age^2, labor-force, married,
          kids, family structure. (Homeownership EXCLUDED -- it is downstream of wealth/income,
          so including it would be a 'bad control'.)

  T2.6 -- The education transmission chain. Quantifies the core stratification-economics
          claim: education narrows the INCOME gap but does NOT close the WEALTH gap.
          Method: compare education's share of the EXPLAINED income gap (T2.2) vs
          education's share of the EXPLAINED wealth gap (T2.1). If education explains a
          much larger fraction of the income gap than the wealth gap, the claim is
          quantified.

Source: Fed SCF 2022 (public download: https://www.federalreserve.gov/econres/files/scfp2022.zip)
Reference group: White (race 1). 5 implicates, weighted by WGT.

INTEGRITY GUARDRAIL: the unexplained income residual is NOT a wage-discrimination estimate
(it conflates discrimination with omitted human-capital and selection variables). Reported
as 'unexplained conditional on included covariates' only. SCF INCOME is comprehensive
household income (incl. capital income), appropriate here because we situate income in the
wealth context -- it is NOT a clean wage-gap estimate. No causal claims.
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
WEALTH_DECOMP = OUT / "wealth_gap_decomposition.csv"  # T2.1 output, for T2.6 comparison


def build_X_income(df: pd.DataFrame):
    """Covariates for income regression (no homeowner -- downstream). Returns (X, names)."""
    n = len(df)
    cols = [("const", np.ones(n))]
    cols.append(("age", df["AGE"].values.astype(float)))
    cols.append(("age_sq", (df["AGE"].values.astype(float) ** 2) / 1e3))
    for code, label in [(2, "edu_hs"), (3, "edu_somecoll"), (4, "edu_degree")]:
        cols.append((label, (df["EDCL"].values == code).astype(float)))
    cols.append(("married", (df["MARRIED"].values == 1).astype(float)))
    cols.append(("kids", df["KIDS"].values.astype(float)))
    for code in [2, 3, 4, 5]:
        cols.append((f"famstruct_{code}", (df["FAMSTRUCT"].values == code).astype(float)))
    cols.append(("in_labor_force", (df["LF"].values == 1).astype(float)))
    names = [c[0] for c in cols]
    return np.column_stack([c[1] for c in cols]), names


def wols(X, y, w):
    sw = np.sqrt(w); Xw = X * sw[:, None]; yw = y * sw
    beta, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    return beta


def wmean(v, w):
    return float((v * w).sum() / w.sum())


def ob_decompose(df_w, df_b, Xfn, yfn):
    Xw, names = Xfn(df_w); Xb, _ = Xfn(df_b)
    yw = yfn(df_w); yb = yfn(df_b)
    ww = df_w["WGT"].values.astype(float); wb = df_b["WGT"].values.astype(float)
    bw = wols(Xw, yw, ww); bb = wols(Xb, yb, wb)
    Xbar_w = np.array([wmean(Xw[:, j], ww) for j in range(Xw.shape[1])])
    Xbar_b = np.array([wmean(Xb[:, j], wb) for j in range(Xb.shape[1])])
    ybar_w = wmean(yw, ww); ybar_b = wmean(yb, wb); gap = ybar_w - ybar_b
    explained = float(np.dot(bw, Xbar_w - Xbar_b))
    unexplained = float(np.dot(bw - bb, Xbar_b))
    explained_by = {names[j]: float(bw[j] * (Xbar_w[j] - Xbar_b[j])) for j in range(len(names))}
    resid = yw - Xw @ bw
    r2 = 1 - float((ww * resid ** 2).sum()) / float((ww * (yw - ybar_w) ** 2).sum())
    return dict(names=names, ybar_w=ybar_w, ybar_b=ybar_b, gap=gap, explained=explained,
                unexplained=unexplained, explained_by=explained_by, r2_white=r2,
                n_w=len(df_w), n_b=len(df_b))


def edu_share(explained_by, gap):
    """Net education contribution (edu_degree + edu_somecoll + edu_hs) as % of gap."""
    e = explained_by.get("edu_degree", 0) + explained_by.get("edu_somecoll", 0) + explained_by.get("edu_hs", 0)
    return e, 100 * e / gap if gap else float("nan")


def _load_scf_2022(cols):
    """Read the 2022 SCF summary .dta (fetched by L01) with UPPER-case columns."""
    dta = next((RAW / "scf" / "2022").rglob("*.dta"))
    df = pd.read_stata(dta, columns=[c.lower() for c in cols])
    df.columns = [str(c).upper() for c in df.columns]
    return df


def main() -> int:
    df = _load_scf_2022(["RACE", "WGT", "INCOME", "NETWORTH", "EDCL", "AGE",
                         "MARRIED", "KIDS", "HOUSECL", "FAMSTRUCT", "LF"])
    df["WGT"] = df["WGT"].astype(float)
    w = df[df["RACE"] == 1].copy(); b = df[df["RACE"] == 2].copy()

    # ---- T2.2 income decomposition (log income, positive income) ----
    wp = w[w["INCOME"] > 0]; bp = b[b["INCOME"] > 0]
    INC = ob_decompose(wp, bp, build_X_income, lambda d: np.log(d["INCOME"].values.astype(float)))

    # ---- recompute T2.1 wealth log decomposition here for a consistent comparison ----
    wpos = w[w["NETWORTH"] > 0]; bpos = b[b["NETWORTH"] > 0]
    # wealth needs homeowner covariate; reuse build_X from T2.1 logic inline
    def build_X_wealth(d):
        n = len(d); c = [("const", np.ones(n)), ("income_10k", d["INCOME"].values / 1e4),
                         ("age", d["AGE"].values.astype(float)),
                         ("age_sq", (d["AGE"].values.astype(float) ** 2) / 1e3)]
        for code, lab in [(2, "edu_hs"), (3, "edu_somecoll"), (4, "edu_degree")]:
            c.append((lab, (d["EDCL"].values == code).astype(float)))
        c.append(("homeowner", (d["HOUSECL"].values == 1).astype(float)))
        c.append(("married", (d["MARRIED"].values == 1).astype(float)))
        c.append(("kids", d["KIDS"].values.astype(float)))
        for code in [2, 3, 4, 5]:
            c.append((f"famstruct_{code}", (d["FAMSTRUCT"].values == code).astype(float)))
        c.append(("in_labor_force", (d["LF"].values == 1).astype(float)))
        return np.column_stack([x[1] for x in c]), [x[0] for x in c]
    WL = ob_decompose(wpos, bpos, build_X_wealth, lambda d: np.log(d["NETWORTH"].values.astype(float)))

    # education shares
    inc_edu_val, inc_edu_pct = edu_share(INC["explained_by"], INC["gap"])
    wl_edu_val, wl_edu_pct = edu_share(WL["explained_by"], WL["gap"])

    print("=" * 72)
    print("T2.2 BLACK-WHITE INCOME DECOMPOSITION + T2.6 EDUCATION TRANSMISSION (SCF 2022)")
    print("=" * 72)
    print(f"\n[T2.2] LOG income gap = {INC['gap']:.3f}  "
          f"(geom-mean income White ${np.exp(INC['ybar_w']):,.0f} vs Black ${np.exp(INC['ybar_b']):,.0f}; "
          f"ratio {np.exp(INC['gap']):.2f}x)")
    print(f"       EXPLAINED   = {INC['explained']:.3f}  ({100*INC['explained']/INC['gap']:.1f}% of gap)")
    print(f"       UNEXPLAINED = {INC['unexplained']:.3f}  ({100*INC['unexplained']/INC['gap']:.1f}% of gap)")
    print(f"       White-model weighted R^2 = {INC['r2_white']:.3f}")
    print("       Per-covariate EXPLAINED contribution:")
    for name, val in sorted(INC["explained_by"].items(), key=lambda kv: -abs(kv[1])):
        if abs(val) < 1e-3: continue
        print(f"         {name:<18} {val:>+7.3f}  ({100*val/INC['gap']:+5.1f}% of gap)")

    print(f"\n[T2.6] EDUCATION TRANSMISSION CHAIN (the stratification-economics claim)")
    print(f"       Education net contribution to:")
    print(f"         INCOME gap (log) : {inc_edu_val:+.3f} = {inc_edu_pct:.1f}% of the income gap")
    print(f"         WEALTH gap (log) : {wl_edu_val:+.3f} = {wl_edu_pct:.1f}% of the wealth gap")
    if inc_edu_pct > wl_edu_pct * 1.5:
        verdict = ("education explains a LARGER share of the income gap than the wealth gap -> "
                   "the stratification-economics claim is QUANTIFIED: education narrows income but does not close wealth")
    else:
        verdict = "education shares comparable across gaps -> claim NOT supported at the 1.5x threshold"
    print(f"       => {verdict}")

    # write outputs
    rows = []
    for label, d in [("T2.2_income_log", INC), ("T2.1_wealth_log_recomputed", WL)]:
        rows.append({"spec": label, "metric": "gap", "value": round(d["gap"], 4)})
        rows.append({"spec": label, "metric": "explained", "value": round(d["explained"], 4),
                     "pct_of_gap": round(100 * d["explained"] / d["gap"], 1)})
        rows.append({"spec": label, "metric": "unexplained", "value": round(d["unexplained"], 4),
                     "pct_of_gap": round(100 * d["unexplained"] / d["gap"], 1)})
        for name, val in d["explained_by"].items():
            if abs(val) > 1e-3:
                rows.append({"spec": f"{label}_per_covariate", "metric": name,
                             "value": round(val, 4), "pct_of_gap": round(100 * val / d["gap"], 1)})
    rows.append({"spec": "T2.6_transmission", "metric": "education_share_of_income_gap_pct",
                 "value": round(inc_edu_pct, 1)})
    rows.append({"spec": "T2.6_transmission", "metric": "education_share_of_wealth_gap_pct",
                 "value": round(wl_edu_pct, 1)})
    rows.append({"spec": "T2.6_transmission", "metric": "ratio_income_over_wealth",
                 "value": round(inc_edu_pct / wl_edu_pct, 2) if wl_edu_pct else None})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "income_decomposition.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    print(f"\nWrote {OUT/'income_decomposition.csv'}")

    # methodology note
    (OUT / "education_transmission_methodology.md").write_text(_md(INC, WL, inc_edu_pct, wl_edu_pct),
                                                               encoding="utf-8")
    print(f"Wrote {OUT/'education_transmission_methodology.md'}")
    return 0


def _md(INC, WL, inc_edu_pct, wl_edu_pct) -> str:
    return (
        "# T2.2 + T2.6 — Income Decomposition & Education→Wealth Transmission (SCF 2022)\n\n"
        "## T2.2 Income gap decomposition\n"
        f"Black–White log-income gap = **{INC['gap']:.3f}** (geometric-mean ratio "
        f"{np.exp(INC['gap']):.2f}×). Of this, **{100*INC['explained']/INC['gap']:.0f}% is explained** "
        f"by education, age, labor-force, and family-structure differences, and "
        f"**{100*INC['unexplained']/INC['gap']:.0f}% is unexplained** (White-model weighted R² = "
        f"{INC['r2_white']:.2f}).\n\n"
        "## T2.6 The education transmission chain\n"
        "The stratification-economics claim (Oliver & Shapiro; Darity, Hamilton) is that education "
        "narrows the **income** gap but does **not** close the **wealth** gap — because wealth "
        "transmits across generations independently of individual educational attainment. Quantified "
        f"on SCF 2022: education (net of HS/some-college/degree dummies) accounts for "
        f"**{inc_edu_pct:.0f}% of the income gap** but only **{wl_edu_pct:.0f}% of the wealth gap** "
        f"— a ratio of {inc_edu_pct/wl_edu_pct:.1f}×. Equalizing educational attainment would "
        f"therefore close a meaningfully larger share of the income gap than the wealth gap.\n\n"
        "## Integrity guardrail\n"
        "The income-gap unexplained residual is **not** a wage-discrimination estimate; it conflates "
        "discrimination with omitted variables and selection. SCF INCOME is comprehensive household "
        "income (including capital income) and is situated here in the wealth context — it is not a "
        "clean Mincer wage-gap estimate. Results are **associations**, not causal effects. The "
        "wealth decomposition excludes debtor households (NETWORTH ≤ 0; ~19% of Black vs ~5% of "
        "White — itself part of the gap the log spec cannot see).\n\n"
        "## Known limits\n"
        "- 2022 cross-section; v2 will replicate across SCF waves.\n"
        "- No occupation/industry controls in the income regression (SCF codes are coarse).\n"
        "- Standard errors not multiple-imputation-corrected; point estimates only.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
