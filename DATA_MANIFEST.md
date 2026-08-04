# Published data manifest — DuBois (race.heterodata.org)

Every file the site publishes, with the URL it is served from and the
SHA-256 of the exact bytes served. Verified against the live site on
2026-08-04.

Base URL: `https://race.heterodata.org/data/files/`

| File | Bytes | SHA-256 |
|---|---:|---|
| [`CITATION.cff`](https://race.heterodata.org/data/files/CITATION.cff) | 1,875 | `eedded7cb99827e636abc96e3cff0d04461222a0554d314cfd76eacff5b92f0d` |
| [`business_ownership_by_race.csv`](https://race.heterodata.org/data/files/business_ownership_by_race.csv) | 1,131 | `a75acc36c8b8fc2002c2442e4e5caf466a3e57ba1591c37156d43e82317beac9` |
| [`data_dictionary.csv`](https://race.heterodata.org/data/files/data_dictionary.csv) | 3,258 | `0fc480f43f28ac205435d6389497872db4285b0a19b42a100263a1217d3f5112` |
| [`demographics_crosscheck.csv`](https://race.heterodata.org/data/files/demographics_crosscheck.csv) | 294 | `7ec352f800022f89257e056f9a3f87ddd4898bc732273f8a788b7ef930bf75c9` |
| [`demographics_population.csv`](https://race.heterodata.org/data/files/demographics_population.csv) | 10,773 | `99c330180cbc1cef296962bccd79dd9faa9b7803b10dcf2f1efd3f85c0594690` |
| [`demographics_race_shares.csv`](https://race.heterodata.org/data/files/demographics_race_shares.csv) | 1,149 | `bd22d2d66c196a919192ac8d695cda5df28b747929740f4077150a8cc7cb2ac7` |
| [`education_attainment_gap.csv`](https://race.heterodata.org/data/files/education_attainment_gap.csv) | 1,250 | `e324655d9b8e5d22c5bfb3c17ac58cdc139bf5ca9a5375c6edb81b664c8bc1de` |
| [`housing_ownership_gap.csv`](https://race.heterodata.org/data/files/housing_ownership_gap.csv) | 801 | `b35845590b407a288051af27215f8e337393eefc1d0894affeed0a4255a17cea` |
| [`imprisonment_by_race.csv`](https://race.heterodata.org/data/files/imprisonment_by_race.csv) | 490 | `70e3c9e1c412ff380d72f46541f232771493518544e8e00f6830b29f446d45ab` |
| [`income_ratio.csv`](https://race.heterodata.org/data/files/income_ratio.csv) | 2,239 | `a99fdbad8a3ad3cfe27d6be38ef137255d40202f095ee5051fbd7956496ed986` |
| [`metro_income_gap_2022.csv`](https://race.heterodata.org/data/files/metro_income_gap_2022.csv) | 24,691 | `f420a31656c4b6b03a9ae2b26b80ec583bcdaba985c202c806003cadd7227d08` |
| [`poverty_gap.csv`](https://race.heterodata.org/data/files/poverty_gap.csv) | 1,282 | `7860899ce6f5b7baaee239bd1bd070b7d73b7cf8d416cb21a987235b5062a459` |
| [`slavetrade_annual.csv`](https://race.heterodata.org/data/files/slavetrade_annual.csv) | 14,113 | `783ce5b797dada6b4856dc576aedbe2fcc3eda1fbfc7fbf995dd71ffc7840026` |
| [`slavetrade_by_region.csv`](https://race.heterodata.org/data/files/slavetrade_by_region.csv) | 354 | `1abf3515980000d25706f49a448f6e003c64fe7dd608637adb1beb1f8c90b226` |
| [`slavetrade_summary.csv`](https://race.heterodata.org/data/files/slavetrade_summary.csv) | 210 | `b0a16fa4308f6334970058e11a6da3bd0518da5e2474798afd4d05860c3cc48b` |
| [`unemployment_annual.csv`](https://race.heterodata.org/data/files/unemployment_annual.csv) | 5,873 | `c7e1b48eef370720aa65746a04cad44016971d9157f2c82b04fd1240bf694a6a` |
| [`unemployment_ratio.csv`](https://race.heterodata.org/data/files/unemployment_ratio.csv) | 2,240 | `b98ccb74a2db9d80c7cd36960a47d7242792e9513726c2c323bcb8abf37e5d5f` |
| [`unemployment_recession_peaks.csv`](https://race.heterodata.org/data/files/unemployment_recession_peaks.csv) | 418 | `f0653dc29f77d644b38267ea97ccacfaa5a136d1b0540b4d34ee13186863f7ea` |
| [`wealth_by_race_2022.csv`](https://race.heterodata.org/data/files/wealth_by_race_2022.csv) | 413 | `d663eacca77ab63da7b9955ad28fbb45bc9fffd085c4fcca7dd4e3248db49432` |
| [`wealth_by_race_timeseries.csv`](https://race.heterodata.org/data/files/wealth_by_race_timeseries.csv) | 2,179 | `b9dc28268b1eddf7ac99b225d400ae9b356299dd9e8509e53c85f2ca85e60d6d` |
| [`wealth_gap_summary_2022.csv`](https://race.heterodata.org/data/files/wealth_gap_summary_2022.csv) | 262 | `505393df03211324927e066c8b627c7879106153411e974ac88fde8b3f282137` |
| [`wealth_gap_timeseries.csv`](https://race.heterodata.org/data/files/wealth_gap_timeseries.csv) | 638 | `d9fbe29bafff59f865c5a8f8b5a95b79d0aea892e9e9d656a24b1be9f171cb2f` |

**22 files**, 75,933 bytes total.

## Fetch them all

```bash
mkdir -p app/data
base=https://race.heterodata.org/data/files
while read -r f; do curl -fsSL -o "app/data/$f" "$base/$f"; done <<'FILES'
CITATION.cff
business_ownership_by_race.csv
data_dictionary.csv
demographics_crosscheck.csv
demographics_population.csv
demographics_race_shares.csv
education_attainment_gap.csv
housing_ownership_gap.csv
imprisonment_by_race.csv
income_ratio.csv
metro_income_gap_2022.csv
poverty_gap.csv
slavetrade_annual.csv
slavetrade_by_region.csv
slavetrade_summary.csv
unemployment_annual.csv
unemployment_ratio.csv
unemployment_recession_peaks.csv
wealth_by_race_2022.csv
wealth_by_race_timeseries.csv
wealth_gap_summary_2022.csv
wealth_gap_timeseries.csv
FILES
```

Then check the bytes you received against the SHA-256 column above.


## What is still missing from a fresh clone

`app/data/headlines.json` and `app/data/series_registry.json` are render
inputs rather than published data, so they are not offered as downloads and
are not in the table above. The 22 files above are the complete published
dataset; the two render inputs are not required to read or reuse the data,
only to boot this particular application.
