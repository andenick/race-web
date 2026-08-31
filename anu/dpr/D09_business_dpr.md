# DPR — Panel 9: Business Ownership & Credit

**Panel**: PANEL_09_BUSINESS
**Build note**: 1 (build alongside the income/wealth panels)
**Created**: 2026-07-23
**Status**: DPR drafted; data built & validated

---

## 1. Purpose

The business panel measures the ownership side of the racial wealth gap — who
*founded and employs* in the U.S. economy, disaggregated by the race of the
owner. Where the wealth and income panels (P01, P02) document the household
balance sheet and wage, this panel documents the **enterprise balance sheet**:
employer firms, their employees, and their payroll, by owner race. The headline
finding is severe under-representation: Black-owned employer firms are roughly
**2–3% of the total** versus a ~13% population share — a gap wider than income
and approaching the wealth gap in magnitude.

## 2. Research Questions Addressed

- RQ3: The wealth gap (business equity is a wealth component)
- RQ4: The long-run arc of Black economic status (entrepreneurship as a
  pathway historically closed by credit-market discrimination)
- RQ7: Mechanisms of stratification (capital-access barriers → firm-formation
  barriers → intergenerational wealth transmission)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1012 | Employer firms, employees, payroll by owner race | 2018–2021 | US | Census ABS Company Summary |

Owner-race breakdown (`RACE_GROUP` codes): 30 White · 40 Black/AA · 50 AIAN ·
60 Asian · 70 NHPI · 91 Hispanic.

## 4. Sources & Access

### 4.1 Census — Annual Business Survey (ABS) Company Summary (abscs)
- **Endpoint**: `https://api.census.gov/data/{year}/abscs`
- **Held locally**: `data/raw/census/business_ownership_by_race.csv`
- **Coverage**: 2018–2021 (annual; the ABS replaced the quinquennial Survey of
  Business Owners beginning reference year 2017, first published 2018).
- **License**: public domain.
- **Why**: the only annual, nationally-consistent, race-of-owner business
  census. Distinguishes *employer* firms (those with paid employees) from
  non-employer sole proprietors — the economically meaningful unit.

### 4.2 Credit/loan data (bridge — separate)
- HMDA business-loan or SBA loan-by-race data is a sibling-project concern;
  not loaded in this series. See `INTEGRATION_HMDA.md` for the cross-reference.

## 5. Methodology & Transformations

### 5.1 Employer-firm universe
The loader (`L09`) queries `abscs` for `FIRMPDEMP` (employer firms), `EMP`
(employees), `PAYANN` (annual payroll, $ thousands) for each owner
`RACE_GROUP`. The `RACE_GROUP=00` (all-firms) total is fetched separately as
the denominator for the share calculation.

### 5.2 Share construction
`share_of_firms_pct = 100 × firms / total` where `total` is the all-firms
(`RACE_GROUP=00`) count for that year. No reweighting or imputation.

### 5.3 The race/ethnicity overlap (CRITICAL — documented, not "fixed")
Census ABS owner-race groups and Hispanic ethnicity are **not mutually
exclusive**: a firm can be coded Hispanic (91) *and* also reported under a race
group (e.g. Hispanic + White). In addition, "some other race" and "two or more
races" owners are partly omitted from the published owner-race breakdown.
Consequence: **the six reported group shares legitimately sum to ~97–99% per
year, not exactly 100%**. The validator (V09.3) therefore checks the sum falls
in [90, 101]% — a sum outside that band would indicate a real error, while a
sum of 97–99% is the expected, honest result of the overlap. This is documented
in §5 and §9; the shares are **never renormalized** to force 100%.

## 6. Output Files

- `data/raw/census/business_ownership_by_race.csv` — D1012: firms, employees,
  payroll (`$ thousands`), and `share_of_firms_pct` by owner race, 2018–2021
  (24 rows = 4 years × 6 race groups). *Note: lives under `data/raw/census/`,
  not `data/processed/`, because it is the raw API extract; the validator reads
  it from there.*

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `loaders/L09_fetch_census_abs.py / P09_construct_business.py` | Load | Query ABS abscs API → employer firms/employees/payroll by owner race |
| `lib/V09_validate_business.py` | Validate | 5-check suite (see §8) |

## 8. Validation Checks

The validator `V09` runs five checks; the 2018–2021 series satisfies all five
(verified against the output CSV):

| Check | Rule | Result on this data |
|---|---|---|
| V09.1 | `firms` all positive integers | PASS |
| V09.2 | `share_of_firms_pct` ∈ [0, 100] | PASS |
| V09.3 | shares sum to [90, 101]% per year | PASS — sums: 2018=97.70, 2019=98.07, 2020=98.26, 2021=98.33 |
| V09.4 | White share is the largest each year | PASS — Black share: 2.18→2.33→2.44→2.73% |
| V09.5 | `employees` & `payroll_thousands` positive | PASS |

Report written to `data/processed/VALIDATION_p09_business.md`.

## 9. Known Gaps & Limitations

- **Window**: 2018–2021 — the ABS publication window at time of build. The
  series is not back-extended (no pre-2018 ABS; the predecessor Survey of
  Business Owners was quinquennial with different methodology).
- **Race/ethnicity overlap**: shares sum to ~97–99% by design (§5.3). They are
  **not** renormalized; comparisons across groups should note the overlap.
- **Non-employer firms excluded**: the universe is *employer* firms only
  (≥1 paid employee). The much larger non-employer (sole-proprietor) population
  is a separate Census series and would raise Black ownership shares, but
  reflects far less economic activity.
- **Credit access not measured**: this panel counts firms, not the loan-denial
  rates that constrain their formation (HMDA/SBA bridge — §4.2).
- **No geography**: U.S.-total only; metro/state business ownership by race is
  a v2 task.
- **Black share is small in absolute terms**: even by 2021, Black-owned
  employer firms are 161,031 of ~5.9M total (~2.73%) — a ~6× under-representation
  vs the ~13% population share, the structural finding of this panel.

## 10. Provenance Trail

Every output cell traces: Census ABS Company Summary (`abscs` API,
`https://api.census.gov/data/{year}/abscs`, public domain) →
`loaders/L09_fetch_census_abs.py / P09_construct_business.py` (query FIRMPDEMP/EMP/PAYANN by RACE_GROUP,
compute `share_of_firms_pct` against the RACE_GROUP=00 total) →
`data/raw/census/business_ownership_by_race.csv` →
`lib/V09_validate_business.py` (5/5 checks PASS). The share column is a single
division on the API's own total; no secondary source is joined. DPR updated if
the ABS methodology, window, or race-coding changes.
