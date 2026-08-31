# DPR — Panel 12: Historical Series — Slave Trade & Cliometric Replication

**Panel**: PANEL_12_HISTORICAL
**Build note**: 1 (forced-migration data built; cliometric centerpiece QUEUED for GPU cycle)
**Created**: 2026-07-23
**Status**: SlaveVoyages (D1014, D1015) built & validated; *Time on the Cross* replication pending offline extraction/offline extraction extraction

---

## 1. Purpose

The historical panel supplies the deep-time origin of Black economic status in
the Americas: the **forced migration** that populated the New World with
enslaved African labor, and (as its centerpiece) the cliometric reconstruction
of the slave economy from *Time on the Cross* (Fogel & Engerman, 1974). The
slave-trade series is the *inflow* that the demographics panel (P10) reconciles
against the resident enslaved population; it is the denominator-adjustment
input for all pre-1865 population and labor-force estimates.

## 2. Research Questions Addressed

- RQ4: The long-run arc of Black economic status (the forced origin of the
  population and the capitalized value of enslaved labor)
- RQ10: International comparative context (the trade was trans-Atlantic; arrival
  regions span Brazil, the Caribbean, Spanish Americas, and mainland NA)
- Bridge to P10 demographics: SlaveVoyages disembarkation ↔ Census slave counts

## 3. Core Series

| Series ID | Name | Years | Geography | Source |
|---|---|---|---|---|
| D1014 | Trans-Atlantic slave trade: annual embarked/disembarked | 1514–1866 | trans-Atlantic + arrival region | SlaveVoyages TAST 2019 |
| D1015 | Middle-Passage mortality (rate + deaths) | 1514–1866 | trans-Atlantic | derived from D1014 (embarked − disembarked) |

Arrival-region breakdown (`REGARR` broad regions, cumulative): Brazil, British
Caribbean, Spanish Americas, Mainland North America, Dutch/Danish/Other
Caribbean, Africa (intra-American), Europe.

## 4. Sources & Access

### 4.1 SlaveVoyages — Trans-Atlantic Slave Trade Database (TAST, 2019 release)
- **Reference**: SlaveVoyages.org, *Trans-Atlantic Slave Trade Database*
  (`tastdb-exp-2019`); codebook `SPSS_Codebook_2019.pdf`.
- **Held locally**: `data/raw/slavevoyages/tastdb-exp-2019.csv (fetched by L12b)` (36,108 voyages,
  1514–1866).
- **License**: CC-BY.
- **Key variables**: `YEARAM` (year of arrival), `SLAXIMP` (slaves embarked,
  imputed), `SLAMIMP` (slaves disembarked, imputed), `REGARR` (hierarchical
  broad region of arrival; `20000`–`29999` = Mainland North America).
- **Why**: the scholarly-consensus record of the trade; imputed embark/disembark
  figures are the basis for the canonical ~12.5M-embarked estimate.

### 4.2 Time on the Cross (Fogel & Engerman, 1974) — QUEUED, not yet extracted
- **Reference**: Robert William Fogel & Stanley L. Engerman, *Time on the Cross:
  The Economics of American Negro Slavery* (1974).
- **Held**: a private scanned copy, scanned source `the scanned source` (318 MB).
- **Status**: the cliometric replication (slave productivity, profitability,
  material conditions) is the intended **centerpiece** of this panel, but its
  publication-grade OCR extraction is **QUEUED for the future offline extraction cycle** — it is a large
  scanned corpus that is not processed in a regular session. Until that
  extraction lands, this DPR documents only the SlaveVoyages component (D1014,
  D1015). No synthetic or placeholder cliometric figures are present.

## 5. Methodology & Transformations

### 5.1 Voyage aggregation
The loader (`L12a`) reads the full 36,108-voyage table and:
- maps the hierarchical `REGARR` code to one of 8 broad arrival regions
  (`20000`–`29999` → Mainland North America; `30000`s → British/French/Dutch
  Caribbean; `40000`s → Spanish Americas; `50000`s → Brazil; etc.);
- groups by `YEARAM` to build annual totals (voyages, embarked, disembarked)
  and a North-America-only sub-series (`disembarked_na`, `voyages_na`).

### 5.2 Mortality derivation (D1015)
Middle-Passage mortality is **derived, not a separate source**:
`mortality_total = max(0, embarked − disembarked)`;
`mortality_rate_pct = 100 × mortality_total / embarked_total`. This is the
documented analytical method of the original database (imputed embark minus
imputed disembark = voyage deaths). No interpolation is applied to sparse
years — years with zero embarked carry a null rate.

### 5.3 North-America undercount (FLAG)
`SLAMIMP` (disembarked) is **sparse for mainland-North-America voyages**: the
NA sub-total (68,816) undercounts the canonical ~388,750 disembarkations
estimated for mainland British North America. This is a **known data
characteristic of the TAST NA records**, not a loader bug — it is flagged here
(§9) and in the methodology-consolidated note. NA inflow figures should be read
as a lower bound until reconciled against the broader imputed-arrival estimates.

## 6. Output Files

- `data/processed/slavetrade_annual.csv` — D1014/D1015: annual voyages,
  embarked, disembarked (total + NA), mortality total & rate, 1514–1866
- `data/processed/slavetrade_by_region.csv` — cumulative embarked/disembarked by
  8 broad arrival regions
- `data/processed/slavetrade_summary.csv` — headline totals (see §5 figures)

## 7. Pipeline Scripts

| Script | Stage | Function |
|---|---|---|
| `loaders/L12b_fetch_slavevoyages.py / P12_construct_slavetrade.py` | Load | Parse TAST 2019 → annual + by-region + summary |
| (TBD) | Load/Process | *Time on the Cross* cliometric replication (post-offline extraction extraction) |

No dedicated validator module is wired for P12 yet; internal-consistency is
asserted in-loader (imputed totals tie out; mortality = embarked − disembarked).

## 8. Validation Checks (in-loader)

- **Totals tie out**: `total_embarked_imputed` (10,665,568) −
  `total_disembarked_imputed` (9,202,995) is consistent with the overall
  middle-passage mortality of **13.7%** (1,462,573 deaths).
- **Year coverage**: 1514–1866, continuous where voyages exist.
- **Region sum**: by-region disembarked sums to the total minus voyages with
  unmapped/missing `REGARR`.
- **NA lower-bound flag**: NA total (68,816) is reported as-is; the gap to the
  canonical ~388K is a known limitation (§5.3), not a validation failure.

## 9. Known Gaps & Limitations

- **Mainland NA undercount**: `SLAMIMP` sparse for NA → 68,816 vs canonical
  ~388K; treat as a lower bound (§5.3).
- **Pre-1514 / post-1866**: outside the trade's recorded window.
- **Imputation dependence**: embark/disembark are the *imputed* TAST fields
  (suffixed `IMP`); they incorporate the database's voyage-level imputation
  model. Originals (where extant) differ slightly.
- ***Time on the Cross* pending**: the cliometric centerpiece is not yet
  extracted (future offline extraction cycle queued; source `the scanned source`, 318 MB
  scanned). No placeholder figures stand in for it.
- **No annual NA mortality sub-series**: NA rows are mostly zero (NA voyages
  are a small share of the total and the `SLAMIMP` sparsity suppresses
  meaningful NA-only mortality rates).

## 10. Provenance Trail

Every output cell traces: SlaveVoyages TAST 2019
(`data/raw/slavevoyages/tastdb-exp-2019.csv (fetched by L12b)`, CC-BY) →
`loaders/L12b_fetch_slavevoyages.py / P12_construct_slavetrade.py` (group by `YEARAM` → annual; map `REGARR` →
regions; derive mortality = embarked − disembarked) → the three
`data/processed/slavetrade_*.csv` files. No secondary source is joined for the
trade series. The *Time on the Cross* cliometric component will add a separate
provenance trail (a private scanned copy `the scanned source` → offline publication-grade OCR extraction →
construction scripts) once the GPU extraction completes. DPR updated when any
transformation or source changes.
