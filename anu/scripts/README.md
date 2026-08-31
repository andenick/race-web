# Reproducing the RACE (DuBois) Data

## Prerequisites
- Python 3.10+
- `pip install -r ../requirements.txt`

## Order of execution
Loaders (L##) are independent of each other; processors (P##) depend on loader
outputs; validators (V##) run last. `make all` runs everything in order.

```bash
cd anu/
python scripts/L01_fetch_fed_scf.py     # example: download raw SCF waves
python scripts/P01_construct_wealth.py  # process into data/processed/
python scripts/V14_validate_registry.py # final gate -> data/final/
```

## Directory layout
- `data/raw/` — exactly what the public endpoints served (per-source subdirs)
- `data/processed/` — panel CSVs + analytical outputs + validation reports
- `data/final/` — the registry-validated set (written only by V14 on full PASS)

## API keys / manual steps
- **CENSUS_API_KEY** (free): required by every Census API loader (L02, L05,
  L06, L09, L12, L13, L17, L18) -- the API rejects keyless queries.
  https://api.census.gov/data/key_signup.html
- **MeasuringWorth** (D1001 backbone): manual CSV download via web form; place
  at `data/raw/measuringworth/USGDP_1790-2025.csv`. See the L11 docstring.
- Everything else downloads keyless from the canonical public URLs printed in
  each loader's docstring.

## What you get
`data/final/` contains one CSV per registry output, matching the
`series_registry.json` contract (27 series across 38 output files, incl.
multi-file series).

## Troubleshooting downloads
- Each loader is idempotent (re-runs skip files already on disk).
- If a public URL moves, the loader's docstring names the source landing page
  for a manual download; place the file at the documented path and re-run.
- SCF downloads are the heavy step (~200 MB across 12 waves); everything else
  is small.
