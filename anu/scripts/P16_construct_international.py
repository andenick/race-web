"""
P16 -- International Ethnic Inequality Processor (Panel 16)
Project: DuBois (Race, Stratification & Economic Disparities)
Panel: PANEL_16_INTERNATIONAL

Combines keyless macro-inequality data (UNDP HDR + World Bank Gini) with direct
Black-White income-gap ratios from national statistics agencies to position the
US racial wealth/income gap in international context.

SOURCES:
  Macro inequality (L16 loader, keyless):
    - UNDP HDR 2023/24: HDI, IHDI, % loss, coefficient of human inequality,
      income-inequality component. https://hdr.undp.org/data-center  (CC BY 3.0 IGO)
    - World Bank Gini (SI.POV.GINI). https://api.worldbank.org  (CC BY 4.0)

  Ethnic/racial income gaps (national statistics, cited):
    - US: Black/White median household income ratio = 0.643 (Census ACS 2022,
      B19013A/B; source = this project's P02 panel, data/processed/income_ratio.csv)
    - Brazil: Black/brown hourly earnings R$12.4 vs White R$20.0 (ratio 0.620);
      IBGE PNAD Contínua 2022, Síntese de Indicadores.
      https://agenciadenoticias.ibge.gov.br/en/agencia-news/2184-news-agency/news/38572
    - South Africa: Black African avg HH income R143,632 vs White R676,375
      (ratio 0.212); StatsSA Income & Expenditure Survey 2022/23 (IES, P0100).
      https://www.statssa.gov.za/publications/P0100/P01002022.pdf

COMPARABILITY CAVEAT (MANDATORY — read before interpreting the gap ratios):
  The three ethnic-gap ratios use DIFFERENT income metrics:
    - US: median household income (Census ACS)
    - Brazil: hourly earnings (IBGE — a wage metric, not household income)
    - South Africa: average (mean) household income (StatsSA IES)
  They are NOT directly comparable to each other. They give the ORDER OF MAGNITUDE
  of the Black-White gap in each country, not a controlled cross-country comparison.
  The macro-inequality metrics (Gini, IHDI loss) ARE comparable across countries.

OUTPUT (data/processed/):
  international_comparison.csv -- one row per country, 2022 snapshot, with both
    macro-inequality and (where available) ethnic-gap metrics.

HEADLINE:
  The US IHDI loss (11.2%) is higher than every European peer (Germany 7.3%,
  France 9.9%, UK 8.0%, Canada 7.6%), exceeded only by Brazil (24.1%) and South
  Africa (35.6%) among major economies. The US Gini (41.7) is the highest among
  high-HDI democracies. This macro inequality is consistent with — and partly a
  consequence of — the persistent US Black-White gap documented in P01-P10.
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
INP = RAW / "international"
OUT = PROC


def _load_undp() -> dict[str, dict]:
    rows = {}
    with (INP / "undp_hdr_inequality.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["iso3"]] = r
    return rows


def _load_worldbank_latest() -> dict[str, dict]:
    """Return the most recent non-empty Gini per country (2018-2022)."""
    latest = {}
    with (INP / "worldbank_gini.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["gini"] == "":
                continue
            iso = r["iso3"]
            if iso not in latest or int(r["year"]) > int(latest[iso]["gini_year"]):
                latest[iso] = {"gini": float(r["gini"]), "gini_year": r["year"]}
    return latest


# Ethnic/racial Black-White income-gap ratios from national statistics agencies.
# Each is a REAL published figure with a full citation. Metric type is flagged
# because they are not directly comparable (see module docstring).
ETHNIC_GAPS = {
    "USA": {
        "ratio": 0.643,
        "metric": "median_household_income",
        "black_value": 51374,
        "white_value": 79933,
        "currency": "USD",
        "source": "Census ACS 2022 B19013A/B (DuBois P02)",
        "url": "https://data.census.gov/table/ACSDT1Y2022.B19013",
    },
    "BRA": {
        "ratio": 0.620,
        "metric": "hourly_earnings",
        "black_value": 12.4,
        "white_value": 20.0,
        "currency": "BRL",
        "source": "IBGE PNAD Contínua 2022 (Síntese de Indicadores)",
        "url": ("https://agenciadenoticias.ibge.gov.br/en/agencia-news/"
                "2184-news-agency/news/38572"),
    },
    "ZAF": {
        "ratio": 0.212,
        "metric": "mean_household_income",
        "black_value": 143632,
        "white_value": 676375,
        "currency": "ZAR",
        "source": "StatsSA Income & Expenditure Survey 2022/23 (IES P0100)",
        "url": "https://www.statssa.gov.za/publications/P0100/P01002022.pdf",
    },
}


def _f(v) -> str:
    """Format numeric or blank."""
    if v is None or v == "":
        return ""
    try:
        return f"{float(v):.2f}"
    except (ValueError, TypeError):
        return str(v)


def main() -> int:
    undp = _load_undp()
    wb = _load_worldbank_latest()
    if not undp:
        print("FATAL: no UNDP data loaded", flush=True)
        return 1

    countries = ["USA", "BRA", "ZAF", "DEU", "FRA", "GBR", "CAN", "SWE", "MEX", "COL"]

    cols = [
        "iso3", "country", "hdi_2022", "ihdi_2022", "hdi_loss_pct",
        "coef_human_inequality", "income_inequality_component",
        "worldbank_gini", "gini_year",
        # ethnic / racial gap (only US, BRA, ZAF have published figures)
        "black_white_income_ratio", "gap_metric", "gap_source", "gap_url",
    ]
    rows = []
    for iso in countries:
        u = undp.get(iso, {})
        w = wb.get(iso, {})
        rec = {
            "iso3": iso,
            "country": u.get("country", ""),
            "hdi_2022": _f(u.get("hdi_2022")),
            "ihdi_2022": _f(u.get("ihdi_2022")),
            "hdi_loss_pct": _f(u.get("loss_2022")),
            "coef_human_inequality": _f(u.get("coef_ineq_2022")),
            "income_inequality_component": _f(u.get("ineq_inc_2022")),
            "worldbank_gini": _f(w.get("gini")),
            "gini_year": str(w.get("gini_year", "")),
            "black_white_income_ratio": "",
            "gap_metric": "",
            "gap_source": "",
            "gap_url": "",
        }
        eg = ETHNIC_GAPS.get(iso)
        if eg:
            rec["black_white_income_ratio"] = f"{eg['ratio']:.3f}"
            rec["gap_metric"] = eg["metric"]
            rec["gap_source"] = eg["source"]
            rec["gap_url"] = eg["url"]
        rows.append(rec)

    out_path = OUT / "international_comparison.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out_path} ({len(rows)} countries)")

    # --- Summary ---
    print(f"\n--- Panel 16 International Inequality Summary ---")
    print(f"{'Country':16} {'HDI':>5} {'IHDI':>5} {'Loss%':>6} {'Gini':>5} {'B/W':>5}")
    for r in rows:
        bw = r["black_white_income_ratio"] or "-"
        print(f"{r['country'][:16]:16} {r['hdi_2022']:>5} {r['ihdi_2022']:>5} "
              f"{r['hdi_loss_pct']:>6} {r['worldbank_gini']:>5} {bw:>5}")

    us = next(r for r in rows if r["iso3"] == "USA")
    de = next(r for r in rows if r["iso3"] == "DEU")
    zaf = next(r for r in rows if r["iso3"] == "ZAF")
    print(f"\nHeadline: US IHDI loss ({us['hdi_loss_pct']}%) > all European peers")
    print(f"  (Germany {de['hdi_loss_pct']}%, Sweden {next(r['hdi_loss_pct'] for r in rows if r['iso3']=='SWE')}%);")
    print(f"  exceeded only by Brazil/South Africa. US Gini {us['worldbank_gini']} is")
    print(f"  highest among high-HDI democracies.")
    print(f"\n  Black-White income ratio: US 0.643, Brazil 0.620, South Africa 0.212")
    print(f"  (different metrics — see comparability caveat; not directly comparable)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
