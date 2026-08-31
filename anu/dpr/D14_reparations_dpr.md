# DPR — Panel 14: Reparations & Policy

**Panel**: PANEL_14_REPARATIONS
**Build note**: 6 (curated; built 2026-07-27)
**Created**: 2026-07-27
**Status**: Data built & verified
**content_type**: **cross_sectional** (curated comparison of published estimates)

## 1. Purpose

Assembles the major reparations estimates to show the order of magnitude the
data imply. This is a CURATED panel — no API. Every figure is a real published
number with full citation.

## 2. Core Series

| SID | Name | Source | Type |
|---|---|---|---|
| D2005 | Reparations: Aggregate Black-White Wealth Shortfall | SCF 2022 (P31) | derived |
| D1017 | Reparations Estimates Comparison | 4 published methods | cross_sectional |

## 3. Methods Compared

| Method | $T (low) | $T (high) | Source |
|---|---|---|---|
| DuBois SCF-static (median gap x Black hhs) | 3.8 | 19.0 | Fed SCF 2022 |
| Darity & Mullen (2020) per-capita gap | 10.0 | 12.0 | Brookings / From Here to Equality |
| Craemer et al. (2020) slavery price-based | 12.0 | 13.0 | Rev. Black Pol. Economy |
| Craemer et al. (2020) wage @ 3% interest | 18.6 | 18.6 | JEP 36(2) 2022 |

## 4. CA Task Force (AB 3121) Per-Harm Breakdown

| Harm | Period | Amount |
|---|---|---|
| Health disparities | 1850–present | $13,600/yr |
| Mass incarceration | 1971–present | $2,400/yr |
| Housing discrimination | 1933–1977 | $3,000/yr |
| Business devaluation | 1850–present | $77,000 one-time |
| Eminent domain | 1850–present | no $ estimate |

Max per eligible lifelong CA resident: >$1.2M (POLITICO, 2023).

## 5. Integrity Guardrail

This is a comparison of published estimates and a computed counterfactual, NOT
a policy prescription. Each figure is labeled with its methodology and source.
No causal or normative claims.

## 6. Pipeline Scripts

| Script | Function |
|---|---|
| `processors/P14_construct_reparations.py` | Assemble curated comparison + CA breakdown |
| `analysis/P31_counterfactual_reparations.py` | SCF-static computation (pre-existing) |
