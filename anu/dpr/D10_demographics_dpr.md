# DPR — Panel 10: Demographic Structure & Projections

**Panel**: PANEL_10_DEMOGRAPHICS
**Build note**: 1 (build first — structural backbone)
**Created**: 2026-07-23
**Status**: DPR drafted; acquisition pending

---

## 1. Purpose

The demographic panel is the **structural backbone** of DuBois — every other panel (wealth, income, employment, housing, criminal justice) joins on race × geography × time. It establishes the population universe by race/ethnicity from 1790 (first Census, counting free vs. enslaved) through the present (ACS annual), with Census Bureau projections to 2060. It also captures the forced-migration inflow via SlaveVoyages.

## 2. Research Questions Addressed

- RQ4: The long-run arc of Black economic status (this panel establishes the population denominator)
- RQ10: International comparative context (population structure by ethnicity)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D10.01 | US population by race (decennial) | 1790–2020 | US | HSUS / Census Decennial |
| D10.02 | US population by race (annual, ACS) | 2005–2023 | US / state / county | Census ACS |
| D10.03 | Race population shares | 1790–2023 | US | derived from D10.01/02 |
| D10.04 | Free vs. enslaved population | 1790–1860 | US / state | HSUS / Census Decennial |
| D10.05 | Hispanic origin population | 1970–2023 | US | Census |
| D10.06 | Age structure by race | 1790–2023 | US | HSUS / ACS |
| D10.07 | Geographic distribution by race (region/state) | 1790–2023 | region/state | HSUS / ACS / IPUMS |
| D10.08 | Census projections by race to 2060 | 2024–2060 | US | Census Projections |
| D10.09 | Slave-trade forced migration inflow | 1514–1866 | trans-Atlantic | SlaveVoyages |
| D10.10 | Multiracial / "two or more races" | 2000–2023 | US | Census |

## 4. Sources & Access

### 4.1 HSUS — Historical Statistics of the United States (public PDF)
- **Location**: `HSUS 1975 (public PDF) `
- **Coverage**: colonial era–2000; population series (Ca series), labor, economic
- **Access**: US Census HSUS 1975 (public PDF); see scripts/L10_fetch_hsus.py
- **License**: public domain (Carter et al., Cambridge UP)
- **Why**: the only continuous historical race-population series 1790–1860 (slave/free) and 1860–1970 by race

### 4.2 Census Decennial + NHGIS
- **Coverage**: 1790–2020; race categories as enumerated each year
- **Access**: NHGIS bulk (registration); Census API for recent
- **License**: public domain

### 4.3 Census ACS (1-yr & 5-yr)
- **Coverage**: 2005–2023 annual; race × age × geography
- **Access**: Census API (endpoints at api.census.gov)
- **License**: public domain

### 4.4 SlaveVoyages.org (NEW — acquire)
- **Coverage**: 36,000+ voyages, 1514–1866
- **Access**: free API + bulk download (https://www.slavevoyages.org/)
- **License**: CC-BY
- **Why**: forced migration inflow — the denominator adjustment for pre-1865 Black population

### 4.5 Census Population Projections
- **Coverage**: 2024–2060 by race
- **Access**: Census bulk
- **License**: public domain

## 5. Methodology & Transformations

### 5.1 Race-category harmonization (CRITICAL)
Census race categories changed at nearly every decennial count. This panel **documents the category scheme per year** in a `category_scheme` column rather than forcing a false continuity:

| Period | Scheme | Notes |
|---|---|---|
| 1790–1820 | free white / other free / slave | "other free" = free non-white |
| 1830–1850 | white / free colored / slave | |
| 1860–1870 | white / black / mulatto | post-Emancipation: slave category dropped |
| 1890 | white / black / mulatto / quadroon / octoroon / Chinese / Japanese | finest-grained in history |
| 1900–1920 | white / black / mulatto / others | mulatto dropped after 1920 |
| 1930–1960 | white / Negro / other | Mexican counted as race in 1930 only |
| 1970– | + Hispanic origin (separate ethnicity question) | |
| 1980– | race categories expand (Asian/Pacific Islander, etc.) | |
| 2000– | "two or more races" allowed | multiracial |

**Harmonization rule**: map to the modern OMB 5-category scheme (White, Black/AA, AIAN, Asian, NHPI) + Hispanic-ethnicity cross-tab, but **preserve the original enumeration in a parallel `race_raw` column** and document every remap. Never silently reclassify.

### 5.2 Hispanic-origin handling
Hispanic is an **ethnicity, not a race** (separate Census question since 1970). Report race "alone or in combination" and document the convention. Hispanic-White, Hispanic-Black, etc. are valid cross-tabs.

### 5.3 Differential undercount adjustment
Black and Hispanic populations are historically undercounted. The Census Bureau publishes Coverage Measurement estimates. Apply undercount adjustments where published (post-1950); document pre-1950 undercount qualitatively.

### 5.4 Forced-migration integration
SlaveVoyages voyages are aggregated to annual disembarkation counts (mainland North America) and reconciled against Census slave-population growth. Discrepancies (natural increase vs. forced inflow) documented per decade.

## 6. Output Files

- `demographics_population.csv` — D10.01, D10.02: population counts by race, 1790–2023
- `demographics_shares.csv` — D10.03: race shares (% of total)
- `demographics_free_enslaved.csv` — D10.04: 1790–1860 slave/free
- `demographics_hispanic.csv` — D10.05
- `demographics_age_structure.csv` — D10.06
- `demographics_geographic.csv` — D10.07: region/state distribution
- `demographics_projections.csv` — D10.08: 2024–2060
- `demographics_slavetrade.csv` — D10.09: forced migration
- `demographics_multiracial.csv` — D10.10

## 7. Pipeline Scripts (to build)

| Script | Stage | Function |
|---|---|---|
| `L10_fetch_hsus.py` | Load | Emit the verified HSUS A 1-8 as-enumerated decennial values (public-domain tabulation) |
| `L11_census_decennial.py` | Load | Pull Census Decennial via NHGIS |
| `L12_fetch_census_race_demo.py` | Load | Pull ACS race × age × geography via Census API |
| `L13_slavevoyages.py` | Load | Pull SlaveVoyages voyage database |
| `L14_census_projections.py` | Load | Pull Census population projections |
| `P10_construct_demographics.py` | Process | Harmonize categories, compute shares, apply undercount adj. |
| `V10_validate_demographics.py` | Validate | Range checks, continuity, cross-source (HSUS vs Census), category-scheme audit |
| `M10_demographics_merge.py` | Merge | Join into panel |

## 8. Validation Checks

1. **Range**: population counts ≥ 0; shares sum to 100% (± rounding)
2. **Continuity**: no implausible jumps year-over-year (>5% without documented event)
3. **Cross-source**: HSUS vs Census Decennial (must agree at overlapping years)
4. **Category-scheme audit**: every row has a valid `category_scheme`; `race_raw` preserved
5. **Undercount**: post-1950 adjusted series within published Coverage Measurement bounds
6. **Slave-trade reconciliation**: decadal SlaveVoyages inflow + natural increase ≈ Census slave-population change

## 9. Known Gaps & Limitations

- **Pre-1790**: no Census; estimates from historical demography only (not in scope v1)
- **1860–1870 transition**: Emancimation category discontinuity documented, not "smoothed"
- **AIAN / NHPI / Asian subgroups**: small-sample; ACS 5-year with MOE flagged (v2)
- **County-level historical**: limited; state-level for pre-1940

## 11. Loader Run Result (L10, 2026-07-23) — OCR QUALITY FINDING

A first-pass parse of the A 1-8 region of the HSUS PDF was done as a one-shot OCR extraction.

**Result**: 5 of 19 decennial years (1790–1970) extract at HIGH confidence via
internal-consistency validation (density = pop/land_area); all 5 match canonical
US Census decennial populations exactly:

| Year | Extracted population | Canonical | ✓ |
|---|---|---|---|
| 1790 | 3,929,214 | 3,929,214 | ✓ |
| 1820 | 9,638,453 | 9,638,453 | ✓ |
| 1830 | 12,866,020 | 12,866,020 | ✓ |
| 1850 | 23,191,876 | 23,191,876 | ✓ |
| 1880 | 50,155,783 | 50,155,783 | ✓ |

The remaining 14 years (1810, 1840, 1860, 1870, 1890–1950, 1960, 1970) are
OCR-fragmented: the population column is garbled or missing (e.g. 1870 reads as
"539 818 449"; 1860's 31,443,321 is absent; 1920/1930/1950/1970 have no
population token at all). The loader flags these REVIEW honestly — it does NOT
guess or inject canonical values.

**Decision (D5, resolved)**: A one-shot OCR extraction of the HSUS PDF recovers ~26%
of decennial years cleanly. This is insufficient for a race-economics dataset
where precision is contested. **Two parallel paths**:

1. **Primary (clean)**: acquire structured Census Decennial / NHGIS data
   (census.gov / nhgis.org) for the full 1790–2020 series — this is the
   authoritative, already-structured source the OCR is approximating.
2. **Reference (offline extraction)**: re-extract the HSUS bicentennial PDF
   (`hist_stats_colonial-1970p1-chA.pdf`) via offline extraction / publication-grade OCR for the
   race-disaggregated and free/slave series (A 91-104, A 119-134) that have no
   clean structured equivalent.

The HSUS as-enumerated values remain a cross-validation reference, not the primary load.

## 10. Provenance Trail

Every output cell traces to: source PDF/CSV (with download date) → loader → processor → merger. DPR updated when any transformation changes.
