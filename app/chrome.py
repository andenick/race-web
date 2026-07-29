"""Arcanum Site Kit (ASK) v1 — shared-chrome context processor for DuBois.

Single mechanism that injects the shared header/footer/switcher variables into
**every** Jinja template render, regardless of which route builds the per-route
context. Wired in ``main.py`` via::

    Jinja2Templates(directory=..., context_processors=[chrome.ark_context])

Starlette runs each context processor for every ``TemplateResponse`` (it receives
the ``Request`` and returns a dict merged into the context), so no per-route edits
are needed.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from starlette.requests import Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-site identity (the only values another site changes)
# ---------------------------------------------------------------------------
SITE_KEY: str = "race"            # ecosystem.json site.key -> switcher "current"
SITE_TITLE: str = "DuBois"        # display name next to the Arcanum brand
SITE_HOME: str = "/"              # what the site title links to
DPR_URL: str = "/methodology"     # DuBois's provenance / methodology page (footer link)

# Blueprint nav vocabulary. All 15 routes are live; the dimension pages are the
# core content and the utility pages (Explore/Data/Code/Methodology/About) close
# the blueprint. Order: the six headline dimensions first, then Geography &
# History, then the blueprint utility sections.
NAV: list[tuple[str, str]] = [
    ("Wealth Gap",      "/wealth-gap"),
    ("Employment",      "/employment"),
    ("Income & Poverty", "/income-poverty"),
    ("Housing",         "/housing"),
    ("Criminal Justice", "/criminal-justice"),
    ("Education",       "/education"),
    ("Business",        "/business"),
    ("Geography",       "/geography"),
    ("History",         "/history"),
    ("Explore",         "/explore"),
    ("Data",            "/data"),
    ("Code",            "/code"),
    ("Methodology",     "/methodology"),
    ("About",           "/about"),
]

# Vendored canonical manifest (served at /static/_shared/ecosystem.json).
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_ECOSYSTEM_PATH = _STATIC_DIR / "_shared" / "ecosystem.json"


@lru_cache(maxsize=1)
def load_ecosystem() -> dict:
    """Parse the vendored ecosystem.json once (cached). Non-fatal on error."""
    try:
        with open(_ECOSYSTEM_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001 — chrome must never break a render
        logger.warning("ecosystem.json not loaded (%s): %s", _ECOSYSTEM_PATH, exc)
        return {}


def _nav_for(path: str) -> list[dict]:
    """Build the nav list with ``active`` set from the current request path."""
    items: list[dict] = []
    for label, href in NAV:
        active = path == href or (href != "/" and path.startswith(href + "/"))
        items.append({"label": label, "href": href, "active": active})
    return items


@lru_cache(maxsize=1)
def load_cdf() -> dict:
    """This site's CDF block (ecosystem schema v3) for the footer triad."""
    eco = load_ecosystem()
    for site in eco.get("sites", []):
        if site.get("key") == SITE_KEY:
            return site.get("cdf") or {}
    return {}


def ark_context(request: Request) -> dict:
    """Starlette context processor — runs for every TemplateResponse."""
    return {
        "site_key": SITE_KEY,
        "site_title": SITE_TITLE,
        "site_home": SITE_HOME,
        "dpr_url": DPR_URL,
        "ecosystem": load_ecosystem(),
        "cdf": load_cdf(),
        "nav": _nav_for(request.url.path),
    }
