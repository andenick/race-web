# DPR — Panel 3: Employment & Unemployment

**Panel**: PANEL_03_EMPLOYMENT
**Build note**: 1 (core economic indicator)
**Created**: 2026-07-27
**Status**: DPR drafted; data built and validated

---

## 1. Purpose

The employment panel measures **unemployment rates by race** and the celebrated Black–White unemployment **ratio** — the most stable empirical regularity in U.S. labor-market disparities. Across more than half a century, Black unemployment has run at roughly twice the White rate in every year, through every recession and expansion. This panel delivers seasonally-adjusted annual unemployment rates for four race/ethnicity groups (1954 White onward; full panel 1972–2025), the Black/White and Hispanic/White ratios, and recession-peak rates mapped to NBER cycles.

## 2. Research Questions Addressed

- RQ1: The Black–White employment gap and the ~2× regularity
- RQ2: Business-cycle behavior — do recessions widen the ratio, and does it mean-revert?
- RQ4: The long-run arc of Black economic status (labor-market access as the flow)

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1005 | Unemployment rate by race (SA, annual avg) | White 1954–; Black 1972–; Hispanic 1973–; Asian 2003– | US | BLS CPS via FRED |
| D1006 | Black/White unemployment ratio | 1972–2025 | US | Derived from D1005 |

Supporting derived series: Hispanic/White ratio, Asian rate, and recession-peak rates by race (7 NBER cycles).

## 4. Sources & Access

### 4.1 BLS Current Population Survey (CPS) via FRED public CSV endpoint — PRIMARY
- **Coverage**: monthly seasonally-adjusted unemployment rates, by race, the longest available from FRED
- **FRED series**:
  - `LNS14000003` — White (available 1954+)
  - `LNS14000006` — Black or African American (available 1972+)
  - `LNS14000009` — Hispanic or Latino (available 1973+)
  - `LNS14032183` — Asian (available 2003+)
- **Access**: FRED public CSV endpoint (fredgraph.csv, keyless); consumed by the loader
- **License**: public domain (BLS via FRED)
- **Why**: CPS is the official U.S. unemployment source; FRED race-disaggregated series are the canonical long-run series

## 5. Methodology & Transformations

### 5.1 Monthly → annual averages
Each race series is a monthly SA rate. Annual averages are computed as the unweighted mean of the 12 monthly values within each calendar year. The `n_months` column records how many months entered the average (12 for full years; 6 for 2025, the partial year).

### 5.2 Race-availability stagger
The four series begin in different years because BLS did not collect/publish them simultaneously: White from 1954, Black from 1972, Hispanic from 1973, Asian from 2003. The output preserves these true start years — no back-fill. The annual long file therefore has White-only rows 1954–1971, then progressively more races.

### 5.3 Ratio derivation (D1006)
`black_white_ratio = black_unemployment / white_unemployment` per year, computed on the annual averages. The Hispanic/White ratio follows the same form. `black_white_gap_pp = black_unemployment − white_unemployment` (percentage points).

### 5.4 NBER recession peaks
For each of 7 NBER-dated recessions, the peak monthly unemployment rate by race is extracted within the recession window (peak month → trough month) and recorded in the peaks file.

## 6. Output Files

- `unemployment_ratio.csv` — D1005/D1006 wide file: White, Black, Hispanic, Asian annual rates + Black/White ratio + gap (pp) + Hispanic/White ratio (54 rows, 1972–2025)
- `unemployment_annual.csv` — D1005 long file: one row per year × race (with `n_months`), preserving the staggered start years
- `unemployment_recession_peaks.csv` — peak rate by race for 7 NBER recessions (1973-75 through 2020 COVID)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `L03_fetch_fred_unemployment.py` | Load | Pull the 4 CPS race series from FRED fredgraph.csv |
| `P03_construct_employment.py` | Process | Monthly→annual averages, ratios, gaps, NBER recession peaks |
| `V03_validate_employment.py` | Validate | 5 internal-consistency checks (see §8) |

## 8. Validation Checks

Run via `V03_validate_employment.py`; report at `data/processed/VALIDATION_p03_employment.md`.

1. **V03.1 — Black ≥ White every year**: the ~2× regularity must hold; `black_unemployment ≥ white_unemployment` in all 54 years
2. **V03.2 — Ratio in [1.0, 3.5]**: every `black_white_ratio` within bound
3. **V03.3 — Span ≥ 53 years**: ratio file covers 1972–2025 (actual: 54 years)
4. **V03.4 — All 4 races in modern years**: every year 2020+ has White, Black, Hispanic, and Asian rows in the annual file
5. **V03.5 — Recession peaks present (informational)**: peaks file non-empty (7 recessions recorded)

## 9. Known Gaps & Limitations

- **Pre-1972 Black unemployment absent.** BLS did not publish a Black unemployment series before 1972; pre-1972 rows are White-only (not imputed). Similarly Asian is absent before 2003 and Hispanic before 1973.
- **2025 is partial** (6 months averaged, `n_months = 6`) — preliminary, subject to revision.
- **COVID 2020 anomaly.** The 2020 Black/White ratio collapsed to **1.58×** — the lowest in the series — because the COVID shock hit White unemployment disproportionately (service-sector layoffs). This is a real compositional anomaly, not a data error; the ratio mean-reverted to ~1.9× by 2022.
- **~2× regularity.** The Black/White ratio **averages 2.11×** across 1972–2025, ranging from 1.58× (2020) to 2.57× (1989) — remarkably stable. Black unemployment peaked near **20% in the 1981–82 Volcker recession** (recession peak 20.2%; annual 1982 = 18.91%, 1983 = 19.5%).
- **SA series are revised.** Monthly SA rates can be revised by BLS; vintage noted via the fetch date.

## 10. Provenance Trail

Every output cell traces to: BLS CPS monthly SA rates (FRED `LNS14000003/06/09`, `LNS14032183`, downloaded from FRED fredgraph.csv) → `L03_fetch_fred_unemployment.py` (fetch) → `P03_construct_employment.py` (annual averages, ratios, recession peaks) → CSVs in `data/processed/`. DPR updated when any transformation changes.
