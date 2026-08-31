# DPR — Panel 18: Taxation by Race (IMPUTED)

**Panel**: PANEL_18_TAXATION
**Build note**: 6 (built 2026-07-27)
**Created**: 2026-07-27
**Status**: Data built & verified
**content_type**: **cross_sectional** (Tax Year 2021)

## 1. Purpose

Estimates federal income-tax burden by race using IRS SOI data + ACS income
distributions. The IRS data is REAL; the race attribution is IMPUTED.

## 2. Core Series

| SID | Name | Type | Source |
|---|---|---|---|
| D1020 | Federal Income Tax by AGI Bracket | cross_sectional | IRS SOI Table 1.4 (2021) |
| D1021 | Federal Tax Burden by Imputed Race | derived | IRS SOI + ACS B19001A/B imputation |

## 3. Sources & Access

### 3.1 IRS SOI Table 1.4 (no key needed)
- https://www.irs.gov/pub/irs-soi/21in14ar.xls (Tax Year 2021)
- 20 AGI brackets: returns, AGI, taxable income, income tax before credits
- Total: 160.8M returns, $14.8T AGI, $2.29T tax (15.5% effective rate)
- Public domain.

### 3.2 Census ACS B19001A/B (Census API key)
- Household income distribution by race (White-alone, Black-alone), 16 brackets
- Used for race imputation of tax burden

## 4. Imputation Method (FLAGGED)

IRS does NOT collect race. Race is IMPUTED:
- For each AGI bracket, estimate Black/White household share from ACS B19001A/B
- Apply share to IRS tax amounts: imputed_black_tax = black_share × total_tax
- Aggregate across brackets for total tax by imputed race

Limitations: ACS household income ≠ IRS AGI; households ≠ tax returns;
within-bracket racial composition assumed uniform. Standard public-finance
imputation (cf. Tax Policy Center).

## 5. Headline

Imputed effective rate: White 15.8% vs Black 12.8%. The difference reflects the
PROGRESSIVE tax code interacting with the racial income distribution, NOT
differential treatment of races by the tax code.

## 6. Pipeline Scripts

| Script | Function |
|---|---|
| `loaders/L18_fetch_irs_soi.py` | Download IRS SOI + pull ACS B19001A/B |
| `processors/P18_construct_taxation.py` | Impute race, compute tax by bracket + race |
