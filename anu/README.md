# Anu Replication Package — RACE (DuBois)

**What this is**: the complete, self-contained data-construction package behind the
[RACE site](https://github.com/andenick/race-web) (*Race, Stratification & Economic
Disparities in the United States*, after W.E.B. Du Bois). With public internet and
Python 3.10+, you can reproduce every number the site displays from the original
public sources: Federal Reserve SCF, Census ACS/ABS/CPS, BLS via FRED, BJS,
IRS SOI, SlaveVoyages, Opportunity Insights, UNDP, and the World Bank.

- `series_registry.json` — the canonical data contract: 27 series, their public
  sources, units, construction methods, scripts, and validation rules
- `scripts/` — L## loaders (download from public sources), P## processors
  (construct the panels), V## validators (range/consistency checks + the final
  registry gate), M01 (data dictionary)
- `dpr/` — Data Provenance Records, one per series family, plus consolidated
  methodology and extension-provenance notes
- `data/` — gitignored; produced by the scripts (`raw/` → `processed/` → `final/`)

## Quick start

```bash
cd anu/
python -m pip install -r requirements.txt

# 1. fetch raw data from public sources
python scripts/L01_fetch_fed_scf.py            # Fed SCF, 12 waves (~200 MB)
python scripts/L02_fetch_census_income_poverty.py
python scripts/L03_fetch_fred_unemployment.py
python scripts/L04_fetch_fred_cpi.py
python scripts/L05_fetch_census_housing.py
python scripts/L06_fetch_census_education.py
python scripts/L08_fetch_bjs_prisoners.py
python scripts/L09_fetch_census_abs.py
python scripts/L10_fetch_hsus.py
python scripts/L11_fetch_measuringworth.py     # MANUAL download -- see its docstring
python scripts/L12_fetch_census_race_demo.py
python scripts/L12b_fetch_slavevoyages.py
python scripts/L13_fetch_census_metro.py
python scripts/L14_fetch_opportunity_atlas.py
python scripts/L16_fetch_international.py
python scripts/L17_fetch_cps_voting.py         # requires CENSUS_API_KEY (free)
python scripts/L18_fetch_irs_soi.py

# 2. construct the series
python scripts/P01_construct_wealth.py
python scripts/P02_construct_income_poverty.py
python scripts/P03_construct_employment.py
python scripts/P05_construct_housing.py
python scripts/P06_construct_education.py
python scripts/P08_construct_imprisonment.py
python scripts/P09_construct_business.py
python scripts/P10_construct_demographics.py
python scripts/P11_construct_mobility.py
python scripts/P12_construct_slavetrade.py
python scripts/P13_construct_metro.py
python scripts/P14_construct_reparations.py
python scripts/P16_construct_international.py
python scripts/P17_construct_political.py
python scripts/P18_construct_taxation.py
python scripts/P21_decompose_wealth.py         # analytical layer (SCF 2022)
python scripts/P22_decompose_income.py
python scripts/P23_decompose_employment.py
python scripts/P24_decompose_homeownership.py
python scripts/P31_counterfactual_reparations.py
python scripts/P32_counterfactual_incarceration.py
python scripts/M01_data_dictionary.py

# 3. validate (panel validators, then the registry gate)
python scripts/V01_validate_wealth.py
python scripts/V02_validate_income.py
python scripts/V03_validate_employment.py
python scripts/V04_validate_poverty.py
python scripts/V05_validate_housing.py
python scripts/V06_validate_education.py
python scripts/V08_validate_imprisonment.py
python scripts/V09_validate_business.py
python scripts/V10_validate_demographics.py
python scripts/V13_validate_geographic.py
python scripts/V99_validate_all_panels.py
python scripts/V14_validate_registry.py        # final gate; promotes data/final/
```

Or simply `make all` (see Makefile). Validation reports land in
`data/processed/VALIDATION_*.md`; `V14_validate_registry.py` copies the fully
validated series files to `data/final/` only when every check passes.

## API keys

Two exceptions:

| Source | Key? |
|---|---|
| Federal Reserve SCF, FRED (fredgraph.csv), BJS, IRS SOI, SlaveVoyages, Opportunity Insights (Census CES), UNDP HDR, World Bank | **none needed** |
| All **Census API** loaders (ACS/ABS/CPS) | **free key required** — https://api.census.gov/data/key_signup.html, then `export CENSUS_API_KEY=...` (the API returns a "Missing Key" page without one) |
| MeasuringWorth population backbone (D1001) | no key, but a **manual CSV download** (web form) — see `scripts/L11_fetch_measuringworth.py` |

## The 27 series at a glance

Six core dimensions plus historical, political, mobility, taxation, international,
and analytical layers — IDs, sources, units, and coverage are in
`series_registry.json`; construction stories are in `dpr/`.

| Layer | Series IDs | Source families |
|---|---|---|
| Wealth | D1003, D1004, D2001, D2003, D2005 | Fed SCF (12 waves) |
| Income & poverty | D1007, D1008, D2002 | Census ACS + CPI-U |
| Employment | D1005, D1006, D2004 | BLS CPS via FRED |
| Housing | D1010 | Census ACS |
| Education | D1009 | Census ACS |
| Criminal justice | D1011, D2006 | BJS Prisoners |
| Business | D1012 | Census ABS |
| Demographics | D1001, D1002 | MeasuringWorth, HSUS, Census ACS |
| Historical | D1014, D1015 | SlaveVoyages TAST 2019 |
| Geographic | D1013 | Census ACS (metros) |
| International | D1016 | UNDP HDR, World Bank, national agencies |
| Reparations | D1017 | published literature + SCF |
| Political | D1018 | Census CPS Voting Supplement |
| Mobility | D1019 | Opportunity Atlas (Chetty et al. 2018) |
| Taxation | D1020, D1021 | IRS SOI + ACS (race imputed — see caveats) |

## Data integrity rules this package enforces

- No synthetic, interpolated, or placeholder values anywhere. The 2020 ACS 1-year
  gap (COVID cancellation) is left absent, not filled.
- Every value traces to a public source download or a documented computation
  from one. No growth-rate splicing on derived quantities: ratios are computed
  from component medians per period.
- Known caveats travel with the data: the 1989 SCF Black-wealth artifact, CPS
  turnout self-report bias, and the IRS race *imputation* (the IRS does not
  collect race) are flagged in the registry and DPRs.
- `V14_validate_registry.py` is the final gate: presence, count, unit sanity,
  coverage, required-column nulls, and a package hygiene scan.

## Relationship to the site

The site's display data is the bundle generated from this pipeline (the site
repo's `app/data/` is distributed as a downloadable bundle). Running the full
package reproduces those CSVs; `V99`/`V14` are the checks they must pass.
