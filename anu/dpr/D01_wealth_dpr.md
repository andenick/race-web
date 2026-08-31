# DPR — Panel 1: Wealth & Asset Ownership

**Panel**: PANEL_01_WEALTH
**Build note**: 1 (core economic indicator)
**Created**: 2026-07-27
**Status**: DPR drafted; data built and validated

---

## 1. Purpose

The wealth panel is the **headline indicator** of the Black–White economic gap in DuBois. Net worth is the stock of accumulated advantage — it transmits across generations, compounds through asset ownership, and is where racial disparities are widest (an order of magnitude larger than the income gap). This panel measures median and mean net worth by race from the Federal Reserve's Survey of Consumer Finances across all 12 available triennial waves (1989–2022), plus a 2022 cross-sectional asset-structure breakdown.

## 2. Research Questions Addressed

- RQ1: The Black–White wealth gap and its persistence over time
- RQ4: The long-run arc of Black economic status (wealth as the cumulative stock)
- RQ2: Whether the gap narrows or widens across business cycles (Great Recession, COVID recovery)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1003 | Median net worth by race | 1989–2022 (12 waves) | US | Fed SCF |
| D1004 | Black wealth as % of White (ratio) | 1989–2022 | US | Derived from D1003 |

Supporting series in the same load: mean net worth by race (1989–2022), and a 2022 asset-structure cross-section (median assets, financial assets, home equity, and debt by race).

## 4. Sources & Access

### 4.1 Federal Reserve Survey of Consumer Finances (SCF) — PRIMARY
- **Coverage**: 12 triennial waves, 1989, 1992, 1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022
- **Access**:
  - 1989–2019: downloaded from federalreserve.gov to `data/raw/scf/`
  - 2022: CSV inside https://www.federalreserve.gov/econres/files/scfp2022.zip
- **License**: public domain (U.S. Federal Reserve)
- **Why**: the SCF is the canonical U.S. household-wealth survey; it over-samples high-wealth households and is the only source with reliable race-disaggregated net-worth distributions

## 5. Methodology & Transformations

### 5.1 Weighted percentile (median) computation
Median net worth is the **weighted median**: the value at the 50th percentile of the weight-cumulative distribution. Mean net worth is the weighted mean. Both use the SCF survey weight (`WGT`).

**SCF weight convention (CRITICAL):** this extract's `WGT` sums to the U.S. household population **across all 5 implicates**. Each household appears five times (once per implicate), and its weight is repeated. For raw population *counts* this means **no ÷5** is applied — the summed weight already represents the population. For *medians and ratios*, the ÷5 cancels on both sides of the ratio, so no correction is needed. This convention is internally consistent and does not bias D1003 (medians) or D1004 (ratios).

### 5.2 Race-coding harmonization
The SCF `RACE` variable changed scheme across waves:

| Period | Codes available | Notes |
|---|---|---|
| 1989–2019 | White / Black / Hispanic / Other (codes 1,2,3,5) | No separate Asian category |
| 2022 | + Asian (code 4) added | Asian reported only in 2022 — not back-imputed |

Asian net worth (2022 median $514,200) is therefore available as a single cross-section, not a time series. The 1989–2019 trend series is strictly comparable on a White/Black/Hispanic/Other basis.

### 5.3 Ratio derivation (D1004)
`black_pct_of_white = black_median_networth / white_median_networth × 100`, computed per wave from the weighted medians (not spliced from growth rates). `black_white_gap_dollars = white_median_networth − black_median_networth`.

## 6. Output Files

- `wealth_by_race_timeseries.csv` — D1003 long file: 12 waves × race, with weighted median and mean net worth (49 rows)
- `wealth_gap_timeseries.csv` — D1004 wide file: Black % of White, Black–White gap $, Hispanic % of White, per wave (12 rows)
- `wealth_by_race_2022.csv` — 2022 cross-section: median assets, financial assets, home equity, and debt by race (5 rows)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L01_fetch_fed_scf.py / P01_construct_wealth.py` | Load | Read 12 SCF Stata files, harmonize RACE codes, emit weighted median/mean net worth by race |
| `P01_construct_wealth.py` | Process | Assemble long + wide timeseries, compute ratios and gaps, emit 2022 asset cross-section |
| `V01_validate_wealth.py` | Validate | 6 internal-consistency checks (see §8) |

## 8. Validation Checks

Run via `V01_validate_wealth.py`; report at `data/processed/VALIDATION_p01_wealth.md`.

1. **V01.1 — Twelve SCF waves**: gap file contains exactly years 1989, 1992, …, 2022 (no missing/extra)
2. **V01.2 — Black % in range**: every `black_pct_of_white` finite and in (0, 35]; the 1989 value (6.0%) is flagged suspect (anomalously low but >0, not failed)
3. **V01.3 — Gap dollars positive**: every `black_white_gap_dollars > 0`
4. **V01.4 — Black median < White median**: holds every wave
5. **V01.5 — Race codes present**: White(1)/Black(2)/Hispanic(3) present every wave; Asian(4) present in 2022
6. **V01.6 — 2022 plausible**: White median > $200,000; Black median in (0, $100,000)

## 9. Known Gaps & Limitations

- **1989 value (6.0%) is real, not a pipeline bug.** The 1989 Black median net worth ($9,914) yielding 6.0% of White was **verified** against the SCF microdata — it is a genuine early-SCF small-sample / race-coding artifact, not an extraction error. It is **excluded from trend claims** (synthesis findings cite 1992–2022). The validator deliberately keeps it in-range rather than dropping it.
- **Asian time series absent.** Asian net worth is reported only in 2022; no back-imputation. The 1989–2019 series has no Asian row.
- **Great-Recession trough (2013, 8.2%)** reflects both the housing crash (Black wealth is housing-concentrated) and the SCF's survey timing; it is the lowest Black–White ratio in the post-1992 series.
- **Triennial only.** SCF waves are 3 years apart; no annual granularity between waves.
- **2022 headline:** Black median $49,590 = **18.2%** of White median $272,000 — the widest the gap has been in dollar terms ($222,410), though the *ratio* recovered above its 2013 trough.

## 10. Provenance Trail

Every output cell traces to: SCF Stata microdata (1989–2019 from `data/raw/scf/`, 2022 from the Fed's scfp2022.zip) → `L01_fetch_fed_scf.py / P01_construct_wealth.py` (weighted medians/means by RACE) → `P01_construct_wealth.py` (ratio + gap derivation) → CSVs in `data/processed/`. DPR updated when any transformation changes.
