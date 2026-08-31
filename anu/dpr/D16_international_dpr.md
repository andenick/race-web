# DPR — Panel 16: International Ethnic Inequality

**Panel**: PANEL_16_INTERNATIONAL
**Build note**: 6 (acquisition-hard → acquired 2026-07-27)
**Created**: 2026-07-27
**Status**: Data built & verified
**content_type**: **cross_sectional** (2022 snapshot; no time-series extension applies)

## 1. Purpose

Positions the US Black-White gap in international context: how does overall
inequality and the racial income gap in the US compare to peer democracies and
to structurally unequal societies (Brazil, South Africa)?

## 2. Core Series

| SID | Name | Year | Source | Type |
|---|---|---|---|---|
| D1016 | International Inequality Comparison | 2022 | UNDP HDR + World Bank + national stats | cross_sectional |

## 3. Sources & Access

### 3.1 UNDP HDR 2023/24 (keyless)
- Composite Indices CSV: HDI, IHDI, % loss, coefficient of human inequality,
  income-inequality component for 10 countries.
- https://hdr.undp.org/data-center (CC BY 3.0 IGO)

### 3.2 World Bank Gini (keyless API)
- SI.POV.GINI for 10 countries, 2018-2022.
- https://api.worldbank.org (CC BY 4.0)

### 3.3 Ethnic/racial income gaps (national statistics, cited)
- US: Census ACS 2022 (Black/White median HH ratio 0.643) — from P02
- Brazil: IBGE PNAD Contínua 2022 (hourly earnings, ratio 0.620)
- South Africa: StatsSA IES 2022/23 (mean HH income, ratio 0.212)

## 4. Methodology

UNDP and World Bank metrics measure OVERALL distributional inequality (comparable
across countries). The ethnic-gap ratios use DIFFERENT income metrics (median HH
income vs hourly earnings vs mean income) and are NOT directly comparable — they
give the order of magnitude of the Black-White gap in each country.

## 5. Headline

US IHDI loss (11.2%) > all European peers (Germany 7.3%, France 9.9%, UK 8.0%,
Canada 7.6%); exceeded only by Brazil (24.1%) and South Africa (35.6%). US Gini
(41.7) is highest among high-HDI democracies.

## 6. Known Limitations

- Cross-sectional (2022 snapshot)
- Ethnic-gap ratios use different metrics (see comparability caveat)
- No time-series extension applies

## 7. Pipeline Scripts

| Script | Function |
|---|---|
| `loaders/L16_fetch_international.py` | Download UNDP HDR + World Bank Gini |
| `processors/P16_construct_international.py` | Merge + add cited ethnic gaps |
