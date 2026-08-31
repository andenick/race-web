# DPR — Panel 11: Intergenerational Mobility

**Panel**: PANEL_11_MOBILITY
**Build note**: 5 (built 2026-07-27 from existing data)
**Created**: 2026-07-27
**Status**: Data built & verified
**content_type**: **time_series** (birth cohorts 1978-1992)

## 1. Purpose

Measures intergenerational income mobility by race — does a child born into a
given starting position move up, stay, or fall? This is the slowest-moving DuBois
panel: the gap narrows but persists over 14 birth cohorts.

## 2. Core Series

| SID | Name | Years | Source |
|---|---|---|---|
| D1019 | Intergenerational Mobility by Race | 1978-1992 | Opportunity Insights Table 5 |

## 3. Source & Access

Opportunity Insights / Opportunity Atlas, Table 5: National mobility by race,
gender, and parent income percentile.
- File: `data/raw/opportunity/table_5.csv (fetched by L14)` (15 cohorts)
- Paper: Chetty, Hendren, Jones, Porter (2018), QJE 133(2).
- https://opportunityinsights.org/data/

**RESOLVED BLOCKER**: The prior TODO listed P11 as blocked ("Table_5 acquired,
no race col"). That was incorrect: Table 5 DOES contain race-disaggregated
columns (kfr_black_pooled_pXX, kfr_white_pooled_pXX, etc.). The national-level
race×cohort data is sufficient for this panel.

## 4. Methodology

kfr = "kid family income rank": mean percentile rank in national income
distribution for children at age ~31, conditional on parents' income percentile.
Extracted at p25 (parents at 25th pct), p75, p100 for each race.

## 5. Headline

p25 (parents at 25th percentile):
- 1978 cohort: Black 33.5th pct, White 48.4th → gap 14.9pp
- 1992 cohort: Black 35.1st pct, White 46.1st → gap 11.0pp
- Ratio improved 0.69 → 0.76; driven by both modest Black gains and White stagnation
- p75 gap also narrowed: 15.6 → 14.9pp

## 6. Pipeline Scripts

| Script | Function |
|---|---|
| `processors/P11_construct_mobility.py` | Extract kfr by race×parent-pct, compute gap + ratio |
