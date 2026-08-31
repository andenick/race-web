# DuBois — Consolidated Extension Provenance

**Purpose**: single reference documenting, for every series, its source, access method, and vintage — closing the D6 (EPR) gap identified in the independent anu-review. DuBois is a multi-source aggregator: its series are **direct modern-API/source pulls to the present**, not historical book-period splices. There is no "extension splice" in the replicator sense — each series runs unbroken from its source agency to the latest available year. This document centralizes that provenance so reviewers need not reconstruct it from per-loader docstrings.

**Rule (no proxies)**: every series uses its authoritative public source directly. No series substitutes a proxy. Where a series is *derived* (a ratio, a decomposition, a counterfactual), the parent series and the derivation method are stated. Where data is *imputed* (e.g., IRS race), it is flagged.

---

## Descriptive series (D1xxx) — direct source pulls

| SID | Series | Source (public) | Access | Coverage | Vintage note |
|---|---|---|---|---|---|
| D1001 | US Total Population | MeasuringWorth (Williamson) | MeasuringWorth manual download; HSUS cross-check | 1790–2024 | annual interpolation; cross-validated vs HSUS 99.8% |
| D1002 | Population by Race (shares) | Census ACS B02001/B03002 | Census API | 2005–2022 | 2020 gap (ACS1 cancelled, COVID) — left null, not imputed |
| D1003 | Median Net Worth by Race | Fed SCF (12 waves) | `data/raw/scf/` (1989-2019 .zip) + Fed scfp2022.zip (2022) | 1989–2022 | triennial; race-coding harmonized; 1989 value verified-real but excluded from trend |
| D1004 | Black Wealth % of White | derived from D1003 | (derived) | 1989–2022 | weighted medians; SCF weight convention corrected (counts) |
| D1005 | Unemployment Rate by Race | BLS CPS via FRED | FRED fredgraph.csv (keyless) | 1954–2025 | White 1954+; Black/Hispanic 1972/73+; Asian 2003+ |
| D1006 | Black/White Unemployment Ratio | derived from D1005 | (derived) | 1972–2025 | annual avgs of monthly SA |
| D1007 | Median HH Income by Race | Census ACS B19013 | Census API | 2005–2022 | CPIAUCSL-deflated to 2022$; 2020 gap |
| D1008 | Poverty Rate by Race | Census ACS B17001 | Census API | 2005–2022 | rate = _002E/_001E; 2020 gap |
| D1009 | Bachelor's+ by Race | Census ACS C15002 | Census API | 2006–2022 | race-iterations began 2006; collapsed column structure documented |
| D1010 | Homeownership Rate by Race | Census ACS B25003 | Census API | 2005–2022 | owner/total; 2020 gap |
| D1011 | Imprisonment Rate by Race | BJS *Prisoners in 2020* (NCJ 302776) | `data/raw/bjs/` CSVs | 2010–2020 | per 100K adult residents; FBI arrests NOT conflated |
| D1012 | Employer Firms by Owner Race | Census ABS Company Summary | Census API | 2018–2021 | race groups overlap Hispanic → shares sum ~98% (documented) |
| D1013 | Median Income by Race by Metro | Census ACS B19013A/B | Census API | 2022 | cross-sectional; 390 metros; ~33 "inverted" metros documented |
| D1014 | Slave Trade Embarked/Disembarked | SlaveVoyages TAST 2019 | `data/raw/slavevoyages/tastdb-exp-2019.csv (fetched by L12b)` | 1514–1866 | 36,108 voyages; NA mainland undercount flagged |
| D1015 | Middle-Passage Mortality | derived from D1014 | (derived) | 1514–1866 | 13.7% overall |

## Analytical / derived series (D2xxx) — computed on held microdata/series

| SID | Series | Method | Parent data | Honesty note |
|---|---|---|---|---|
| D2001 | Wealth-Gap Decomposition | Oaxaca–Blinder (White ref) | SCF 2022 microdata | unexplained ≠ discrimination; identity exact |
| D2002 | Income-Gap Decomposition | Oaxaca–Blinder | SCF 2022 | SCF income = comprehensive HH income, not clean wage |
| D2003 | Homeownership-Gap Decomposition | LPM-Oaxaca–Blinder | SCF 2022 | large residual = credit/segregation/down-payment |
| D2004 | Unemployment Cyclical Beta | OLS u_B on u_W | BLS CPS 1972–2025 | descriptive elasticity, not causal |
| D2005 | Reparations Wealth Shortfall | counterfactual: gap × HH | SCF 2022 | mean tail-inflated; Darity-Mullen is different counterfactual |
| D2006 | Incarceration Annual Cost | counterfactual: (Bk−W rate) × adults | BJS + demographics + income | assumptions labeled; annual-flow, not lifetime |

## Why there are no traditional "extension splice" EPRs
Anu EPRs document the splice between a book-period series and a modern extension. DuBois has **no source book** (it is an original aggregator, not a replication). Its series begin at the source agency's first available year and run to the present in one continuous pull. Where a series has a known historical gap (e.g., pre-1972 Black unemployment — not collected by BLS), the gap is **documented and left null**, not spliced or imputed. This is the honest analog of an EPR for an aggregator profile.

## API-key provenance
- **Census API key**: optional for ACS at this volume (CENSUS_API_KEY env var). Used by L02/L05/L06/L12/L13; required by L17 (CPS).
- **FBI CDE key**: held in `Technical/AnuData/config/api_keys.env` (auth verified; P15 routes migrated — blocked).
- No private/internal credentials or paths appear in any published artifact.
