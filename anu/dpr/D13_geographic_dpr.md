# DPR — Panel 13: Geographic / Metro Disparities

**Panel**: PANEL_13_GEOGRAPHIC
**Build note**: 1 (build alongside the income panel)
**Created**: 2026-07-23
**Status**: DPR drafted; data built & validated
**content_type**: **cross_sectional** (single year, 2022 — NOT a time series; no extension applies)

---

## 1. Purpose

The geographic panel localizes the racial income gap in space: how wide is the
Black–White median-income gap *metro by metro*? It reveals that the disparity is
not uniform — it is widest in the richest metros (where White income is
exceptionally high) and narrows or even inverts in a small set of special-case
areas. This cross-section complements the national income time series (P02) by
showing *where* the gap bites hardest and anchors any place-based policy or
segregation analysis.

## 2. Research Questions Addressed

- RQ4: The long-run arc of Black economic status (geographic concentration of
  the gap)
- RQ7: Mechanisms of stratification (metro-level segregation, housing-market
  sorting, and spatial mismatch)
- RQ8: The Great Migration's legacy (spatial distribution of the gap across
  Northern vs Southern metros)

## 3. Core Series

| Series ID | Name | Year | Geography | Source | content_type |
|---|---|---|---|---|---|
| D1013 | Median household income by race (White B19013A / Black B19013B) by metro | 2022 | all CBSAs (metro + micro) | Census ACS 1-yr | **cross_sectional** |

Derived columns (computed, not sourced): `black_white_ratio`,
`gap_dollars` (White − Black median income).

## 4. Sources & Access

### 4.1 Census — ACS 1-year, B19013A / B19013B by MSA
- **Endpoint**: `https://api.census.gov/data/2022/acs/acs1`, variables
  `B19013A_001E` (median household income, White alone) and
  `B19013B_001E` (Black/AA alone), for `metropolitan statistical area /
  micropolitan statistical area:*`.
- **Held locally**: `data/processed/metro_income_gap_2022.csv` (390 metros).
- **Coverage**: 2022 (ACS 1-year); all CBSAs reporting both race medians.
- **License**: public domain.
- **Why**: ACS B19013 race-iterations are the standard median-income-by-race
  tables; the metro geography isolates place-level disparity.

### 4.2 Race-iteration convention
`A` suffix = White alone; `B` suffix = Black/AA alone (Census "alone"
universe). Hispanic is a separate ethnicity, not mixed into these race
iterations.

## 5. Methodology & Transformations

### 5.1 Pairing & filtering
The loader (`L13`) pulls both race medians for every CBSA and keeps only metros
where **both** White and Black medians are positive and non-null (ACS suppresses
small-sample cells). This yields 390 metros with complete race coverage.

### 5.2 Derived disparity measures
For each metro:
- `black_white_ratio` = `black_income / white_income` (rounded to 3 dp)
- `gap_dollars` = `white_income − black_income`

Rows are sorted by `gap_dollars` descending (widest gaps first). No smoothing,
weighting, or modeling.

### 5.3 The "inverted" metros (data characteristic, NOT an error)
~33 of 390 metros (**8.5%**) have `black_white_ratio ≥ 1.0` — i.e. Black median
income *≥* White. These are **not errors**. They fall into three documented
categories:
1. **Puerto Rico metros** (e.g. Yauco 2.34×, Aguadilla 1.34×, Mayagüez 1.25×,
   Arecibo 1.04×, Ponce 1.02×) — both populations are Hispanic; the "White
   alone" / "Black alone" split is noisy and not comparable to mainland race
   coding.
2. **Military-base / installation towns** (e.g. Fairbanks AK 1.04×, Killeen-Temple
   TX, Hinesville GA) — uniform military pay compresses race gaps.
3. **Small micro areas** with tiny Black samples (e.g. Sevierville TN 1.87×,
   Chillicothe OH 1.83×, Russellville AR 1.83×) — high-variance medians from
   handfuls of Black households.

The validator (V13.2b) expects ≤20% of metros above 1.0 and documents these
exceptions; 8.5% passes comfortably.

## 6. Output Files

- `data/processed/metro_income_gap_2022.csv` — D1013: median income by race,
  ratio, and gap for 390 metros, 2022 (cross-sectional; sorted by gap desc)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `loaders/L13_fetch_census_metro.py / P13_construct_metro.py` | Load | Pull B19013A/B by CBSA → pair → ratio & gap |
| `lib/V13_validate_geographic.py` | Validate | 6-check suite (see §8) |

## 8. Validation Checks

The validator `V13` runs six checks; the 2022 cross-section satisfies all six
(verified against the output CSV):

| Check | Rule | Result on this data |
|---|---|---|
| V13.1 | ≥ 100 metro rows (panel claims 390) | PASS — 390 metros |
| V13.2 | `black_white_ratio` ∈ [0.2, 2.5] | PASS — range 0.264 (Jefferson City MO) to 2.344 (Yauco PR) |
| V13.2b | ≤ 20% of metros have ratio ≥ 1.0 | PASS — 33/390 = 8.5% (documented PR/military/micro exceptions) |
| V13.3 | both incomes > 0 every row | PASS |
| V13.4 | `gap_dollars > 0` for ≥ 80% of metros | PASS — ~91.5% positive (same 8.5% exceptions) |
| V13.5 | no null `metro_name` | PASS |

Report written to `data/processed/VALIDATION_p13_geographic.md`.

## 9. Known Gaps & Limitations

- **Cross-sectional (single year, 2022)**: this is **not** a time series. The
  Anu extension machinery does not apply (content_type = cross_sectional). A
  multi-year metro panel would require ACS 1-year for each year and CBSA
  boundary reconciliation (CBSA definitions change over time) — a v2 task.
- **Small-sample noise**: ACS 1-year medians for small Black populations in
  micro areas have wide margins of error; the inverted metros (§5.3) are the
  extreme case. MOEs are not carried in this file.
- **Metro definition churn**: CBSA boundaries are fixed at the 2020 OMB
  delineation; comparisons to pre-2020 geographies require a crosswalk.
- **Two-race only**: only White and Black medians are loaded; Asian, Hispanic,
  AIAN metro medians (B19013D/E/H/I) are a straightforward extension.
- **No cost-of-living adjustment**: gaps are nominal dollars; a real
  (CPI/COLA-adjusted) gap would compress in high-cost metros where the nominal
  gap is widest (e.g. San Jose).

## 10. Provenance Trail

Every output cell traces: Census ACS 1-year 2022
(`https://api.census.gov/data/2022/acs/acs1`, variables `B19013A_001E` /
`B19013B_001E`, by CBSA, public domain) → `loaders/L13_fetch_census_metro.py / P13_construct_metro.py`
(pair race medians, keep both-present metros, compute `black_white_ratio` and
`gap_dollars`, sort by gap desc) → `data/processed/metro_income_gap_2022.csv` →
`lib/V13_validate_geographic.py` (6/6 checks PASS). The derived columns are
pure arithmetic on the ACS medians; no secondary source is joined. DPR updated
if the year, geography, or race-iteration convention changes.
