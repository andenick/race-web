"""DuBois — Group E routes: /data, /code, /about.

Three content pages + a path-traversal-safe download route for the published CSVs.

This module is self-contained: it creates its own ``Jinja2Templates`` instance that
reuses the shared ASK chrome context processor (``app.chrome.ark_context``), so every
render inherits the same header/footer/nav/ecosystem chrome as the existing pages &
mdash; without importing from ``app.main`` (which would create a circular import once
the orchestrator wires this router in). The ``asset_ver`` cache-buster is recomputed
identically to ``app.main`` (same static files &rArr; same hash).

DO NOT import from app.main. The orchestrator does ``app.include_router(router)``.
"""
from __future__ import annotations

import csv
import hashlib
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app import chrome  # shared-chrome context processor (same as main.py)

logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
STATIC = BASE / "static"
TEMPLATES_DIR = BASE / "templates"

router = APIRouter()

# The only formats this site publishes. Used by BOTH the /data listing and the
# download route, so a file can never be reachable that the page does not list.
DOWNLOADABLE_SUFFIXES = (".csv", ".cff")

# ---------------------------------------------------------------------------
# Templates — own instance, same chrome context processor (no circular import)
# ---------------------------------------------------------------------------
templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR),
    context_processors=[chrome.ark_context],
)


def _asset_ver(static_dir: Path) -> str:
    """Short content hash of the vendored kit + site css/js — identical to app.main."""
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


templates.env.globals["asset_ver"] = _asset_ver(STATIC)


# ---------------------------------------------------------------------------
# Descriptions — grounded in the real data_dictionary.csv + source headers.
# These are curated 1-liners written from reading the published files; the
# route below only ever lists files that physically exist in app/data/.
# ---------------------------------------------------------------------------
_FILE_DESCRIPTIONS: dict[str, str] = {
    # P1 — Wealth (Fed SCF)
    "wealth_by_race_timeseries.csv":
        "Weighted median & mean net worth by race, 1989–2022 in 2022 USD (Fed SCF, 12 waves).",
    "wealth_gap_timeseries.csv":
        "Black median wealth as % of White, 1989–2022 (headline wealth-gap series; Fed SCF).",
    "wealth_by_race_2022.csv":
        "Asset composition by race, 2022 — home equity, financial assets, debt (Fed SCF).",
    "wealth_gap_summary_2022.csv":
        "2022 Black–White wealth gap summary: ratio, absolute gap, and % of White wealth.",
    # P2 — Income (Census ACS B19013)
    "income_ratio.csv":
        "Median household income by race (nominal & real 2022$) and Black/White ratio, 2005–2022.",
    # P3 — Employment (BLS CPS via FRED)
    "unemployment_annual.csv":
        "Annual average unemployment rate by race (seasonally adjusted), 1954–2025.",
    "unemployment_ratio.csv":
        "Black/White unemployment ratio and gap in percentage points, 1972–2025 (~2× headline).",
    "unemployment_recession_peaks.csv":
        "Peak unemployment by race across 7 NBER recessions, 1973–2020.",
    # P4 — Poverty (Census ACS B17001)
    "poverty_gap.csv":
        "Poverty rate by race, Black/White poverty ratio and gap (pp), 2005–2022.",
    # P5 — Housing (Census ACS B25003)
    "housing_ownership_gap.csv":
        "Homeownership rate by race and Black/White gap, 2005–2022.",
    # P6 — Education (Census ACS C15002)
    "education_attainment_gap.csv":
        "Bachelor's+ attainment by race and Black/White ratio, 2006–2022.",
    # P8 — Criminal justice (BJS)
    "imprisonment_by_race.csv":
        "Imprisonment rate per 100,000 by race and Black/White ratio, 2010–2020 (BJS Prisoners 2020).",
    # P9 — Business (Census ABS)
    "business_ownership_by_race.csv":
        "Employer firms, employees, and payroll by owner race, 2018–2021 (Census ABS).",
    # P10 — Demographics (MeasuringWorth + HSUS + ACS)
    "demographics_population.csv":
        "Annual US total population (1790–2024) plus Black/AA and Hispanic counts (ACS).",
    "demographics_race_shares.csv":
        "Race population shares (Black, White, Asian, Hispanic) as % of total, 2005–2022.",
    "demographics_crosscheck.csv":
        "Cross-source validation: MeasuringWorth vs HSUS census counts (avg 99.8% agreement).",
    # P12 — Historical (SlaveVoyages)
    "slavetrade_annual.csv":
        "Trans-Atlantic slave trade: voyages, embarked & disembarked persons, 1514–1866 (TAST 2019).",
    "slavetrade_by_region.csv":
        "Slave-trade voyages and disembarkments by region (SlaveVoyages TAST 2019).",
    "slavetrade_summary.csv":
        "Slave-trade aggregate summary statistics (SlaveVoyages TAST 2019).",
    # P13 — Geographic (Census ACS B19013A/B)
    "metro_income_gap_2022.csv":
        "Median household income by race by metro area, 2022 cross-section.",
    # Meta
    "data_dictionary.csv":
        "The data dictionary — per-series panel, units, year span, source, and notes for every column.",
    "CITATION.cff":
        "Citation File Format record — how to cite the DuBois dataset (CC-BY-4.0).",
}


def _load_dictionary_descriptions() -> dict[str, str]:
    """Read data_dictionary.csv and build a filename→source-span summary as a fallback.

    Used only for files that lack a curated entry, so the page never shows a bare
    placeholder for a real data file. Returns panel + span + source when available.
    """
    out: dict[str, str] = {}
    path = DATA_DIR / "data_dictionary.csv"
    if not path.is_file():
        return out
    rows: dict[str, list[dict]] = {}
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                fname = (r.get("filename") or "").strip()
                if fname:
                    rows.setdefault(fname, []).append(r)
    except Exception as exc:  # noqa: BLE001
        logger.warning("data_dictionary.csv read failed: %s", exc)
        return out
    for fname, entries in rows.items():
        spans = {e.get("year_span", "").strip() for e in entries if e.get("year_span")}
        sources = {e.get("source", "").strip() for e in entries if e.get("source")}
        span = sorted(spans)[0] if len(spans) == 1 else next(iter(spans), "")
        src = sorted(sources)[0] if len(sources) == 1 else next(iter(sources), "")
        bits = [b for b in (span, src) if b]
        if bits:
            out[fname] = " — ".join(bits)
    return out


_DICT_FALLBACK = _load_dictionary_descriptions()


def _format_for(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return {"csv": "CSV", "cff": "Citation (CFF)"}.get(ext, ext.upper())


def _list_data_files() -> list[dict]:
    """Build the real, present-on-disk list of downloadable files for the /data page.

    Only .csv and .cff files are listed (keeps internal JSON like headlines.json off
    the public download page). Order: curated descriptions first, then alphabetical.
    """
    files: list[dict] = []
    if not DATA_DIR.is_dir():
        return files
    for p in sorted(DATA_DIR.iterdir(), key=lambda x: x.name):
        if not p.is_file():
            continue
        if p.suffix.lower() not in DOWNLOADABLE_SUFFIXES:
            continue  # do not expose internal JSON artifacts as downloads
        desc = _FILE_DESCRIPTIONS.get(p.name) or _DICT_FALLBACK.get(p.name) or ""
        if not desc:
            desc = "See data_dictionary.csv for column-level provenance."
        files.append({
            "name": p.name,
            "description": desc,
            "format": _format_for(p.name),
        })
    return files


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/data", response_class=HTMLResponse)
def data_page(request: Request) -> HTMLResponse:
    """Downloads page — every published CSV + the data dictionary + citation record."""
    files = _list_data_files()
    n_csv = sum(1 for f in files if f["name"].endswith(".csv"))
    return templates.TemplateResponse(
        "data.html",
        {
            "request": request,
            "files": files,
            "n_csv": n_csv,
        },
    )


@router.get("/code", response_class=HTMLResponse)
def code_page(request: Request) -> HTMLResponse:
    """Code & reproducibility page — describes the real loader/processor pipeline."""
    return templates.TemplateResponse("code.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request) -> HTMLResponse:
    """About page — the W.E.B. Du Bois namesake and the dataset's purpose."""
    return templates.TemplateResponse("about.html", {"request": request})


@router.get("/data/files/{name}")
def download_file(name: str) -> FileResponse:
    """Serve a single file from app/data/ with path-traversal protection.

    Safety layers (defense in depth):
      1. ``{name}`` is a single path segment (no ``/``) by FastAPI default.
      2. Reject any name containing a path separator or ``..``.
      3. Resolve the target and assert it is *inside* DATA_DIR.
      4. Assert the resolved path is an existing regular file.
      5. Only serve files actually on disk (no synthesis).
      6. Extension allowlist — only the formats the /data page publishes. This keeps
         internal artefacts (headlines.json, series_registry.json) unreachable even by
         direct URL, and keeps the site's offered formats consistent with the download
         standard, which does not publish JSON.
    """
    # Layer 2 — reject traversal artefacts outright.
    if not name or "/" in name or "\\" in name or ".." in name or "\x00" in name:
        raise HTTPException(status_code=404, detail="Not found")

    # Layer 6 — allowlist the published extensions.
    if not name.lower().endswith(DOWNLOADABLE_SUFFIXES):
        raise HTTPException(status_code=404, detail="Not found")

    base = DATA_DIR.resolve()
    target = (DATA_DIR / name).resolve()

    # Layer 3 — target must live inside DATA_DIR.
    try:
        target.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")

    # Layer 4+5 — must be a real file on disk.
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    media = "text/csv" if name.lower().endswith(".csv") else "application/octet-stream"
    return FileResponse(
        path=str(target),
        filename=name,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
