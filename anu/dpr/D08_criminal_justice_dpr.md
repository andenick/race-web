# DPR — Panel 8: Criminal Justice & Incarceration

**Panel**: PANEL_08_CRIMINAL_JUSTICE
**Build note**: 1 (build alongside the human-capital panels)
**Created**: 2026-07-23
**Status**: DPR drafted; data built & validated
**Bridges**: the Davis incarceration-economics project (sibling project on the political economy of prisons)

---

## 1. Purpose

The criminal-justice panel measures the carceral dimension of racial
stratification — the rate at which each racial group is imprisoned in the
United States. It is the **harshest disparity** in the entire DuBois dataset:
the Black imprisonment rate runs roughly **5–6× the White rate** every year,
an order of magnitude wider than the income or wealth gaps. By documenting the
level and the (slowly declining) trend of this disparity, the panel supplies
the incarceration input to any model that links criminal-justice exposure to
labor-market exclusion, family disruption, and wealth destruction — the same
nexus that motivates the Davis project.

## 2. Research Questions Addressed

- RQ4: The long-run arc of Black economic status (carceral exposure as a drain
  on household formation and labor supply)
- RQ7: Mechanisms of stratification (the criminal-justice system as a direct,
  state-enforced axis of racial inequality)
- Bridge to Davis: shared imprisonment denominator for incarceration-economics
  modeling

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1011 | Imprisonment rate per 100,000 by race/ethnicity | 2010–2020 | US (state+federal prison) | BJS *Prisoners* Fig 2 |

Derived columns (computed, not sourced): `black_white_ratio`,
`black_white_gap` (rate points per 100,000).

## 4. Sources & Access

### 4.1 BJS — Prisoners in 2020 (Statistical Tables)
- **Reference**: E. Ann Carson, *Prisoners in 2020*, NCJ 302776, Bureau of
  Justice Statistics (2021). https://bjs.ojp.gov/content/pub/sheets/p20st.zip
- **Held locally**: `data/raw/bjs/p20stf02.csv` (Figure 2 — imprisonment rate per
  100,000 U.S. residents age-bound by race/ethnicity), plus the companion
  `p20stt*.csv` statistical-table set.
- **Coverage**: 2010–2020, annual; White, Black/AA, Hispanic, AIAN, Asian.
- **License**: public domain (U.S. Government work).
- **Why**: the canonical, nationally-consistent imprisonment-rate-by-race
  series. BJS standardizes state+federal prison counts against resident
  population, avoiding the definitional chaos of state-by-state arrest data.

### 4.2 NOT used here (different universe — never conflate)
- **FBI UCR arrests / NIBRS**: a *different* universe (arrests, not
  imprisonment; local-agency reporting, not census of prisoners). Mixing FBI
  arrest rates with BJS imprisonment rates produces spurious comparisons.
  Documented as out-of-scope for this series.

## 5. Methodology & Transformations

### 5.1 Rate extraction
The loader (`L08`) parses Figure 2 (`p20stf02.csv`), which already reports
**rate per 100,000 U.S. residents** by race/ethnicity — no denominator
construction or population join is needed. Rows are identified by a four-digit
leading year and the five rate columns (white, black, hispanic, aian, asian).

### 5.2 Derived disparity measures
For each year where both White and Black rates are present:
- `black_white_ratio` = `black_rate / white_rate` (rounded to 2 dp)
- `black_white_gap` = `black_rate − white_rate` (rate points per 100,000)

No smoothing, interpolation, or modeling is applied. Every value is a faithful
transcription of the BJS published figure.

### 5.3 Trend read (descriptive, not transformed)
The series shows a **monotone decarceration trend** for every group across
2010–2020, with an acceleration in 2020 consistent with COVID-era releases.
This is reported (V08.5), not imputed.

## 6. Output Files

- `data/processed/imprisonment_by_race.csv` — D1011: per-100,000 imprisonment
  rate by race + Black/White ratio & gap, 2010–2020 (11 rows)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `loaders/L08_fetch_bjs_prisoners.py / P08_construct_imprisonment.py` | Load | Parse BJS Fig 2 → per-100,000 rates + derived ratio/gap |
| `lib/V08_validate_imprisonment.py` | Validate | 5-check internal-consistency suite (see §8) |

## 8. Validation Checks

The validator `V08` runs five checks; the 2010–2020 series satisfies all five
by construction (verified against the output CSV):

| Check | Rule | Result on this data |
|---|---|---|
| V08.1 | `black_white_ratio` ∈ [3.0, 8.0] every year | PASS — range 5.08–6.0 |
| V08.2 | `black_rate > white_rate` every year | PASS — min ratio 5.08× |
| V08.3 | all rates ≥ 0; `black_rate ≤ 2500` | PASS — max black rate 1,489 |
| V08.4 | `black_white_gap > 0` every year | PASS |
| V08.5 | decarceration: last-year ratio < first-year (report, not fail) | PASS — 6.0 → 5.13, declined |

Report written to `data/processed/VALIDATION_p08_imprisonment.md`.

## 9. Known Gaps & Limitations

- **Window**: 2010–2020 only — the *Prisoners in 2020* report's Fig 2 horizon.
  No pre-2010 or post-2020 BJS race-rate figures are loaded in this panel
  (acquisition is a v2 task; the race-disaggregated rate series is not published
  as a single continuous run before 2010).
- **Jail excluded**: BJS "imprisonment" = sentenced prison (state + federal),
  not local jail. The jail population (~630K) is a separate BJS series
  (Census of Jails) and would roughly double the exposed population.
- **AIAN visibility**: the AIAN rate is the second-highest every year
  (1,044 → 778 per 100,000), but the small AIAN denominator makes this rate
  comparatively volatile; flagged for careful interpretation.
- **FBI arrests are a different universe**: never splice FBI arrest rates onto
  BJS imprisonment rates (see §4.2).
- **State geography**: this series is U.S.-total only; a state-by-race jail/
  prison breakdown (and its economic correlates) is a Davis-bridge v2 task.

## 10. Provenance Trail

Every output cell traces: `data/raw/bjs/p20stf02.csv` (BJS *Prisoners in 2020*,
Fig 2, public domain, NCJ 302776) → `loaders/L08_fetch_bjs_prisoners.py / P08_construct_imprisonment.py`
(parse → per-100,000 rates → derived `black_white_ratio` / `black_white_gap`)
→ `data/processed/imprisonment_by_race.csv` → `lib/V08_validate_imprisonment.py`
(5/5 checks PASS). The derived columns are pure arithmetic on the BJS rate; no
secondary source is joined. DPR updated if the source report, window, or
derivation changes.
