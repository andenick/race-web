# DPR — Panel 06: Education

**Panel**: PANEL_06_EDUCATION
**Build note**: 1 (core human-capital panel)
**Series ID**: D1009 (Bachelor's+ Attainment by Race)
**Created**: 2026-07-23
**Status**: DPR drafted; pipeline live (L06 → P06 → V06), 16-year output delivered

---

## 1. Purpose

The education panel measures **bachelor's-degree-or-higher attainment** by race
for the population aged 25+. Educational attainment is the canonical human-capital
input to earnings — yet it is only a *partial* equalizer: Black bachelor's+
attainment has risen (16.86% → 25.41% over 2006–2022), but the gap **widened in
absolute terms** because White attainment rose faster. This panel documents that
divergence honestly and flags the structural C15002 column discovery (§5.1) that
the loader had to handle.

## 2. Research Questions Addressed

- RQ1: Magnitude & persistence of Black-White economic gaps (education is the
  most-asked "is it closing?" gap)
- RQ4: Long-run arc of Black economic status (modern ACS era, 2006–2022)
- RQ6: Relative position of Asian (exceeds White), Hispanic (lowest), AIAN
  (lowest) populations

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1009.01 | Bachelor's+ attainment, White alone | 2006–2022 | US | ACS C15002A |
| D1009.02 | Bachelor's+ attainment, Black/AA alone | 2006–2022 | US | ACS C15002B |
| D1009.03 | Bachelor's+ attainment, AIAN alone | 2006–2022 | US | ACS C15002C |
| D1009.04 | Bachelor's+ attainment, Asian alone | 2006–2022 | US | ACS C15002D |
| D1009.05 | Bachelor's+ attainment, White non-Hispanic | 2006–2022 | US | ACS C15002H |
| D1009.06 | Bachelor's+ attainment, Hispanic/Latino | 2006–2022 | US | ACS C15002I |
| D1009.07 | Black-White attainment gap (pp) & ratio | 2006–2022 | US | derived |

## 4. Sources & Access

### 4.1 Census ACS 1-Year — Table C15002 (Sex by Educational Attainment for the Population 25+)
- **Coverage**: **2006–2019, 2021, 2022** (note: starts 2006, not 2005 — see
  §9); **2020 cancelled** (COVID)
- **Access**: Census ACS API (`https://api.census.gov/data/{year}/acs/acs1`),
  race iterations A/B/C/D/H/I
- **License**: public domain (US Government)
- **Loader**: `Technical/AnuData/loaders/L06_fetch_census_education.py` →
  `data/raw/census/education_attainment_by_race.csv`
- **Why C15002 (not B15002)**: the race-iteration tables published under the
  C15002 series code are the structured attainment-by-race tables the API
  serves; the base B15002 does not offer the A/B/C/D/H/I iterations at this
  collapsed granularity. See §5.1 for the column-structure discovery.

### 4.2 Race-iteration convention
A=White alone · B=Black/AA alone · C=AIAN alone · D=Asian alone · H=White alone
NOT Hispanic · I=Hispanic/Latino.

## 5. Methodology & Transformations

### 5.1 CRITICAL — C15002 race-iteration column discovery
The race-iteration tables **C15002A/B/H/I use a MORE-COLLAPSED column structure
than the base table**. The base educational-attainment table (B15002) lists
each degree level separately — Bachelor's (`_015E`), Master's (`_016E`),
Professional (`_017E`), Doctorate (`_018E`) for males, and the mirrored
`_032E`–`_035E` for females (eight columns to sum). The **C15002 race
iterations pre-sum** bachelor's-or-higher per sex into just two columns:

- `_001E` = total population 25+
- `_006E` = **Male, bachelor's degree or higher** (pre-summed)
- `_011E` = **Female, bachelor's degree or higher** (pre-summed)

`bachelors_plus = _006E + _011E`; `bachelors_pct = 100 × bachelors_plus / _001E`.

**Why this matters**: a loader that assumed the eight-column B15002 layout
would silently request nonexistent columns (or double-count). The L06 loader was
written against the *actual* C15002 variables metadata and documents this
collapsed structure in its docstring. This is the kind of source-schema quirk
that only surfaces by reading the Census variables definitions, not the
high-level table description.

### 5.2 Gap & ratio computation (P06_construct_education.py)
The processor pivots the long-form loader output and derives, per year:
- `black_white_gap_pp = White_bachelors_pct − Black_bachelors_pct` (pp; White
  minus Black because higher attainment is advantaged)
- `black_white_ratio = Black_bachelors_pct / White_bachelors_pct`
- `hispanic_white_gap_pp = White − Hispanic`
- `asian_white_gap_pp = Asian − White` (positive — Asian *exceeds* White)

No smoothing or imputation; 2020 and 2005 are absent rows.

### 5.3 Trend interpretation
- Absolute gap: **widened** 11.69pp (2006) → 13.55pp (2022). Both groups gained,
  but White faster (+10.41pp vs Black +8.55pp).
- Relative ratio: **converged** 0.591 (2006) → 0.652 (2022) — Black attainment
  grew faster *proportionally*, so the ratio improved even as the pp gap grew.
The two measures tell different stories; the panel reports both and does not
privilege one narrative.

## 6. Output Files

- `data/processed/education_attainment_gap.csv` — 16-year panel: bachelor's+ % by
  race + B/W, H/W, and A/W gaps. Columns: `year, White_bachelors_pct,
  Black_bachelors_pct, AIAN_bachelors_pct, Asian_bachelors_pct,
  White_nH_bachelors_pct, Hispanic_bachelors_pct, black_white_gap_pp,
  black_white_ratio, hispanic_white_gap_pp, asian_white_gap_pp`.

**Headline figures (from the CSV)**:
- 2022: White **38.96%** · Black **25.41%** · Asian **57.41%** · AIAN **16.85%**
  · White-nH **39.53%** · Hispanic **20.35%**; B/W gap **13.55pp**, B/W ratio
  **0.652**, H/W gap **18.61pp**, Asian-over-White **18.45pp**
- 2006: White 28.55% · Black 16.86%, B/W gap 11.69pp, ratio 0.591
- Change 2006→2022: White +10.41pp, Black +8.55pp → **gap widened** 11.69→13.55pp

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L06_fetch_census_education.py` | Load | Pull ACS C15002 by race-iteration (collapsed `_006E`/`_011E` cols) → `data/raw/census/education_attainment_by_race.csv` |
| `P06_construct_education.py` | Process | Pivot to wide, compute B/W, H/W, A/W gaps + ratio → `education_attainment_gap.csv` |
| `V06_validate_education.py` | Validate | 6 checks (5 gating + 1 INFO trend) → `VALIDATION_p06_education.md` |

## 8. Validation Checks

V06 (`lib/V06_validate_education.py`) enforces five gating checks plus one
informational trend check:

1. **V06.1** All attainment rates in [0, 100] (hard bound)
2. **V06.2** White bachelor's rate strictly > Black rate every year
3. **V06.3** Asian bachelor's rate strictly > White rate every year (stylized
   fact — Asian attainment exceeds White throughout)
4. **V06.4** Black-White gap (pp) strictly positive every year
5. **V06.5** Black/White attainment ratio in [0.4, 0.8] (Black ~60% of White;
   actual range 0.591–0.655)
6. **V06.6** *(INFO, not fail)* Black attainment trend: last year > first year
   — reports rising (16.86% → 25.41%, +8.55pp)

Report emitted to `data/processed/VALIDATION_p06_education.md`.

## 9. Known Gaps & Limitations

- **No 2005 row**: ACS C15002 race-iterations did not begin until **2006**. The
  series starts 2006, one year later than the income/poverty/housing panels.
  A 2005 gap against the all-races base table is not comparable and is omitted.
- **2020 gap**: ACS 1-year cancelled (COVID). Absent row, **not imputed**.
- **"Bachelor's+" only**: the panel does not split high-school, some-college, or
  associate's attainment — bachelor's-or-higher is the headline human-capital
  threshold. A fuller attainment ladder is a v2 task.
- **Attainment ≠ quality / debt**: a bachelor's from a poorly-resourced
  institution carries different labor-market and debt consequences. This panel
  counts credentials, not their economic return (which belongs in the income/
  wealth panels).
- **Asian aggregation**: the D iteration aggregates highly heterogeneous
  subgroups (Indian, Chinese, Vietnamese, etc.) whose attainment varies widely;
  the aggregate Asian-exceeds-White figure masks within-group dispersion.
- **ACS 1-year margins of error** not carried (point estimates only).

## 10. Provenance Trail

Every output cell traces to: Census ACS API call (C15002 race-iteration,
year-stamped; collapsed `_006E`/`_011E` bachelor's+ columns per §5.1) →
`L06_fetch_census_education.py` (`data/raw/census/education_attainment_by_race.csv`,
raw counts) → `P06_construct_education.py` (gap/ratio derivation →
`data/processed/education_attainment_gap.csv`) → `V06_validate_education.py`
(5-gate + 1-INFO trend → `VALIDATION_p06_education.md`). DPR updated when any
transformation changes.
