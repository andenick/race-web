# DPR — Panel 17: Political Participation

**Panel**: PANEL_17_POLITICAL
**Build note**: 6 (acquisition-hard → acquired 2026-07-27)
**Created**: 2026-07-27
**Status**: Data built & verified
**content_type**: **time_series** (biennial 2010-2022)

## 1. Purpose

Measures voter turnout by race from the CPS Voting Supplement, revealing that
the political gap is the SMALLEST DuBois panel — the 1965 VRA closed the formal
participation gap; the remaining disparity is a midterm-mobilization gap.

## 2. Core Series

| SID | Name | Years | Source |
|---|---|---|---|
| D1018 | Voter Turnout by Race | 2010-2022 | Census CPS Voting Supplement API |

## 3. Source & Access

Census CPS Voting and Registration Supplement, via Census API.
**Working endpoint** (resolves prior blocker — 4 variants had failed):
```
https://api.census.gov/data/{year}/cps/voting/nov?get=PES1,PTDTRACE,PWCMPWGT&for=state:*
```
Key insight: CPS microdata requires `for=state:*` (NOT `for=us:1`). Returns
~100K individual records per year that must be weighted and aggregated.

Variables: PES1 (voted?), PTDTRACE (race), PWCMPWGT (composited weight).
Public domain.

## 4. Methodology

Weighted turnout % = Σ(PES1==1 × weight) / Σ(PES1∈{1,2} × weight) per race.
Universe = citizens 18+ who answered Yes or No (excludes non-citizens/under-18).

**CAVEAT**: CPS self-reported turnout overstates actual turnout by ~5-10pp
(social desirability bias). The racial GAP is analytically meaningful; the LEVEL
is inflated.

## 5. Headline

2012: Black turnout (77.9%) EXCEEDED White (70.8%) — first time in CPS history.
Presidential-year avg gap: +1.4pp (Black exceeds White).
Midterm-year avg gap: −2.5pp (Black trails).
The political gap is the smallest DuBois panel.

## 6. Pipeline Scripts

| Script | Function |
|---|---|
| `loaders/L17_fetch_cps_voting.py` | Pull CPS microdata, compute weighted turnout by race |
| `processors/P17_construct_political.py` | Compute gap + ratio + summary |
