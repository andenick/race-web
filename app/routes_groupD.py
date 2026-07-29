"""DuBois — Group D routes: geography, history, explore.

Self-contained APIRouter for these pages. Creates its own Jinja2Templates
instance bound to the same shared-chrome context processor (app.chrome.ark_context)
so the ASK header/footer (incl. the mandated dual-anchor footer) render identically
to the main app — WITHOUT editing main.py or chrome.py.

Wiring (added by the integrator in main.py)::
    from app.routes_groupD import router as groupD_router
    app.include_router(groupD_router)

All figures trace to real public-source data in app/data/.
Nothing is fabricated.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app import chrome  # ASK v1 — shared-chrome context processor (read-only import)

router = APIRouter()

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

# Own templates instance — same directory + same context processor as main.py,
# so every page inherits the ASK chrome (header, dual-anchor footer, theme tokens)
# with zero edits to main.py.
templates = Jinja2Templates(
    directory=str(BASE / "templates"),
    context_processors=[chrome.ark_context],
)


# ---------------------------------------------------------------------------
# Data loaders (real CSVs shipped with the app)
# ---------------------------------------------------------------------------

def _load_metro_income_gap(limit: int | None = None) -> list[dict]:
    """Load metro median income by race (390 metros, 2022 ACS B19013A/B).

    Sorted by absolute Black–White income gap (dollars) descending so the widest
    gaps surface first. Optional ``limit`` slices the top-N.
    """
    rows: list[dict] = []
    with open(DATA / "metro_income_gap_2022.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "metro_id": int(row["metro_id"]),
                    "metro_name": row["metro_name"],
                    "white_income": int(row["white_income"]),
                    "black_income": int(row["black_income"]),
                    "ratio": float(row["black_white_ratio"]),
                    "gap_dollars": int(row["gap_dollars"]),
                }
            )
    rows.sort(key=lambda r: r["gap_dollars"], reverse=True)
    if limit is not None:
        rows = rows[:limit]
    return rows


def _load_population() -> list[dict]:
    """US total population 1790–2024 (MeasuringWorth / Williamson backbone)."""
    rows: list[dict] = []
    with open(DATA / "demographics_population.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pop = row.get("total_population", "").strip()
            if not pop:
                continue
            rows.append({"year": int(row["year"]), "population": int(pop)})
    return rows


def _load_slavetrade_annual() -> list[dict]:
    """Annual trans-Atlantic slave-trade embarked/disembarked 1514–1866 (TAST 2019)."""
    rows: list[dict] = []
    with open(DATA / "slavetrade_annual.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "year": int(row["year"]),
                    "voyages": int(row["voyages"]),
                    "embarked": float(row["embarked_total"]),
                    "disembarked": float(row["disembarked_total"]),
                    "mortality_pct": float(row["mortality_rate_pct"]),
                }
            )
    rows.sort(key=lambda r: r["year"])
    return rows


def _load_slavetrade_summary() -> dict:
    """Headline totals from slavetrade_summary.csv (36,108 voyages, 10.67M embarked)."""
    out: dict[str, str] = {}
    with open(DATA / "slavetrade_summary.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[row["metric"]] = row["value"]
    return out


def _load_series_registry() -> list[dict]:
    """The publish:true series from series_registry.json for the explore grid.

    The filter is applied for real (it was previously only described in a
    docstring), so setting ``publish: false`` upstream actually withholds a
    series instead of silently shipping it.
    """
    with open(DATA / "series_registry.json", "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return [s for s in doc.get("series", []) if s.get("publish")]


# Pre-load immutable datasets once at import (real data, not generated).
METROS_ALL = _load_metro_income_gap()              # all 390 (for the count)
METROS_TOP = METROS_ALL[:15]                        # top 15 by gap
POPULATION = _load_population()                     # 1790–2024
SLAVETRADE_ANNUAL = _load_slavetrade_annual()       # 1514–1866
SLAVETRADE_SUMMARY = _load_slavetrade_summary()    # headline totals
SERIES = _load_series_registry()                    # the registry entries


# ---------------------------------------------------------------------------
# HTML pages
# ---------------------------------------------------------------------------

@router.get("/geography", response_class=HTMLResponse)
def geography(request: Request) -> HTMLResponse:
    """Geographic page: Black–White median-income gap across 390 metro/micro areas.

    Chart shows the TOP 15 by absolute dollar gap; the full 390-row dataset is
    available via /api/geography/metros (real ACS B19013A/B 2022 data).
    """
    return templates.TemplateResponse(
        "geography.html",
        {
            "request": request,
            "metros_top15": METROS_TOP,
            "metro_count": len(METROS_ALL),
        },
    )


@router.get("/history", response_class=HTMLResponse)
def history(request: Request) -> HTMLResponse:
    """Historical page: US population growth 1790→2024 + the trans-Atlantic slave trade."""
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "population": POPULATION,
            "slavetrade": SLAVETRADE_ANNUAL,
            "summary": SLAVETRADE_SUMMARY,
        },
    )


# Maps a registry panel id to the dimension page that visualizes it. Every panel
# present in series_registry.json has a page, so every Explore row links through
# (an unmapped panel would render "—", which previously hid 8 of 15 rows whose
# pages were in fact live).
_PANEL_PAGES: dict[str, tuple[str, str]] = {
    "P1_Wealth": ("/wealth-gap", "Wealth Gap"),
    "P2_Income": ("/income-poverty", "Income & Poverty"),
    "P3_Employment": ("/employment", "Employment"),
    "P4_Poverty": ("/income-poverty", "Income & Poverty"),
    "P5_Housing": ("/housing", "Housing"),
    "P6_Education": ("/education", "Education"),
    "P8_CriminalJustice": ("/criminal-justice", "Criminal Justice"),
    "P9_Business": ("/business", "Business"),
    "P10_Demographics": ("/history", "History"),
    "P12_Historical": ("/history", "History"),
    "P13_Geographic": ("/geography", "Geography"),
}


@router.get("/explore", response_class=HTMLResponse)
def explore(request: Request) -> HTMLResponse:
    """Explore page: a searchable browser over every published series in the registry."""
    enriched = []
    for s in SERIES:
        entry = dict(s)
        href = _PANEL_PAGES.get(s.get("panel", ""))
        if href:
            entry["link"], entry["link_label"] = href
        enriched.append(entry)
    return templates.TemplateResponse(
        "explore.html",
        {
            "request": request,
            "series": enriched,
        },
    )


# ---------------------------------------------------------------------------
# JSON API endpoints (real data, for client-side use / downloads)
# ---------------------------------------------------------------------------

@router.get("/api/geography/metros")
def api_metros() -> JSONResponse:
    """All 390 metro/micro areas: White & Black median income + gap (2022 ACS)."""
    return JSONResponse(METROS_ALL)


@router.get("/api/history/population")
def api_population() -> JSONResponse:
    """US total population 1790–2024 (MeasuringWorth)."""
    return JSONResponse(POPULATION)


@router.get("/api/history/slavetrade")
def api_slavetrade() -> JSONResponse:
    """Annual trans-Atlantic slave-trade data 1514–1866 (TAST 2019)."""
    return JSONResponse(SLAVETRADE_ANNUAL)
