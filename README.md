# DuBois — race.heterodata.org

**Race, stratification & economic disparities in the United States.**

Named for W.E.B. Du Bois, who pioneered the empirical study of race and economic
stratification. DuBois presents race-disaggregated US economic data across six
measurable dimensions — wealth, income, employment, poverty, housing, and criminal
justice — reconstructed from authoritative public sources (Census, Federal Reserve,
BLS, BJS).

This is a [Heterodata](https://heterodata.org) research site. Architect:
[Nick Anderson](https://nickanderson.us).

## Site status — full build (15 routes)

All fifteen routes serve real, source-traced data on the shared chrome. The
header nav links to every content page.

| Route | Page | Data source |
|-------|------|-------------|
| `/` | Landing + the 6-dimension hierarchy chart | `headlines.json` (hierarchy ratios) |
| `/wealth-gap` | Black–White median wealth 1989–2022 (north star) | `wealth_gap_timeseries.csv` (Fed SCF) |
| `/employment` | Black/White unemployment ratio 1972–2025 + recession peaks | `unemployment_ratio.csv` (BLS CPS) |
| `/income-poverty` | Median income ratio + poverty rate by race | `income_ratio.csv`, `poverty_gap.csv` (Census ACS) |
| `/housing` | Homeownership rate by race, 2005–2022 | `housing_ownership_gap.csv` (Census ACS) |
| `/criminal-justice` | Imprisonment rate per 100k by race, 2010–2020 | `imprisonment_by_race.csv` (BJS) |
| `/education` | Bachelor's+ attainment by race, 2006–2022 | `education_attainment_gap.csv` (Census ACS) |
| `/business` | Employer firms by owner race, 2018–2021 | `business_ownership_by_race.csv` (Census ABS) |
| `/geography` | Black–White income gap across 390 metro areas (2022) | `metro_income_gap_2022.csv` (Census ACS) |
| `/history` | US population 1790–2024 + trans-Atlantic slave trade | `demographics_population.csv`, `slavetrade_annual.csv` |
| `/explore` | Searchable browser of every published series | `series_registry.json` |
| `/data` | Downloads — every CSV + data dictionary + citation | `app/data/*.csv` |
| `/code` | Reproducibility — the loader/processor pipeline | prose |
| `/methodology` | Sources, provenance, race-category harmonization | prose (DPR target) |
| `/about` | The W.E.B. Du Bois namesake and the dataset's purpose | prose |

No "coming soon" placeholders — every page is backed by real data.

## Stack

- **FastAPI** + **Jinja2** templates + **Plotly.js** (vendored, no CDN)
- **Shared site kit** — header/footer chrome, ecosystem switcher, theme toggle,
  oxblood accent (`themes/race.css`), all vendored — no CDN
- Python 3.12, gunicorn + uvicorn workers
- **First-party usage telemetry** — `carson-telemetry` ASGI middleware writes one
  row per request to a local SQLite file. No cookies, no third party, no raw IP:
  the only client identifier is `sha256(ip + daily-rotating salt)` truncated to 16
  hex characters, and no user-agent, query string, referrer or cookie is stored.

## Run locally

```bash
pip install -r app/requirements.txt
cd app && python -m uvicorn main:app --reload --port 8090
# → http://localhost:8090
```

> **`carson-telemetry` is a first-party package, is not on PyPI, and is not
> distributed in this repository.** `app/requirements.txt` declares it (so the
> dependency is visible where a reader looks for it) and the `Dockerfile` strips
> that line and installs the copy from `vendor/carson-telemetry` instead. Without
> that tree `pip install -r app/requirements.txt` and `import app.main` both fail —
> **by design**: the import is deliberately unguarded. A `try/except` around it is
> how a sibling site shipped a telemetry volume that was never written for a month
> while every check stayed green. To run without it, stub the middleware out
> locally rather than making the import optional in the committed source.

Or with Docker:

```bash
docker build -t dubois-web .
docker run -p 8090:8090 dubois-web
```

## Data

> **The data files are not distributed in this repository.** The application
> expects them in `app/data/` and loads them at import, so a fresh clone will not
> start until that directory is populated. The dataset is published separately as
> a downloadable bundle; the site serves each file from `/data/files/{name}` and
> lists them all on `/data`. See "Getting the data" below.

All figures trace to real CSVs in `app/data/` — **20 data CSVs** plus the data
dictionary, the citation record, the series registry and the landing-page
headline file — reconstructed from:

- **Wealth** — Federal Reserve Survey of Consumer Finances (1989–2022, 12 waves)
- **Income / Poverty / Housing / Education** — US Census ACS (B19013, B17001, B25003, C15002)
- **Employment** — BLS Current Population Survey via FRED
- **Criminal justice** — BJS *Prisoners* 2020
- **Business** — Census Annual Business Survey (ABS)
- **Demographics** — MeasuringWorth / HSUS / ACS
- **Historical** — SlaveVoyages trans-Atlantic slave-trade database (TAST 2019)
- **Geographic** — Census ACS B19013A/B (metro cross-section, 2022)

Nothing here is fabricated or interpolated by this project. Where an original
source publishes imputed estimates — SlaveVoyages reports TAST embarked and
disembarked totals corrected for incomplete voyage records — that is stated and
the figure is carried through as published.

### Getting the data

Every published file is downloadable from the live site: the
[`/data`](https://race.heterodata.org/data) page lists them with a one-line
description each, and each is served from
`https://race.heterodata.org/data/files/{filename}`.

**Reproduce the dataset from source**: the [`anu/`](anu/) directory is a
self-contained replication package (27 series, loaders → processors →
validators) that rebuilds every published CSV from the original public
sources — Federal Reserve SCF, Census ACS/ABS/CPS, BLS via FRED, BJS, IRS
SOI, SlaveVoyages, Opportunity Atlas, UNDP, and the World Bank. See
[`anu/README.md`](anu/README.md); `make all` inside `anu/` runs the full
pipeline.

**[`DATA_MANIFEST.md`](DATA_MANIFEST.md) is the complete list** — all 22
published files with their download URLs and the SHA-256 of the exact bytes the
site serves, plus a copy-paste shell loop that fetches them all into `app/data/`.

Two files the app also needs are deliberately *not* offered as downloads
(`headlines.json` and `series_registry.json` are render inputs, not published
data), so a fresh clone still cannot boot the application from downloads alone.
The 22 published files are the dataset; the two render inputs only drive this
particular front end.

`build_bundle.py` rebuilds a reproducible zip of the published CSVs plus the data
dictionary and citation record from whatever is in `app/data/`:

```bash
python build_bundle.py            # → app/data/dubois_data_bundle.zip
```

Known gaps are documented on `/methodology`: the Census Bureau released no
standard ACS 1-year estimates for **2020**, so the income, poverty, housing,
education and race-share series have a one-year hole; the 2025 unemployment
point is a **six-month** average; and `data_dictionary.csv` covers 12 of the 20
data CSVs, with the other eight documented in `series_registry.json`.

## How it is verified

Verification is **count-asserting, not status-code-asserting**: each page is
checked for the number of records it actually renders against its source CSV,
and each chart is confirmed to paint in a real browser. HTTP 200 alone is not
treated as a pass — a page that returns 200 while rendering nothing is a failure.

Every page is also checked for real data (no placeholders), for working offline
with no CDN, for legible charts at every viewport width, and for rendering no
literal markdown.

**Live at [race.heterodata.org](https://race.heterodata.org).**

## Project layout

```
app/
  main.py              FastAPI app (landing, wealth-gap, methodology + data loaders)
  chrome.py            shared-chrome context processor (NAV vocabulary lives here)
  routes_groupB.py     /employment, /income-poverty, /housing
  routes_groupC.py     /criminal-justice, /education, /business
  routes_groupD.py     /geography, /history, /explore
  routes_groupE.py     /data, /code, /about (+ safe download route)
  data/                data files — NOT distributed in this repo (see Data above)
  static/
    _shared/           vendored kit (arcanum.css, arcanum-chrome.js, ark-*.js, themes/race.css)
    vendor/plotly.min.js   Plotly.js (vendored, no CDN)
    style.css          site-specific page styles
  templates/
    base.html          shared layout (shared chrome wired in)
    *.html             one template per content route (15 pages)
    _shared/           header.html + footer.html partials
vendor/
  carson-telemetry/    first-party usage-telemetry package — NOT distributed in
                       this repo (see "Run locally" above); pip-installed by the
                       Dockerfile, which fails the build if it is missing
build_bundle.py        reproducible data-bundle builder
Dockerfile             production image (gunicorn + uvicorn workers)
```

## License

- **Code**: MIT (see [LICENSE](LICENSE))
- **Data**: Reconstructed from public-domain / open government data (CC-BY-4.0 for
  the harmonized dataset). Original agencies remain authoritative.
