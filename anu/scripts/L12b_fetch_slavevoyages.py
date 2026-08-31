"""
L12b -- Trans-Atlantic Slave Trade (TAST) Loader (Panel 12)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads the SlaveVoyages Trans-Atlantic Slave Trade Database (2019 release,
`tastdb-exp-2019`, 36,108 voyages, 1514-1866).

Source: SlaveVoyages.org, Trans-Atlantic Slave Trade Database (2019 release)
Direct CSV: https://www.slavevoyages.org/static/uploads/tastdb-exp-2019.csv
Downloads page: https://www.slavevoyages.org/blog/the-transatlantic-slave-trade-database/163
Codebook: SPSS_Codebook_2019.pdf (same downloads page)
License: CC-BY (SlaveVoyages)

KEY VARIABLES (2019 schema; used by P12_construct_slavetrade.py):
  VOYAGEID  voyage id
  YEARAM    year of voyage/arrival (main date)
  SLAXIMP   slaves embarked (imputed)
  SLAMIMP   slaves disembarked (imputed)
  REGARR    broad region of arrival (hierarchical: 20000-range = Mainland N. America)

OUTPUT (data/raw/slavevoyages/):
  tastdb-exp-2019.csv  -- the full voyage-level database (~25-30 MB)

If the direct link moves, follow the Download links on the downloads page above and place the CSV at
data/raw/slavevoyages/tastdb-exp-2019.csv.
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = RAW / "slavevoyages"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://www.slavevoyages.org/static/uploads/tastdb-exp-2019.csv"
DEST = OUT_DIR / "tastdb-exp-2019.csv"
USER_AGENT = "race-anu-replication/1.0"


def main() -> int:
    if DEST.exists() and DEST.stat().st_size > 1_000_000:
        print(f"{DEST.name} already present ({DEST.stat().st_size:,} bytes), skipping")
        return 0
    print(f"Downloading TAST 2019 database (~25-30 MB) from {URL} ...")
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, DEST.open("wb") as fh:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
    except Exception as e:
        print(f"ERROR: download failed: {repr(e)[:120]}\n"
              "  Manual fallback: https://www.slavevoyages.org/blog/the-transatlantic-slave-trade-database/163",
              file=sys.stderr)
        return 1
    size = DEST.stat().st_size
    print(f"Wrote {DEST} ({size:,} bytes)")
    if size < 5_000_000:
        print("WARNING: file smaller than expected for the full 2019 database",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
