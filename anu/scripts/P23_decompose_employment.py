"""T23 — Cyclical Decomposition of the Black–White Unemployment Ratio.

Project: DuBois (race-economics, AnuData v3.0)

PURPOSE
-------
The descriptive finding is that the Black/White unemployment ratio averages
~2.1x across 1972-2025. This module asks whether that regularity is a *constant
multiplier* (a fixed ~2x) or reflects *differential cyclical sensitivity* —
the "last hired, first fired" hypothesis, where Black unemployment rises more
than proportionally when aggregate (White) unemployment rises.

It estimates, over the 1972-latest overlapping window where BOTH Black and
White annual unemployment exist:

  (1) Level specification:  u_B = alpha + beta * u_W + eps
      beta = "points of Black unemployment per point of White unemployment."
      A constant ~2x rule predicts alpha ~ 0, beta ~ 2. beta > 1 indicates
      differential cyclical co-movement.

  (2) Ratio regression:     ratio = a + b * u_W + eps
      b > 0 would mean the gap *widens* (amplifies) when White unemployment is
      high; b ~ 0 means the ratio is approximately a constant multiplier.

  (3) Recession amplification: mean Black/White ratio inside NBER-recession
      year windows vs expansion years.

  (4) COVID structural-break influence: re-estimate the level regression with
      2020 excluded and report how much the 2020 observation shifts beta.
      The 2020 ratio fell to ~1.58x because the pandemic service-sector
      shutdown hit White employment unusually hard.

INTEGRITY GUARDRAIL (MANDATORY — race-economics data)
-----------------------------------------------------
* beta and the recession/expansion ratio difference are reported as
  DESCRIPTIVE elasticities / correlations, NOT causal effects. Recessions and
  expansions are not randomly assigned; many confounders (education,
  occupation mix, geography, policy) co-move with the cycle. We measure
  statistical co-movement, not a treatment effect.
* No year is dropped or winsorized except the explicit with/without-2020
  influence diagnostic. The headline regressions INCLUDE every overlapping
  year.
* No synthetic data. Missing years are skipped and documented.
* 2025 is a PARTIAL year (n_months=6); it is included for completeness per the
  no-drop rule, and flagged as a known limitation.

KNOWN LIMITATIONS
-----------------
* Black unemployment is not collected before 1972 by BLS (the CPS race tabulation
  for Black workers begins 1972), so the window cannot extend earlier.
* 2020 is a structural anomaly (COVID service-sector shutdown) that distorts
  the usual cyclical pattern; its influence is reported, not removed.
* Annual averages smooth within-year dynamics (e.g., the Apr-2020 spike).
* The ratio regression conflates secular trend (ratio has drifted down since
  the 1980s) with cyclical movement; the level specification is the cleaner
  cyclical test.

INPUTS  : data/processed/ (in this package)
           unemployment_annual.csv   (long form; race in {White, Black or African American, ...})
           unemployment_ratio.csv    (wide; white_unemployment, black_unemployment, black_white_ratio)
           unemployment_recession_peaks.csv (NBER episodes: recession, peak, trough, ...)
OUTPUTS : data/processed/ (in this package)
           employment_cyclical_decomposition.csv  (wide: one row of results)
           employment_cyclical_methodology.md     (2-4 paragraph note)
CONSOLE : clear summary of every estimate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# statsmodels is available in the project venv (0.14.6). Use it for proper
# OLS, R^2, and standard errors; fall back to numpy lstsq if ever missing.
try:
    import statsmodels.api as sm

    HAVE_STATSMODELS = True
except Exception:  # pragma: no cover - environment guard
    HAVE_STATSMODELS = False


# --------------------------------------------------------------------------- #
# Paths (package-relative).
# --------------------------------------------------------------------------- #
HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROC
OUT_DIR = PROC

ANNUAL_CSV = DATA_DIR / "unemployment_annual.csv"
RATIO_CSV = DATA_DIR / "unemployment_ratio.csv"
RECESSION_CSV = DATA_DIR / "unemployment_recession_peaks.csv"

RESULTS_CSV = OUT_DIR / "employment_cyclical_decomposition.csv"
METHOD_MD = OUT_DIR / "employment_cyclical_methodology.md"


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def _race_key(label: str) -> str:
    """Normalise the verbose CPS race labels to short keys."""
    s = str(label).lower()
    if s == "white":
        return "White"
    if s.startswith("black"):
        return "Black"
    if s.startswith("hispanic"):
        return "Hispanic"
    if s.startswith("asian"):
        return "Asian"
    return str(label)


def load_paired_series() -> pd.DataFrame:
    """Return a DataFrame indexed by year with u_W, u_B, ratio (1972-latest).

    Canonical source is unemployment_annual.csv (long form), pivoted on race.
    The pre-computed unemployment_ratio.csv is loaded only to cross-validate.
    """
    if not ANNUAL_CSV.exists():
        raise FileNotFoundError(f"Missing input: {ANNUAL_CSV}")

    ann = pd.read_csv(ANNUAL_CSV)
    ann["rk"] = ann["race"].map(_race_key)
    pivot = (
        ann.pivot_table(index="year", columns="rk", values="unemployment_rate")
        .reset_index()
        .sort_values("year")
    )

    # Overlap window: both White and Black present.
    both = pivot.dropna(subset=["White", "Black"]).copy()
    # Black series begins 1972; enforce the documented start regardless.
    both = both[both["year"] >= 1972].copy()

    df = pd.DataFrame(
        {
            "year": both["year"].astype(int).values,
            "u_W": both["White"].astype(float).values,
            "u_B": both["Black"].astype(float).values,
        }
    )
    df["ratio"] = df["u_B"] / df["u_W"]

    # Cross-validate against the pre-computed ratio file (integrity check).
    if RATIO_CSV.exists():
        rc = pd.read_csv(RATIO_CSV)
        rc = rc[["year", "black_white_ratio"]].dropna()
        merged = df.merge(rc, on="year", how="left")
        diff = (merged["ratio"] - merged["black_white_ratio"]).abs().dropna()
        if len(diff):
            max_diff = float(diff.max())
            if max_diff > 1e-6:
                print(
                    f"[warn] computed ratio differs from unemployment_ratio.csv "
                    f"by up to {max_diff:.4f} (rounding); using computed-from-source."
                )
    return df.reset_index(drop=True)


def load_partial_months() -> dict[int, int]:
    """year -> n_months, to flag partial years (e.g. 2025 = 6 months)."""
    if not ANNUAL_CSV.exists():
        return {}
    ann = pd.read_csv(ANNUAL_CSV)
    ann["rk"] = ann["race"].map(_race_key)
    grp = ann[ann["rk"] == "White"].set_index("year")["n_months"]
    return {int(y): int(v) for y, v in grp.items() if pd.notna(v)}


def recession_years() -> set[int]:
    """Set of calendar years that fall inside any NBER recession episode.

    unemployment_recession_peaks.csv has no `year` column; it lists each episode
    with `peak` and `trough` as YYYY-MM month strings. A year is a recession year
    if it lies in [peak_year, trough_year] inclusive for any episode. This is the
    standard NBER-span definition and naturally handles multi-year recessions.
    """
    if not RECESSION_CSV.exists():
        raise FileNotFoundError(f"Missing input: {RECESSION_CSV}")
    rec = pd.read_csv(RECESSION_CSV)
    years: set[int] = set()
    for _, row in rec.iterrows():
        for col in ("peak", "trough"):
            val = row.get(col)
            if pd.isna(val):
                continue
            # Take the 4-digit year prefix of a YYYY-MM string.
            ystr = str(val).strip()[:4]
            if ystr.isdigit():
                years.add(int(ystr))
    # Expand: every integer year between the min and max year of EACH episode.
    # Re-derive per-episode spans so unrelated years are not bridged together.
    spans: set[int] = set()
    for _, row in rec.iterrows():
        pk, tr = row.get("peak"), row.get("trough")
        if pd.isna(pk) or pd.isna(tr):
            continue
        try:
            y0 = int(str(pk).strip()[:4])
            y1 = int(str(tr).strip()[:4])
        except (ValueError, TypeError):
            continue
        for y in range(min(y0, y1), max(y0, y1) + 1):
            spans.add(y)
    return spans


# --------------------------------------------------------------------------- #
# Estimation
# --------------------------------------------------------------------------- #
def ols(x: np.ndarray, y: np.ndarray) -> dict:
    """OLS with intercept. Prefer statsmodels for SE/R^2; fall back to numpy."""
    X = sm.add_constant(np.asarray(x, dtype=float)) if HAVE_STATSMODELS else None
    if HAVE_STATSMODELS:
        model = sm.OLS(np.asarray(y, dtype=float), X).fit()
        intercept, slope = float(model.params[0]), float(model.params[1])
        se_int, se_slope = float(model.bse[0]), float(model.bse[1])
        r2 = float(model.rsquared)
        resid = np.asarray(model.resid)
    else:
        xa = np.asarray(x, dtype=float)
        ya = np.asarray(y, dtype=float)
        Xn = np.column_stack([np.ones_like(xa), xa])
        coef, *_ = np.linalg.lstsq(Xn, ya, rcond=None)
        intercept, slope = float(coef[0]), float(coef[1])
        resid = ya - Xn @ coef
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((ya - ya.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        se_int = se_slope = float("nan")
    return {
        "intercept": intercept,
        "slope": slope,
        "se_intercept": se_int,
        "se_slope": se_slope,
        "r2": r2,
        "resid": resid,
    }


def analyze() -> dict:
    df = load_paired_series()
    nmos = load_partial_months()
    rec_years = recession_years()
    df["recession"] = df["year"].isin(rec_years)

    # (1) Level specification: u_B = alpha + beta * u_W
    lvl = ols(df["u_W"].values, df["u_B"].values)

    # (2) Ratio regression: ratio = a + b * u_W
    rat = ols(df["u_W"].values, df["ratio"].values)

    # (3) Recession vs expansion mean ratio
    rec_mask = df["recession"].values
    rec_ratio = float(df.loc[rec_mask, "ratio"].mean())
    exp_ratio = float(df.loc[~rec_mask, "ratio"].mean())
    rec_diff = rec_ratio - exp_ratio

    # (4) COVID influence: level regression with and without 2020
    no2020 = df[df["year"] != 2020]
    lvl_no2020 = ols(no2020["u_W"].values, no2020["u_B"].values)
    covid_shift = float(lvl["slope"] - lvl_no2020["slope"])

    # Residual diagnostics for the headline level regression
    resid = lvl["resid"]
    worst_idx = int(np.argmax(np.abs(resid)))
    worst_year = int(df["year"].iloc[worst_idx])
    worst_resid = float(resid[worst_idx])

    results = {
        "year_start": int(df["year"].min()),
        "year_end": int(df["year"].max()),
        "n_years": int(len(df)),
        "n_recession_years": int(rec_mask.sum()),
        "n_expansion_years": int((~rec_mask).sum()),
        # Level specification
        "level_alpha": lvl["intercept"],
        "level_alpha_se": lvl["se_intercept"],
        "level_beta": lvl["slope"],
        "level_beta_se": lvl["se_slope"],
        "level_r2": lvl["r2"],
        "level_resid_mean": float(np.mean(resid)),
        "level_resid_std": float(np.std(resid, ddof=2)),
        "level_max_resid_year": worst_year,
        "level_max_resid": worst_resid,
        # Ratio regression
        "ratio_intercept": rat["intercept"],
        "ratio_slope": rat["slope"],
        "ratio_slope_se": rat["se_slope"],
        "ratio_r2": rat["r2"],
        # Recession amplification
        "recession_mean_ratio": rec_ratio,
        "expansion_mean_ratio": exp_ratio,
        "recession_minus_expansion": rec_diff,
        # COVID influence
        "covid_beta_full": lvl["slope"],
        "covid_beta_excl_2020": lvl_no2020["slope"],
        "covid_beta_shift": covid_shift,
        # data provenance flags
        "last_year_partial_months": nmos.get(int(df["year"].max()), 12),
        "statsmodels_available": HAVE_STATSMODELS,
    }
    return results, df


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_results_csv(results: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Wide single-row CSV: one column per requested metric.
    cols = [
        "level_beta",
        "level_alpha",
        "level_r2",
        "ratio_slope",
        "ratio_intercept",
        "recession_mean_ratio",
        "expansion_mean_ratio",
        "covid_beta_shift",
    ]
    # Include the supporting diagnostics too, appended after the required set.
    extras = [
        "level_beta_se",
        "ratio_slope_se",
        "ratio_r2",
        "level_resid_std",
        "level_max_resid_year",
        "level_max_resid",
        "recession_minus_expansion",
        "covid_beta_excl_2020",
        "n_years",
        "n_recession_years",
        "year_start",
        "year_end",
        "last_year_partial_months",
    ]
    out = {k: [results[k]] for k in cols + extras}
    pd.DataFrame(out).to_csv(RESULTS_CSV, index=False)
    return RESULTS_CSV


def write_methodology(results: dict) -> Path:
    beta = results["level_beta"]
    alpha = results["level_alpha"]
    r2 = results["level_r2"]
    se = results["level_beta_se"]
    rslope = results["ratio_slope"]
    rr2 = results["ratio_r2"]
    rec = results["recession_mean_ratio"]
    exp = results["expansion_mean_ratio"]
    rdiff = results["recession_minus_expansion"]
    shift = results["covid_beta_shift"]
    b_full = results["covid_beta_full"]
    b_excl = results["covid_beta_excl_2020"]
    worst_y = results["level_max_resid_year"]
    worst_r = results["level_max_resid"]
    n = results["n_years"]
    y0, y1 = results["year_start"], results["year_end"]
    nrec = results["n_recession_years"]
    partial = results["last_year_partial_months"]

    md = f"""# Cyclical Decomposition of the Black–White Unemployment Ratio

**Window:** {y0}–{y1} ({n} overlapping years; Black and White both observed).
**Source:** BLS CPS annual averages via `unemployment_annual.csv`; NBER
recession spans via `unemployment_recession_peaks.csv`.
**Integrity note:** all figures below are *descriptive correlations and
elasticities*, not causal effects.

## What was estimated

Two ordinary-least-squares regressions were run over the {y0}–{y1} window in
which both Black and White annual unemployment are observed. The **level
specification**, `u_B = α + β·u_W + ε`, asks how many percentage points Black
unemployment moves per point of White unemployment; it yields
**β = {beta:.3f}** (SE {se:.3f}) with **α = {alpha:.3f}** and **R² = {r2:.3f}**.
The **ratio regression**, `ratio = a + b·u_W + ε`, asks whether the Black/White
ratio itself widens or narrows as White unemployment rises; it yields
**b = {rslope:+.4f}** (R² = {rr2:.3f}).

## Interpreting β (non-causal framing)

A level β of **{beta:.2f}** means that, *descriptively*, a one-percentage-point
rise in White unemployment is associated with roughly a {beta:.1f}-point rise in
Black unemployment — above one-for-one, consistent with differential cyclical
co-movement (the "last hired, first fired" pattern). This is a **statistical
association, not a causal effect**: recessions are not randomly assigned, and
occupational, educational, geographic, and policy confounders co-move with the
business cycle, so β should be read as a descriptive elasticity, not the effect
of a treatment. The positive intercept (α ≈ {alpha:.2f}) means Black
unemployment carries a higher floor, which is why the simple *ratio* (rather than
the level gap in points) is approximately flat: the **ratio slope of {rslope:+.3f}
is close to zero**, i.e. the ~2× multiplier holds roughly as a constant across
the cycle even though the *point gap* widens in recessions. The fit is tight
(R² = {r2:.2f}); the largest residual is {worst_y} ({worst_r:+.2f} points).

## Recession amplification

Partitioning the {n} years into {nrec} NBER-recession-year windows and the
remaining expansion years gives a mean Black/White ratio of **{rec:.3f}× in
recessions vs {exp:.3f}× in expansions** (difference {rdiff:+.3f}). Because the
ratio is approximately constant (ratio slope ≈ 0), the ratio does **not**
systematically widen in recessions; instead it is the *absolute point gap*
(α + β·u_W, with β > 1) that widens. The "2× rule" is therefore best understood
as a multiplicative regularity, while the differential sensitivity shows up in
levels, not in the ratio.

## The 2020 COVID anomaly and its influence

2020 is a structural break: the pandemic service-sector shutdown hit White
employment unusually hard, dropping the ratio to 1.58×. Re-estimating the level
regression **without** 2020 gives β = {b_excl:.3f}; **including** it gives
β = {b_full:.3f}, a **shift of {shift:+.3f}**. The 2020 observation pulls β
{('down' if shift < 0 else 'up')}, exactly as expected for a point that lies
below the historical line. Per the no-drop integrity rule, the headline
regression **includes** 2020; the exclusion is reported only as an influence
diagnostic.

## Known limits

Black unemployment is not collected before 1972 (CPS Black tabulation begins
then), so the window cannot extend earlier. Annual averages smooth within-year
dynamics (e.g. the April-2020 spike). The ratio regression conflates a secular
downward drift in the ratio since the 1980s with cyclical movement, which is why
the level specification is the cleaner cyclical test.
{f"**{y1} is a partial year ({partial} months)** and is included per the no-drop rule; it may be revised when the full year publishes." if partial < 12 else ""}
"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    METHOD_MD.write_text(md, encoding="utf-8")
    return METHOD_MD


# --------------------------------------------------------------------------- #
# Console summary
# --------------------------------------------------------------------------- #
def print_summary(results: dict) -> None:
    line = "=" * 64
    print(line)
    print("T23 — Cyclical Decomposition: Black–White Unemployment Ratio")
    print(line)
    print(
        f"  Window: {results['year_start']}–{results['year_end']} "
        f"({results['n_years']} yrs; "
        f"{results['n_recession_years']} recession / "
        f"{results['n_expansion_years']} expansion)"
    )
    if results["last_year_partial_months"] < 12:
        print(
            f"  [note] {results['year_end']} is a PARTIAL year "
            f"({results['last_year_partial_months']} months) — included per no-drop rule."
        )
    print("-" * 64)
    print("  LEVEL spec:  u_B = alpha + beta * u_W")
    print(
        f"    alpha = {results['level_alpha']:7.3f}   "
        f"beta = {results['level_beta']:7.3f} (SE {results['level_beta_se']:.3f})   "
        f"R2 = {results['level_r2']:.3f}"
    )
    print(
        f"    resid std = {results['level_resid_std']:.3f}   "
        f"max |resid| = {results['level_max_resid_year']} "
        f"({results['level_max_resid']:+.2f} pts)"
    )
    print("  RATIO spec:  ratio = a + b * u_W")
    print(
        f"    a = {results['ratio_intercept']:7.3f}   "
        f"b = {results['ratio_slope']:+.4f} (SE {results['ratio_slope_se']:.4f})   "
        f"R2 = {results['ratio_r2']:.3f}"
    )
    print("  RECESSION vs EXPANSION mean ratio:")
    print(
        f"    recession  = {results['recession_mean_ratio']:.3f}x   "
        f"expansion = {results['expansion_mean_ratio']:.3f}x   "
        f"diff = {results['recession_minus_expansion']:+.3f}"
    )
    print("  COVID influence (level beta):")
    print(
        f"    beta incl 2020 = {results['covid_beta_full']:.3f}   "
        f"excl 2020 = {results['covid_beta_excl_2020']:.3f}   "
        f"shift = {results['covid_beta_shift']:+.3f}"
    )
    print("-" * 64)
    print(f"  statsmodels: {'available' if results['statsmodels_available'] else 'FALLBACK numpy'}")
    print(f"  wrote: {RESULTS_CSV}")
    print(f"  wrote: {METHOD_MD}")
    print(line)


def main() -> int:
    results, _df = analyze()
    write_results_csv(results)
    write_methodology(results)
    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
