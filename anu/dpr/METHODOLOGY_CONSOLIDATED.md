# DuBois — Consolidated Panel Methodology & Provenance (DPRs)

**Scope**: methodology + provenance for all 11 active panels. Supplements the per-panel loader docstrings. D10_demographics_dpr remains the deep template.

## Per-panel: source → method → known limits

### P01 Wealth (D1003, D1004) — Fed SCF
- **Source**: Survey of Consumer Finances, 12 waves (1989–2022). 1989–2019 downloaded from federalreserve.gov to `data/raw/scf/`; 2022 from the Fed's scfp2022.zip.
- **Method**: weighted median/mean net worth by race (SCF `RACE` variable). Weighted percentile = value at 50th percentile of weight-cumulative distribution. 5 implicates included.
- **Race coding**: 1989–2019 = White/Black/Hispanic/Other (no Asian); 2022 adds Asian. Asian reported only 2022 — not back-imputed.
- **Known limit**: 1989 Black-wealth value (6.0%) is suspect (SCF race-coding that wave) — flagged v2-verify, **excluded from synthesis findings**.

### P02 Income (D1007) — Census ACS B19013
- **Source**: ACS 1-year, median household income by race-iteration (A/B/C/D/H/I).
- **Method**: ACS medians + CPIAUCSL deflation to 2022$ (CPI from FRED (CPIAUCSL via fredgraph.csv)).
- **Known limit**: 2020 gap (ACS1 cancelled); current-dollar medians, deflated for real series.

### P03 Employment (D1005, D1006) — BLS CPS via FRED
- **Source**: FRED fredgraph.csv: LNS14000003 (White), LNS14000006 (Black), LNS14000009 (Hispanic), LNS14032183 (Asian).
- **Method**: monthly SA rates → annual averages; Black/White ratio + NBER recession peaks.
- **Known limit**: pre-1972 Black / pre-2000 Asian absent (not collected).

### P04 Poverty (D1008) — Census ACS B17001
- **Source**: ACS 1-year poverty status by race-iteration. poverty_rate = _002E/_001E.

### P05 Housing (D1010) — Census ACS B25003
- **Source**: ACS 1-year tenure by race-iteration. homeownership_rate = owner-occupied/total.
- **Bridge**: HMDA denial rates (sibling project) — see `INTEGRATION_HMDA.md`.

### P06 Education (D1009) — Census ACS C15002
- **Source**: ACS 1-year, race-iterations. **Note**: race-iterations C15002A/B/H/I use a MORE-COLLAPSED structure than the base table (bachelor's+ pre-summed at _006E/_011E).
- **Known limit**: 2005 gap (race-iterations began 2006).

### P08 Criminal Justice (D1011) — BJS Prisoners
- **Source**: BJS *Prisoners in 2020* Fig 2 (`data/raw/bjs/p20stf02.csv`), imprisonment rate per 100,000 by race.
- **Known limit**: 2010–2020 only (this report); no FBI arrests (different universe — never conflate).

### P09 Business (D1012) — Census ABS Company Summary
- **Source**: ABS abscs, employer firms/employees/payroll by owner RACE_GROUP (40=Black, 60=Asian, 91=Hispanic, etc.).

### P10 Demographics (D1001, D1002) — see D10_demographics_dpr (deep)
- MeasuringWorth backbone (1790–2024) + Census ACS race shares (2005–2022) + HSUS cross-validation (99.8%).

### P12 Historical — SlaveVoyages (D1014, D1015)
- **Source**: SlaveVoyages TAST 2019 (`tastdb-exp-2019.csv`, 36,108 voyages).
- **Method**: YEARAM + SLAXIMP (embarked) + SLAMIMP (disembarked) + REGARR (region). Mainland NA = REGARR 20000–29999.
- **Known limit**: Mainland NA summed (68.8K) undercounts the canonical ~388K — SLAMIMP sparse for NA voyages (flagged).

### P13 Geographic (D1013) — Census ACS B19013A/B by metro
- **Source**: ACS 1-year median income by race, by MSA (all CBSAs).

## Cross-cutting rules (apply to all)
- **No synthetic data**: every gap documented, never imputed (D13 PASS).
- **Race convention**: Census "alone" universe; Hispanic = separate ethnicity (H vs I suffix).
- **Cross-source validation**: V10 (7/7) + V_ALL (16/16) PASS.
