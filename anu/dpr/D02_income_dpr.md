# DPR — Panel 2: Income & Earnings

**Panel**: PANEL_02_INCOME
**Build note**: 1 (core economic indicator)
**Created**: 2026-07-27
**Status**: DPR drafted; data built and validated

---

## 1. Purpose

The income panel measures **median household income by race** — the flow counterpart to Panel 1's wealth stock. Income captures current economic well-being and labor-market access, and the Black–White income ratio (a much narrower gap than the wealth ratio) anchors any comparison of flows vs. stocks of racial disparity. This panel delivers nominal and CPI-deflated (2022$) median household income for five race/ethnicity groups across 2005–2022, with the Black–White, Hispanic–White, and Asian–White ratios and dollar gaps.

## 2. Research Questions Addressed

- RQ1: The Black–White income gap and its trend
- RQ4: The long-run arc of Black economic status (income as the annual flow)
- RQ2: Business-cycle behavior of the income gap (Great Recession, COVID recovery)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1007 | Median household income by race (nominal + real 2022$) | 2005–2022 | US | Census ACS B19013 |

Supporting derived series in the same output: Black/White ratio, Black–White gap $, Hispanic/White ratio, Asian/White ratio, plus the same metrics for the "All" and AIAN populations.

## 4. Sources & Access

### 4.1 Census ACS B19013 — median household income by race-iteration — PRIMARY
- **Coverage**: ACS 1-year estimates, 2005–2022; race via iteration tables B19013A (White alone), B19013B (Black), B19013C (AIAN), B19013D (Asian), B19013H (White, not Hispanic), B19013I (Hispanic)
- **Access**: Census API; cached results consumed by the loader
- **License**: public domain (U.S. Census Bureau)
- **Why**: ACS is the only annual, nationally-representative, race-disaggregated household-income source; the race-iteration tables provide the by-race medians directly

### 4.2 CPIAUCSL — deflator (via FRED)
- **Coverage**: monthly CPI-U, all urban consumers, used to deflate nominal medians to constant 2022$
- **Access**: FRED public CSV endpoint (fredgraph.csv)
- **License**: public domain (BLS via FRED)

## 5. Methodology & Transformations

### 5.1 Race-iteration pull
The loader fetches each B19013 race-iteration's median household income per year. ACS medians are model-based estimates (the Census fits a distribution and reports the 50th percentile); they are taken as published — no re-fitting.

### 5.2 CPI deflation to 2022$
Each year's nominal median is converted to real 2022 dollars using the annual-average CPIAUCSL (from FRED):

`real_2022 = nominal × (CPI_2022 / CPI_year)`

By construction the 2022 real value equals the 2022 nominal value (base year), confirming the deflator is anchored correctly.

### 5.3 Ratio & gap derivation
`black_white_ratio = Black_nominal / White_nominal` (computed on nominal medians; the ratio is invariant to deflation). `black_white_gap_dollars` computed in nominal dollars per year. The Hispanic/White and Asian/White ratios follow the same form.

## 6. Output Files

- `income_ratio.csv` — D1007 wide file: nominal + real-2022$ medians for All / White / Black / AIAN / Asian / White-nH / Hispanic, plus Black/White, Hispanic/White, and Asian/White ratios and Black–White gap $ (17 rows, 2005–2022)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L02_fetch_census_income_poverty.py` | Load | Pull ACS B19013 race-iterations + CPIAUCSL from FRED/Census |
| `P02_construct_income_poverty.py` | Process | Deflate to 2022$, compute ratios and gaps, emit wide timeseries |
| `V02_validate_income.py` | Validate | 5 internal-consistency checks (see §8) |

## 8. Validation Checks

Run via `V02_validate_income.py`; report at `data/processed/VALIDATION_p02_income.md`.

1. **V02.1 — Black/White ratio in [0.4, 0.8]**: holds every year (stylized bound for the income gap)
2. **V02.2 — CPI deflation worked**: at least one pre-2022 year has `White_real_2022 > White_nominal`
3. **V02.3 — Gap dollars positive**: every `black_white_gap_dollars > 0`
4. **V02.4 — No null nominal income**: every year has non-empty Black and White nominal medians
5. **V02.5 — Asian ≥ White (informational, not failed)**: checks the stylized fact that Asian median income ≥ White; reports any violation without failing

## 9. Known Gaps & Limitations

- **2020 gap — ACS 1-year cancelled.** The Census Bureau did not release standard 2020 ACS 1-year estimates (data-collection disruption from COVID-19). The series therefore jumps 2019 → 2021; **no 2020 row exists** (documented, not imputed). The 2020 row is absent by source, not by pipeline omission.
- **Start year 2005.** ACS 1-year race-iteration medians are reliably available from 2005 onward; earlier years use experimental weights and are excluded.
- **Nominal medians are published estimates.** ACS medians carry margins of error (not captured in v1); small-population iterations (AIAN) are noisier.
- **Headline:** the Black/White median household income ratio **averages 0.628** across 2005–2022 (range 0.612–0.643) — strikingly stable. In 2022, White real median was **$79,933** vs. Black **$51,374** (a $28,559 gap). The ratio is far less volatile than the wealth ratio (Panel 1), reflecting income's lower concentration and faster adjustment.

## 10. Provenance Trail

Every output cell traces to: ACS B19013 race-iteration tables (Census API) + CPIAUCSL (FRED fredgraph.csv) → `L02_fetch_census_income_poverty.py` (fetch + cache) → `P02_construct_income_poverty.py` (deflate, ratios, gaps) → `income_ratio.csv` in `data/processed/`. DPR updated when any transformation changes.
