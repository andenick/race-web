"""DuBois — Group C routes: criminal justice, education, business.

A self-contained FastAPI ``APIRouter`` (named ``router``) wired into the app via::

    from app.routes_groupC import router
    app.include_router(router)

It owns its own ``Jinja2Templates`` instance built with the same ASK v1 shared-chrome
context processor (``chrome.ark_context``) as ``main.py``, so it never edits
``main.py`` or ``chrome.py``. ``asset_ver`` is computed locally from the same vendored
kit files, so cache-busting stays identical to the rest of the site.

All figures trace to real public-source data. Nothing is
fabricated.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app import chrome  # ASK v1 — shared-chrome context processor

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATIC = BASE / "static"

router = APIRouter()


def _asset_ver(static_dir: Path) -> str:
    """Short content hash of the vendored kit + site css/js — mirrors main.py."""
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


# Own templates instance (same context processor) — no shared-file edits.
templates = Jinja2Templates(
    directory=str(BASE / "templates"),
    context_processors=[chrome.ark_context],
)
templates.env.globals["asset_ver"] = _asset_ver(STATIC)


# ---------------------------------------------------------------------------
# Data loaders — real CSVs, parsed into plain dicts for the templates.
# ---------------------------------------------------------------------------

def _load_imprisonment() -> list[dict]:
    """Imprisonment rate per 100,000 by race, 2010–2020 (BJS Prisoners series)."""
    rows: list[dict] = []
    with open(DATA / "imprisonment_by_race.csv", "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "year": int(row["year"]),
                    "white": int(row["white_rate"]),
                    "black": int(row["black_rate"]),
                    "hispanic": int(row["hispanic_rate"]),
                    "aian": int(row["aian_rate"]),
                    "asian": int(row["asian_rate"]),
                    "black_white_ratio": float(row["black_white_ratio"]),
                    "black_white_gap": int(row["black_white_gap"]),
                }
            )
    return rows


def _load_education() -> list[dict]:
    """Bachelor's-or-higher attainment (%) by race, 2006–2022 (Census ACS C15002)."""
    rows: list[dict] = []
    with open(DATA / "education_attainment_gap.csv", "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "year": int(row["year"]),
                    "white": float(row["White_bachelors_pct"]),
                    "black": float(row["Black_bachelors_pct"]),
                    "aian": float(row["AIAN_bachelors_pct"]),
                    "asian": float(row["Asian_bachelors_pct"]),
                    "hispanic": float(row["Hispanic_bachelors_pct"]),
                    "black_white_gap_pp": float(row["black_white_gap_pp"]),
                    "black_white_ratio": float(row["black_white_ratio"]),
                }
            )
    return rows


def _load_business() -> list[dict]:
    """Employer firms by owner race, 2018–2021 (Census ABS)."""
    rows: list[dict] = []
    with open(DATA / "business_ownership_by_race.csv", "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "year": int(row["year"]),
                    "race_group": int(row["race_group"]),
                    "race": row["race"],
                    "firms": int(row["firms"]),
                    "employees": int(row["employees"]),
                    "share_pct": float(row["share_of_firms_pct"]),
                }
            )
    return rows


IMPRISONMENT = _load_imprisonment()
EDUCATION = _load_education()
BUSINESS = _load_business()


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@router.get("/criminal-justice", response_class=HTMLResponse)
def criminal_justice(request: Request) -> HTMLResponse:
    """Imprisonment rate by race, 2010–2020 (BJS). Black/White ratio avg 5.49x."""
    return templates.TemplateResponse(
        "criminal_justice.html",
        {
            "request": request,
            "imprisonment": IMPRISONMENT,
        },
    )


@router.get("/education", response_class=HTMLResponse)
def education(request: Request) -> HTMLResponse:
    """Bachelor's+ attainment by race, 2006–2022 (Census ACS)."""
    return templates.TemplateResponse(
        "education.html",
        {
            "request": request,
            "education": EDUCATION,
        },
    )


@router.get("/business", response_class=HTMLResponse)
def business(request: Request) -> HTMLResponse:
    """Business ownership by race, 2018–2021 (Census ABS)."""
    return templates.TemplateResponse(
        "business.html",
        {
            "request": request,
            "business": BUSINESS,
        },
    )


# ---- JSON API over the real curated data (for client-side charts) ----

@router.get("/api/criminal-justice")
def api_criminal_justice() -> JSONResponse:
    """Imprisonment rate per 100,000 by race, 2010–2020 (BJS)."""
    return JSONResponse(IMPRISONMENT)


@router.get("/api/education")
def api_education() -> JSONResponse:
    """Bachelor's+ attainment (%) by race, 2006–2022 (Census ACS)."""
    return JSONResponse(EDUCATION)


@router.get("/api/business")
def api_business() -> JSONResponse:
    """Employer firms by owner race, 2018–2021 (Census ABS)."""
    return JSONResponse(BUSINESS)
