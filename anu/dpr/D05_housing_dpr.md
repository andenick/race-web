# DPR — Panel 05: Housing, Segregation & Eviction

**Panel**: PANEL_05_HOUSING
**Build note**: 1 (core wealth-driver panel)
**Series ID**: D1010 (Homeownership Rate by Race)
**Created**: 2026-07-23
**Status**: DPR drafted; pipeline live (L05 → P05 → V05), 17-year output delivered

---

## 1. Purpose

The housing panel documents the racial **homeownership gap** — the single
largest proximate driver of the Black-White wealth gap. Home equity is the
primary asset on most Black household balance sheets, so a ~27-percentage-point
gap in ownership rates translates directly into the wealth disparity Panel 1
measures. This panel *absorbs the original DuBois housing stub*: the earlier
single-table placeholder is superseded by a full ACS-driven tenure series and a
bridge to the HMDA mortgage-denial analysis in the sibling project
(`docs/cross_project/INTEGRATION_HMDA.md`).

## 2. Research Questions Addressed

- RQ1: Magnitude & persistence of Black-White economic gaps (homeownership is the
  canonical structural gap — stable ~27pp for two decades)
- RQ3: Mechanisms of racial wealth accumulation (home equity = primary Black
  asset; exclusion from ownership compounds intergenerationally)
- RQ6: Relative position of Hispanic and Asian populations (full iteration set:
  A/B/C/D/H/I; note Asian ownership below White despite higher income)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1010.01 | Homeownership rate, White alone | 2005–2022 | US | ACS B25003A |
| D1010.02 | Homeownership rate, Black/AA alone | 2005–2022 | US | ACS B25003B |
| D1010.03 | Homeownership rate, AIAN alone | 2005–2022 | US | ACS B25003C |
| D1010.04 | Homeownership rate, Asian alone | 2005–2022 | US | ACS B25003D |
| D1010.05 | Homeownership rate, White non-Hispanic | 2005–2022 | US | ACS B25003H |
| D1010.06 | Homeownership rate, Hispanic/Latino | 2005–2022 | US | ACS B25003I |
| D1010.07 | Black-White homeownership gap (pp) | 2005–2022 | US | derived |

## 4. Sources & Access

### 4.1 Census ACS 1-Year — Table B25003 (Tenure by Race of Householder)
- **Coverage**: 2005–2019, 2021, 2022 annual; **2020 cancelled** (COVID — see §9)
- **Access**: Census ACS API (`https://api.census.gov/data/{year}/acs/acs1`),
  race iterations A/B/C/D/H/I
- **License**: public domain (US Government)
- **Loader**: `Technical/AnuData/loaders/L05_fetch_census_housing.py` →
  `data/raw/census/housing_tenure_by_race.csv`
- **Why ACS B25003**: tenure (own vs. rent) cross-tabulated by race of
  householder is the canonical homeownership series; 1-year file gives annual
  national rates directly.

### 4.2 HMDA bridge (sibling project)
Mortgage denial rates by race (Home Mortgage Disclosure Act, LAR data) are
maintained in a sibling project and linked via
`docs/cross_project/INTEGRATION_HMDA.md`. Denial rates explain *why* the
ownership gap persists (credit-access discrimination) and are consumed as an
analytical overlay, not merged into this panel's tenure series.

### 4.3 Race-iteration convention
A=White alone · B=Black/AA alone · C=AIAN alone · D=Asian alone · H=White alone
NOT Hispanic · I=Hispanic/Latino. (Base table B25003 carries the all-races rate.)

## 5. Methodology & Transformations

### 5.1 Homeownership-rate construction (L05)
ACS B25003 reports, per race iteration:
- `_001E` = total occupied housing units
- `_002E` = owner-occupied housing units

`homeownership_rate = 100 × _002E / _001E` (percent of occupied units that are
owner-occupied). The denominator is **occupied units** (householder universe),
not total population — the rate answers "what share of households of this race
own their home?"

### 5.2 Gap computation (P05_construct_housing.py)
The processor pivots the long-form loader output and derives, per year:
- `black_white_gap_pp = white_rate − black_rate` (percentage points)
- `hispanic_white_gap_pp = white_rate − hispanic_rate`

White minus Black (not Black minus White), because for homeownership *higher is
advantaged* — a positive gap means White advantage. No smoothing or imputation;
2020 is simply absent.

### 5.3 Stub absorption
This panel replaced the original DuBois housing stub (a single placeholder
table) with the full L05/P05 pipeline. The stub's ad-hoc figures are retired;
all housing numbers now flow from ACS B25003. The HMDA denial-rate overlay is
the explicit hand-off to the sibling mortgage-access project.

## 6. Output Files

- `data/processed/housing_ownership_gap.csv` — 17-year panel: homeownership rate
  by race + Black/White & Hispanic/White gaps. Columns: `year, white_rate,
  black_rate, hispanic_rate, asian_rate, black_white_gap_pp,
  hispanic_white_gap_pp`.

**Headline figures (from the CSV)**:
- 2022: White **72.25%** · Black **44.1%** · Asian **63.27%** · Hispanic
  **51.05%**; B/W gap **28.15pp**, H/W gap **21.2pp**
- 2005: White 72.03% · Black 45.76%, B/W gap 26.27pp
- Black/White homeownership gap average across 2005–2022: **27.1pp** (range
  25.77–28.61pp — remarkably stable, widening slightly post-Great-Recession)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L05_fetch_census_housing.py` | Load | Pull ACS B25003 by race-iteration → `data/raw/census/housing_tenure_by_race.csv` |
| `P05_construct_housing.py` | Process | Pivot to wide, compute B/W & H/W gaps → `housing_ownership_gap.csv` |
| `V05_validate_housing.py` | Validate | 5 internal-consistency & stylized-fact checks → `VALIDATION_p05_housing.md` |

## 8. Validation Checks

V05 (`lib/V05_validate_housing.py`) enforces five checks; all PASS on the
delivered panel:

1. **V05.1** All homeownership rates in [0, 100] (hard bound)
2. **V05.2** Black-White gap (pp) strictly positive every year
3. **V05.3** White homeownership rate strictly > Black rate every year
4. **V05.4** Hispanic-White gap (pp) strictly positive every year
5. **V05.5** Black-White gap magnitude in [15, 35] pp (stable ~25–30pp gap;
   actual range 25.77–28.61pp)

Report emitted to `data/processed/VALIDATION_p05_housing.md`.

## 9. Known Gaps & Limitations

- **2020 gap**: ACS 1-year cancelled (COVID). Absent row, **not imputed**.
- **No segregation/eviction series in v1**: the panel title spans segregation &
  eviction, but v1 delivers the *homeownership* series only. Dissimilarity
  indices (segregation) and Princeton Eviction Lab counts are scoped for a later
  wave; they are named here to reserve the panel's analytical scope.
- **HMDA denial rates live in the sibling project**: linked via
  `docs/cross_project/INTEGRATION_HMDA.md`, consumed as an overlay. This panel
  does not itself compute denial rates.
- **Homeownership ≠ housing wealth**: ownership rate measures *access*, not
  *equity*. Black-owned homes appreciate slower (appraisal gap, neighborhood
  effects) — the wealth consequence is in Panel 1, not here.
- **ACS 1-year margins of error** not carried (point estimates only).
- **Pre-2005**: no ACS 1-year by race-iteration; decennial tenure-by-race
  exists from 1990 onward but is a different geography/sample frame (v2).

## 10. Provenance Trail

Every output cell traces to: Census ACS API call (B25003 race-iteration,
year-stamped) → `L05_fetch_census_housing.py` (`data/raw/census/housing_tenure_by_race.csv`,
raw counts `_001E`/`_002E`) → `P05_construct_housing.py` (gap derivation →
`data/processed/housing_ownership_gap.csv`) → `V05_validate_housing.py` (5-check
gate → `VALIDATION_p05_housing.md`). HMDA overlay: sibling project per
`docs/cross_project/INTEGRATION_HMDA.md`. DPR updated when any transformation
changes.
