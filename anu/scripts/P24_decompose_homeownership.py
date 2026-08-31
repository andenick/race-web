"""
T2.4 -- Black-White Homeownership-Gap Decomposition
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_05_HOUSING

Oaxaca-Blinder on a linear-probability model of homeownership (SCF HOUSECL==1), SCF 2022.
Decomposes the ~25pp Black-White homeownership-rate gap into explained contributions
(income, age, education, family structure, labor force) and an unexplained residual.

Why LPM-OB (not Fairlie): the linear-probability Oaxaca-Blinder at the mean is a standard,
interpretable approximation for binary outcomes; the explained terms read directly in
percentage-points. (A nonlinear Fairlie/KHB refinement is a v2 option.) The SCF HOUSECL
homeowner measure is self-reported primary-residence ownership.

Outcome: 1 if HOUSECL==1. Reference group: White (race 1). 5 implicates, weighted by WGT.
Covariates: income, age, age^2, education, married, kids, family structure, labor force.
(Net worth EXCLUDED -- it is downstream of homeownership, a 'bad control'.)

INTEGRITY GUARDRAIL: unexplained residual is NOT a discrimination estimate; it conflates
discrimination with credit-access, geography, and omitted variables. Reported as
'unexplained conditional on included covariates'. Associations, not causal effects.
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


def build_X(df):
    n = len(df); c = [("const", np.ones(n)), ("income_10k", df["INCOME"].values / 1e4),
                      ("age", df["AGE"].values.astype(float)),
                      ("age_sq", (df["AGE"].values.astype(float) ** 2) / 1e3)]
    for code, lab in [(2, "edu_hs"), (3, "edu_somecoll"), (4, "edu_degree")]:
        c.append((lab, (df["EDCL"].values == code).astype(float)))
    c.append(("married", (df["MARRIED"].values == 1).astype(float)))
    c.append(("kids", df["KIDS"].values.astype(float)))
    for code in [2, 3, 4, 5]:
        c.append((f"famstruct_{code}", (df["FAMSTRUCT"].values == code).astype(float)))
    c.append(("in_labor_force", (df["LF"].values == 1).astype(float)))
    return np.column_stack([x[1] for x in c]), [x[0] for x in c]


def wols(X, y, w):
    sw = np.sqrt(w); beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None); return beta


def wmean(v, w): return float((v * w).sum() / w.sum())


def _load_scf_2022(cols):
    """Read the 2022 SCF summary .dta (fetched by L01) with UPPER-case columns."""
    dta = next((RAW / "scf" / "2022").rglob("*.dta"))
    df = pd.read_stata(dta, columns=[c.lower() for c in cols])
    df.columns = [str(c).upper() for c in df.columns]
    return df


def main() -> int:
    df = _load_scf_2022(["RACE", "WGT", "INCOME", "EDCL", "AGE", "MARRIED", "KIDS",
                         "HOUSECL", "FAMSTRUCT", "LF"])
    df["WGT"] = df["WGT"].astype(float)
    w = df[df["RACE"] == 1]; b = df[df["RACE"] == 2]
    Xw, names = build_X(w); Xb, _ = build_X(b)
    yw = (w["HOUSECL"].values == 1).astype(float)
    yb = (b["HOUSECL"].values == 1).astype(float)
    ww = w["WGT"].values; wb = b["WGT"].values
    bw = wols(Xw, yw, ww); bb = wols(Xb, yb, wb)
    Xbar_w = np.array([wmean(Xw[:, j], ww) for j in range(Xw.shape[1])])
    Xbar_b = np.array([wmean(Xb[:, j], wb) for j in range(Xb.shape[1])])
    rate_w = wmean(yw, ww); rate_b = wmean(yb, wb)
    gap = rate_w - rate_b  # in pp (fraction)
    explained = float(np.dot(bw, Xbar_w - Xbar_b))
    unexplained = float(np.dot(bw - bb, Xbar_b))
    resid_w = yw - Xw @ bw
    r2 = 1 - float((ww * resid_w ** 2).sum()) / float((ww * (yw - rate_w) ** 2).sum())

    print("=" * 72)
    print("T2.4 BLACK-WHITE HOMEOWNERSHIP-GAP DECOMPOSITION (SCF 2022, LPM-Oaxaca-Blinder)")
    print("=" * 72)
    print(f"\nHomeownership rate: White {100*rate_w:.1f}%  Black {100*rate_b:.1f}%  "
          f"GAP = {100*gap:.1f}pp")
    print(f"EXPLAINED   = {100*explained:.1f}pp  ({100*explained/gap:.0f}% of gap)")
    print(f"UNEXPLAINED = {100*unexplained:.1f}pp  ({100*unexplained/gap:.0f}% of gap)")
    print(f"White-model weighted R^2 = {r2:.3f}")
    print("Per-covariate EXPLAINED contribution (pp of the gap):")
    rows = []
    for j, name in enumerate(names):
        val = float(bw[j] * (Xbar_w[j] - Xbar_b[j]))
        if abs(val) < 1e-4: continue
        print(f"  {name:<18} {100*val:+6.2f}pp  ({100*val/gap:+5.1f}% of gap)")
        rows.append({"metric": name, "value_pp": round(100 * val, 3),
                     "pct_of_gap": round(100 * val / gap, 1)})
    rows.append({"metric": "gap_pp", "value_pp": round(100 * gap, 2)})
    rows.append({"metric": "explained_pp", "value_pp": round(100 * explained, 2),
                 "pct_of_gap": round(100 * explained / gap, 1)})
    rows.append({"metric": "unexplained_pp", "value_pp": round(100 * unexplained, 2),
                 "pct_of_gap": round(100 * unexplained / gap, 1)})
    rows.append({"metric": "white_ownership_rate", "value_pp": round(100 * rate_w, 2)})
    rows.append({"metric": "black_ownership_rate", "value_pp": round(100 * rate_b, 2)})
    rows.append({"metric": "white_model_r2", "value_pp": round(r2, 4)})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "homeownership_decomposition.csv").write_text(
        pd.DataFrame(rows).to_csv(index=False), encoding="utf-8")
    print(f"\nWrote {OUT/'homeownership_decomposition.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
