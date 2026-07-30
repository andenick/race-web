"""DuBois — race.heterodata.org (FastAPI + Jinja2 + Plotly on ASK v1).

Named for W.E.B. Du Bois, who pioneered the empirical study of race and economic
stratification. This site presents race-disaggregated US economic data across six
measurable dimensions — wealth, income, employment, poverty, housing, and criminal
justice — reconstructed from authoritative public sources (Census, Federal Reserve,
BLS, BJS).

Shared site chrome + the Landing page (6-dimension hierarchy chart) + the
north-star /wealth-gap page. All figures trace to real public-source data.
Nothing is fabricated.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Carson Telemetry Standard §4 (Layer-3 usage events). HARD import, deliberately:
# no try/except, no "telemetry is optional in dev" guard. StarCruiser wrapped this
# same import in try/except while its Dockerfile also failed to install the
# vendored package, and the two defects cancelled each other into silence — the
# site served traffic uncounted from 2026-06-30 to 2026-07-29 and nobody could
# tell. A site that cannot answer "is anyone using this?" is the defect; failing
# loudly at startup is the fix.
from carson_telemetry import telemetry

from app import chrome  # ASK v1 — shared-chrome context processor

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATIC = BASE / "static"

# Service tag on every telemetry line.
SERVICE_TAG = "race-web"

logger = logging.getLogger("dubois")


def _asset_ver(static_dir: Path) -> str:
    """Short content hash of the vendored kit + site css/js — busts cache on deploy."""
    import hashlib

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


app = FastAPI(title="DuBois - Race, Stratification & Economic Disparities")

# One usage_events row per HTTP request, into the SQLite DB at $CARSON_TELEMETRY_DB on
# the writable telemetry volume (see docker-compose.yml). Any dashboard over that DB
# groups by this `service` column, so renaming it orphans the history — keep it "race"
# (the site key), NOT "race-web" (the container name) and NOT "dubois" (the display
# title).
#
# ONE SERVICE LABEL, deliberately. Sites that generate first-party probe traffic at
# volume — a 30 s /healthz healthcheck is ~2,880 self-requests/day, and a paint canary
# can easily out-number real visitors — must tag their own probes under a separate
# service="<site>-synthetic" label, or the numbers measure the monitoring rather than
# the audience. This site declares no healthcheck and is not probed by an uptime
# monitor, so it has no such traffic to separate out and the plain single-label wiring
# is correct.
#
# ⚠ IF A HEALTHCHECK OR AN UPTIME MONITOR IS EVER ADDED TO THIS SITE, ADD THE
# SYNTHETIC-LABEL SPLIT HERE **FIRST**, in the same change — not after. Probe traffic
# added before the split exists is not merely noisy, it is unseparable after the fact:
# the classifier throws the user-agent away by design (privacy contract), so the rows
# it would have used to tell probes from people no longer carry the evidence. Split
# first, then probe.
#
# NOTE ON UA MARKERS: "curl/" and "wget/" are deliberately NOT treated as synthetic.
# This site ships /llms.txt and stable bundle URLs precisely to invite programmatic
# consumers; classifying them as robots would erase the audience those exist to serve.
# First-party smoke tests DECLARE themselves with a header instead.
app.add_middleware(telemetry.ASGIMiddleware, service="race")

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(
    directory=str(BASE / "templates"),
    context_processors=[chrome.ark_context],
)
templates.env.globals["asset_ver"] = _asset_ver(STATIC)

# --- Content routers (12 further pages, grouped by subject) ---
from app.routes_groupB import router as _groupB_router
from app.routes_groupC import router as _groupC_router
from app.routes_groupD import router as _groupD_router
from app.routes_groupE import router as _groupE_router

app.include_router(_groupB_router)
app.include_router(_groupC_router)
app.include_router(_groupD_router)
app.include_router(_groupE_router)


def _load_json(name: str) -> dict:
    with open(DATA / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_wealth_gap() -> list[dict]:
    """Load the wealth-gap timeseries CSV into a list of dicts (real data)."""
    rows: list[dict] = []
    with open(DATA / "wealth_gap_timeseries.csv", "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "year": int(row["year"]),
                    "white": int(row["white_median_networth"]),
                    "black": int(row["black_median_networth"]),
                    "black_pct": float(row["black_pct_of_white"]),
                }
            )
    return rows


HEADLINES = _load_json("headlines.json")
WEALTH_GAP = _load_wealth_gap()


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> str:
    return "ok"


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt() -> PlainTextResponse:
    """Agent-first site map, generated from ecosystem.json and served from the site
    root, where automated clients look for it."""
    path = STATIC / "llms.txt"
    if not path.is_file():
        return PlainTextResponse("not found", status_code=404)
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/plain")


@app.post("/__track")
async def track(request: Request) -> Response:
    """First-party usage beacon sink for ark-track.js / ark-triad.js.

    No cookies, no PII, no third party: records only the site tag, the path, the
    referring hostname and a server-stamped time to the application log. The
    client honours DNT/GPC before it ever posts. Returns 204 with no body so a
    keepalive beacon costs the visitor nothing.
    """
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 — a malformed beacon must never 500
        body = {}
    if isinstance(body, dict):
        logger.info(
            "usage service=%s site=%s path=%s ref=%s surface=%s endpoint=%s",
            SERVICE_TAG,
            str(body.get("site", ""))[:64],
            str(body.get("path", ""))[:200],
            str(body.get("ref", ""))[:128],
            str(body.get("surface", "web"))[:32],
            str(body.get("endpoint", ""))[:64],
        )
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Landing page: what+why + the 6-dimension hierarchy chart + entry cards."""
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "headlines": HEADLINES,
        },
    )


@app.get("/wealth-gap", response_class=HTMLResponse)
def wealth_gap(request: Request) -> HTMLResponse:
    """North-star page: Black median wealth as % of White, 1989–2022 (Fed SCF)."""
    return templates.TemplateResponse(
        "wealth-gap.html",
        {
            "request": request,
            "wealth": WEALTH_GAP,
        },
    )


@app.get("/methodology", response_class=HTMLResponse)
def methodology(request: Request) -> HTMLResponse:
    """Methodology / provenance page (prose; DPR target for the footer link)."""
    return templates.TemplateResponse(
        "methodology.html",
        {"request": request},
    )


# ---- JSON API over the real curated data (for client-side charts) ----

@app.get("/api/hierarchy")
def api_hierarchy() -> JSONResponse:
    """The 6-dimension stratification hierarchy (real ratios from public sources)."""
    return JSONResponse(HEADLINES["hierarchy"])


@app.get("/api/wealth-gap")
def api_wealth_gap() -> JSONResponse:
    """The Black–White wealth-gap timeseries (Fed SCF, 1989–2022, 12 waves)."""
    return JSONResponse(WEALTH_GAP)
