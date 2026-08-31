# DPR — Panel 04: Poverty & Public Assistance

**Panel**: PANEL_04_POVERTY
**Build note**: 1 (core stratification indicator)
**Series ID**: D1008 (Poverty Rate by Race)
**Created**: 2026-07-23
**Status**: DPR drafted; pipeline live (L02 → P02 → V04), 17-year output delivered

---

## 1. Purpose

The poverty panel quantifies the official poverty-rate gap by race — one of the
most direct measures of economic deprivation. Poverty status is a binary
threshold (income below the federal poverty line), so the rate is a clean
share-of-population measure, free from the distributional ambiguity of median
income. It anchors DuBois's stratification narrative: the Black poverty rate has
run at roughly **2.19× the White rate** across 2005–2022, a persistent disparity
that the income panel (median household income) complements but cannot express
so starkly.

## 2. Research Questions Addressed

- RQ1: Magnitude & persistence of Black-White economic gaps (poverty is the
  most-cited deprivation headline)
- RQ4: Long-run arc of Black economic status (this panel covers the modern,
  directly-comparable ACS era, 2005–2022)
- RQ6: Relative position of Hispanic and Asian populations (full race-iteration
  set: A/B/C/D/H/I)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1008.01 | Poverty rate, all races | 2005–2022 | US | ACS B17001 |
| D1008.02 | Poverty rate, White alone | 2005–2022 | US | ACS B17001A |
| D1008.03 | Poverty rate, Black/AA alone | 2005–2022 | US | ACS B17001B |
| D1008.04 | Poverty rate, AIAN alone | 2005–2022 | US | ACS B17001C |
| D1008.05 | Poverty rate, Asian alone | 2005–2022 | US | ACS B17001D |
| D1008.06 | Poverty rate, White non-Hispanic | 2005–2022 | US | ACS B17001H |
| D1008.07 | Poverty rate, Hispanic/Latino | 2005–2022 | US | ACS B17001I |
| D1008.08 | Black-White poverty gap (pp) & ratio | 2005–2022 | US | derived |

## 4. Sources & Access

### 4.1 Census ACS 1-Year — Table B17001 (Poverty Status by Sex by Age)
- **Coverage**: 2005–2019, 2021, 2022 annual; **2020 cancelled** (COVID — see §9)
- **Access**: Census ACS API (`https://api.census.gov/data/{year}/acs/acs1`),
  race iterations A/B/C/D/H/I
- **License**: public domain (US Government)
- **Loader**: `Technical/AnuData/loaders/L02_fetch_census_income_poverty.py` (shared
  with Panel 2 income — emits `data/raw/census/poverty_by_race.csv`)
- **Why ACS 1-Year**: annual frequency + official poverty status variable + full
  race-iteration availability. The 1-year file gives the national headline rate
  directly (no 5-year pooling needed at US level).

### 4.2 Race-iteration convention (Census)
Suffixes: (base)=all races · A=White alone · B=Black/AA alone · C=AIAN alone ·
D=Asian alone · H=White alone NOT Hispanic · I=Hispanic/Latino. Hispanic is an
**ethnicity, not a race** (separate Census question); the H/I suffixes let us
isolate White non-Hispanic and Hispanic rates.

## 5. Methodology & Transformations

### 5.1 Poverty-rate construction (L02)
ACS B17001 reports, per race iteration:
- `_001E` = total population for whom poverty status is determined
- `_002E` = population with income below poverty

`poverty_rate = 100 × _002E / _001E` (percent). This is the Census official
poverty universe (income in past 12 months vs. federal poverty threshold,
adjusted for family size/age). No additional deflation is required — the rate is
a share, not a dollar figure (unlike Panel 2 median income, which P02 deflates
to real 2022$).

### 5.2 Gap & ratio computation (P02_construct_income_poverty.py)
The processor pivots the long-form `poverty_by_race.csv` into a wide panel and
derives, per year:
- `black_white_gap_pp = black_poverty_rate − white_poverty_rate` (percentage points)
- `black_white_poverty_ratio = black_poverty_rate / white_poverty_rate`
- `hispanic_white_gap_pp = hispanic_poverty_rate − white_poverty_rate`

No smoothing, imputation, or interpolation. Missing years (2020) are simply
absent rows.

### 5.3 "White" vs "White non-Hispanic"
The panel carries both `white_poverty_rate` (B17001A, White alone — includes
Hispanic-White) and `white_nh_poverty_rate` (B17001H, White alone NOT Hispanic).
The non-Hispanic White rate is consistently *lower* (e.g., 2022: 9.48% nH vs
9.85% all-White), so the B/W gap is slightly *larger* against the nH baseline.
Gap/ratio columns use the A (White alone) denominator for cross-panel
consistency with the income panel.

## 6. Output Files

- `data/processed/poverty_gap.csv` — 17-year panel: poverty rate by race +
  Black/White & Hispanic/White gaps. Columns: `year, all_poverty_rate,
  white_poverty_rate, black_poverty_rate, aian_poverty_rate, asian_poverty_rate,
  white_nh_poverty_rate, hispanic_poverty_rate, black_white_gap_pp,
  black_white_poverty_ratio, hispanic_white_gap_pp`.

**Headline figures (from the CSV)**:
- 2022: all 12.58% · White 9.85% · Black 21.30% · Hispanic 16.78% · AIAN 21.73%
  · Asian 10.06% · White-nH 9.48%; B/W gap **11.45pp**, B/W ratio **2.16×**
- 2005: Black 25.55% vs White 10.42%, B/W ratio 2.45× (peak ratio)
- Black/White poverty ratio average across 2005–2022: **2.19×**

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L02_fetch_census_income_poverty.py` | Load | Pull ACS B17001 (+B19013) by race-iteration → `data/raw/census/poverty_by_race.csv` (+ `income_by_race.csv` for Panel 2) |
| `P02_construct_income_poverty.py` | Process | Pivot to wide, compute B/W & H/W gaps + ratios → `poverty_gap.csv` (+ `income_ratio.csv` for Panel 2) |
| `V04_validate_poverty.py` | Validate | 5 internal-consistency & stylized-fact checks → `VALIDATION_p04_poverty.md` |

## 8. Validation Checks

V04 (`lib/V04_validate_poverty.py`) enforces five checks; all PASS on the
delivered panel:

1. **V04.1** Black/White poverty ratio in [1.5, 3.0] every year (actual range
   2.06–2.45)
2. **V04.2** Black poverty rate strictly > White poverty rate every year
3. **V04.3** Black-White gap (pp) strictly positive every year
4. **V04.4** All poverty rates in [0, 50] plausibility band
5. **V04.5** All poverty rates in [0, 100] hard bound

Report emitted to `data/processed/VALIDATION_p04_poverty.md`.

## 9. Known Gaps & Limitations

- **2020 gap**: the ACS 1-year was cancelled for 2020 (COVID data-collection
  disruption). The year is simply absent from the series — **not imputed**. This
  is a documented structural break, not a data-quality failure.
- **Official poverty threshold understates true need**: the federal poverty line
  is widely criticized as too low (anchored to 1960s food budgets). This panel
  reports the *official* rate for cross-source comparability; a supplemental
  poverty measure (SPM) variant is out of scope v1.
- **Pre-2005**: no ACS 1-year by race-iteration. Decennial poverty by race
  exists from 1959 (first official measure) but is a different methodology;
  bridging is a v2 task.
- **"Bachelor's+", not income components**: poverty is a household-income
  threshold; it cannot be decomposed into wage vs. transfer effects from the ACS
  table alone.
- **ACS 1-year margins of error** are not carried in this panel (point estimates
  only). For small subgroups (AIAN, Asian) the MOE can be ±1–2pp.

## 10. Provenance Trail

Every output cell traces to: Census ACS API call (B17001 race-iteration,
year-stamped) → `L02_fetch_census_income_poverty.py` (`data/raw/census/poverty_by_race.csv`,
raw counts `_001E`/`_002E`) → `P02_construct_income_poverty.py` (gap/ratio derivation →
`data/processed/poverty_gap.csv`) → `V04_validate_poverty.py` (5-check gate →
`VALIDATION_p04_poverty.md`). DPR updated when any transformation changes.
