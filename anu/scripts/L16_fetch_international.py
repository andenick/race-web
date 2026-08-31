"""
L16 -- International Inequality Loader (Panel 16)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_16_INTERNATIONAL

Downloads two keyless public data sources to position the US Black-White gap in
international context:

1. UNDP Human Development Report 2023/24 -- Composite Indices (keyless CSV)
   https://hdr.undp.org/data-center
   Provides: HDI, Inequality-adjusted HDI (IHDI), % loss due to inequality,
   coefficient of human inequality, and inequality-in-income component (Atkinson).
   License: CC BY 3.0 IGO (UNDP open data).

2. World Bank -- Gini index (keyless REST API, SI.POV.GINI)
   https://api.worldbank.org/v2/country/.../indicator/SI.POV.GINI
   License: CC BY 4.0 (World Bank open data).

Both sources measure OVERALL distributional inequality within a country, NOT
specifically ethnic/racial inequality. They establish the macro context: the US
is more unequal than peer high-HDI nations. The processor (P16) adds the direct
Black-White income-gap ratios from national statistics agencies (Brazil IBGE,
South Africa StatsSA, US Census ACS) with explicit citations.

COVERAGE:
  UNDP HDR: 2010-2022 (IHDI introduced 2010). We extract 2022 snapshot + loss.
  World Bank Gini: 2018-2022 (latest available per country).

OUTPUT:
  data/raw/international/undp_hdr_inequality.csv  -- UNDP inequality metrics, ~12 countries
  data/raw/international/worldbank_gini.csv       -- World Bank Gini, ~8 countries, 2018-2022

NO API KEY REQUIRED for either source.

INTEGRITY: every value traces to the downloaded CSV/API response. No synthetic
data. Missing values left as blank (not imputed).
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

# -- Paths ----------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = RAW / "international"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Countries to extract (high-HDI peers + structurally unequal comparators)
COUNTRIES = {
    "USA": "United States",
    "BRA": "Brazil",
    "ZAF": "South Africa",
    "FRA": "France",
    "DEU": "Germany",
    "GBR": "United Kingdom",
    "CAN": "Canada",
    "MEX": "Mexico",
    "SWE": "Sweden",
    "COL": "Colombia",
}

# UNDP HDR inequality-related columns to extract (2022 snapshot + a few years)
UNDP_INEQ_COLS_2022 = [
    "iso3", "country", "region", "hdicode",
    "hdi_2022", "ihdi_2022", "loss_2022",
    "coef_ineq_2022", "ineq_inc_2022", "ineq_edu_2022", "ineq_le_2022",
    # multi-year IHDI + loss for trend
    "ihdi_2010", "ihdi_2015", "ihdi_2020", "ihdi_2022",
    "loss_2010", "loss_2015", "loss_2020", "loss_2022",
]


def _fetch_undp() -> list[dict]:
    """Download UNDP HDR composite indices CSV and extract inequality metrics."""
    url = ("https://hdr.undp.org/sites/default/files/2023-24_HDR/"
           "HDR23-24_Composite_indices_complete_time_series.csv")
    print(f"  Fetching UNDP HDR from {url[:70]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    rows = []
    for r in reader:
        if r["iso3"] in COUNTRIES:
            rec = {c: r.get(c, "") for c in UNDP_INEQ_COLS_2022}
            rows.append(rec)
    return rows


def _fetch_worldbank_gini() -> list[dict]:
    """Download World Bank Gini index for the country set, 2018-2022."""
    countries_param = ";".join(COUNTRIES.keys())
    url = (f"https://api.worldbank.org/v2/country/{countries_param}"
           f"/indicator/SI.POV.GINI?format=json&date=2018:2022&per_page=200")
    print(f"  Fetching World Bank Gini from api.worldbank.org...")
    req = urllib.request.Request(url, headers={"User-Agent": "race-anu-replication/1.0"})
    resp = urllib.request.urlopen(req, timeout=45)
    data = json.loads(resp.read().decode())
    rows = []
    if len(data) > 1 and data[1]:
        for r in data[1]:
            rows.append({
                "iso3": r["countryiso3code"],
                "country": r["country"]["value"],
                "year": r["date"],
                "gini": r["value"] if r["value"] is not None else "",
            })
    return rows


def main() -> int:
    print("=== L16: International inequality data acquisition ===")

    # --- UNDP HDR ---
    undp_rows = _fetch_undp()
    if not undp_rows:
        print("FATAL: UNDP HDR returned no matching countries", file=sys.stderr)
        return 1
    undp_path = OUT_DIR / "undp_hdr_inequality.csv"
    with undp_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=UNDP_INEQ_COLS_2022, extrasaction="ignore")
        w.writeheader()
        w.writerows(undp_rows)
    print(f"  Wrote {undp_path} ({len(undp_rows)} countries)")
    # quick sanity: show US and ZAF
    for r in undp_rows:
        if r["iso3"] in ("USA", "ZAF", "BRA"):
            print(f"    {r['iso3']}: HDI={r['hdi_2022']}, IHDI={r['ihdi_2022']}, "
                  f"loss={r['loss_2022']}, incomeIneq={r['ineq_inc_2022']}")

    time.sleep(0.5)

    # --- World Bank Gini ---
    wb_rows = _fetch_worldbank_gini()
    if not wb_rows:
        print("WARNING: World Bank Gini returned no data", file=sys.stderr)
    else:
        wb_path = OUT_DIR / "worldbank_gini.csv"
        with wb_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["iso3", "country", "year", "gini"])
            w.writeheader()
            w.writerows(wb_rows)
        print(f"  Wrote {wb_path} ({len(wb_rows)} rows)")

    print("\nL16 complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
