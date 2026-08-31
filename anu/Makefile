# Anu replication package: full pipeline.
# make fetch     -- download all raw data from public sources
# make process   -- construct every panel + the analytical layer
# make validate  -- panel validators + consolidated + registry gate
# make all       -- everything, in order

PY := python

LOADERS := L01_fetch_fed_scf L02_fetch_census_income_poverty L03_fetch_fred_unemployment \
           L04_fetch_fred_cpi L05_fetch_census_housing L06_fetch_census_education \
           L08_fetch_bjs_prisoners L09_fetch_census_abs L10_fetch_hsus \
           L11_fetch_measuringworth L12_fetch_census_race_demo L12b_fetch_slavevoyages \
           L13_fetch_census_metro L14_fetch_opportunity_atlas L16_fetch_international \
           L17_fetch_cps_voting L18_fetch_irs_soi

PROCESSORS := P01_construct_wealth P02_construct_income_poverty P03_construct_employment \
              P05_construct_housing P06_construct_education P08_construct_imprisonment \
              P09_construct_business P10_construct_demographics P11_construct_mobility \
              P12_construct_slavetrade P13_construct_metro P14_construct_reparations \
              P16_construct_international P17_construct_political P18_construct_taxation \
              P21_decompose_wealth P22_decompose_income P23_decompose_employment \
              P24_decompose_homeownership P31_counterfactual_reparations \
              P32_counterfactual_incarceration M01_data_dictionary

VALIDATORS := V01_validate_wealth V02_validate_income V03_validate_employment \
              V04_validate_poverty V05_validate_housing V06_validate_education \
              V08_validate_imprisonment V09_validate_business V10_validate_demographics \
              V13_validate_geographic V99_validate_all_panels V14_validate_registry

.PHONY: fetch process validate all
all: fetch process validate

fetch:
	@for s in $(LOADERS); do echo "== $$s"; $(PY) scripts/$$s.py || exit 1; done

process:
	@for s in $(PROCESSORS); do echo "== $$s"; $(PY) scripts/$$s.py || exit 1; done

validate:
	@for s in $(VALIDATORS); do echo "== $$s"; $(PY) scripts/$$s.py || exit 1; done
