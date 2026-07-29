"""DuBois — Group B routes: employment, income-poverty, housing.

Self-contained APIRouter exporting the three content pages built in this group.
Mirrors main.py's route + chrome pattern: a Jinja2Templates instance wired
with the chrome.ark_context context processor and the same asset_ver cache-buster,
so every TemplateResponse inherits the shared header/footer/switcher chrome
automatically (no per-route chrome wiring needed).

Pages:
  /employment      — Black/White unemployment ratio (1972–2025) + recession peaks
  /income-poverty  — median income ratio + poverty rate by race
  /housing         — homeownership rate by race (2005–2022)

All figures trace to real public-source data. Nothing fabricated.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import chrome  # ASK v1 — shared-chrome context processor

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATIC = BASE / "static"

router = APIRouter()


def _asset_ver(static_dir: Path) -> str:
    """Short content hash of the vendored kit + site css/js — busts cache on deploy."""
    h = hashlib.md5()
    root = Path(static_dir)
    for sub in ("_shared", "css", "js"):
        d = root / sub
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                try:
                    h.update(p.read_bytes())
                except Exception:  # noqa: BLE001
                    pass
    if root.exists():
        for p in sorted(root.glob("*.css")) + sorted(root.glob("*.js")):
            if p.is_file():
                try:
                    h.update(p.read_bytes())
                except Exception:  # noqa: BLE001
                    pass
    return h.hexdigest()[:8]


# Jinja2Templates mirrors main.py's setup: same directory, same chrome context
# processor (so header/footer/nav/switcher inject automatically), same asset_ver
# global. Creating a local instance avoids importing from main.py (circular import
# once main.py wires this router in via app.include_router).
templates = Jinja2Templates(
    directory=str(BASE / "templates"),
    context_processors=[chrome.ark_context],
)
templates.env.globals["asset_ver"] = _asset_ver(STATIC)


def _f(val: str | None) -> float | None:
    """Parse a CSV cell to float; empty string → None (missing)."""
    if val is None:
        return None
    val = val.strip()
    return float(val) if val != "" else None


# ---------------------------------------------------------------------------
# Data loaders (real CSVs shipped with the app, self-contained
# in app/data/). Loaded once at import; every figure traces to these rows.
# ---------------------------------------------------------------------------

def _load_unemployment_ratio() -> list[dict]:
    """BLS CPS annual unemployment by race (1972–2025) + Black/White ratio."""
    rows: list[dict] = []
    with open(DATA / "unemployment_ratio.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "year": int(row["year"]),
                    "white": _f(row["white_unemployment"]),
                    "black": _f(row["black_unemployment"]),
                    "ratio": _f(row["black_white_ratio"]),
                    "gap_pp": _f(row["black_white_gap_pp"]),
                    "hispanic": _f(row["hispanic_unemployment"]),
                    "asian": _f(row["asian_unemployment"]),
                }
            )
    return rows


def _load_recession_peaks() -> list[dict]:
    """Unemployment peaks by race across NBER-dated recessions."""
    rows: list[dict] = []
    with open(DATA / "unemployment_recession_peaks.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "recession": row["recession"],
                    "peak": row["peak"],
                    "trough": row["trough"],
                    "black_peak": _f(row["Black_peak"]),
                    "white_peak": _f(row["White_peak"]),
                    "hispanic_peak": _f(row["Hispanic_peak"]),
                    "asian_peak": _f(row["Asian_peak"]),
                }
            )
    return rows


def _load_income_ratio() -> list[dict]:
    """Census ACS median household income by race (real 2022 dollars) + ratio."""
    rows: list[dict] = []
    with open(DATA / "income_ratio.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "year": int(row["year"]),
                    "black_real": _f(row["Black_real_2022"]),
                    "white_real": _f(row["White_real_2022"]),
                    "ratio": _f(row["black_white_ratio"]),
                }
            )
    return rows


def _load_poverty_gap() -> list[dict]:
    """Census ACS poverty rate by race + Black/White ratio."""
    rows: list[dict] = []
    with open(DATA / "poverty_gap.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "year": int(row["year"]),
                    "black": _f(row["black_poverty_rate"]),
                    "white": _f(row["white_poverty_rate"]),
                    "hispanic": _f(row["hispanic_poverty_rate"]),
                    "ratio": _f(row["black_white_poverty_ratio"]),
                }
            )
    return rows


def _load_housing() -> list[dict]:
    """Census ACS / HVS homeownership rate by race (2005–2022)."""
    rows: list[dict] = []
    with open(DATA / "housing_ownership_gap.csv", "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "year": int(row["year"]),
                    "white": _f(row["white_rate"]),
                    "black": _f(row["black_rate"]),
                    "hispanic": _f(row["hispanic_rate"]),
                    "asian": _f(row["asian_rate"]),
                    "gap_pp": _f(row["black_white_gap_pp"]),
                }
            )
    return rows


UNEMPLOYMENT_RATIO = _load_unemployment_ratio()
RECESSION_PEAKS = _load_recession_peaks()
INCOME_RATIO = _load_income_ratio()
POVERTY_GAP = _load_poverty_gap()
HOUSING = _load_housing()


# ---------------------------------------------------------------------------
# Page routes — each TemplateResponse inherits the chrome context automatically.
# ---------------------------------------------------------------------------

@router.get("/employment", response_class=HTMLResponse)
def employment(request: Request) -> HTMLResponse:
    """Black/White unemployment ratio (1972–2025) with NBER recession shading."""
    return templates.TemplateResponse(
        "employment.html",
        {
            "request": request,
            "unemployment": UNEMPLOYMENT_RATIO,
            "recessions": RECESSION_PEAKS,
        },
    )


@router.get("/income-poverty", response_class=HTMLResponse)
def income_poverty(request: Request) -> HTMLResponse:
    """Median income ratio + poverty rate by race; income-gap vs wealth-gap contrast."""
    return templates.TemplateResponse(
        "income_poverty.html",
        {
            "request": request,
            "income": INCOME_RATIO,
            "poverty": POVERTY_GAP,
        },
    )


@router.get("/housing", response_class=HTMLResponse)
def housing(request: Request) -> HTMLResponse:
    """Homeownership rate by race (2005–2022); the 27-point Black/White gap."""
    return templates.TemplateResponse(
        "housing.html",
        {
            "request": request,
            "housing": HOUSING,
        },
    )
