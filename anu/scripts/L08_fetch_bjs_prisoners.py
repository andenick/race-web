"""
L08 -- BJS Prisoners-in-2020 Loader (Panel 8)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads the Bureau of Justice Statistics "Prisoners in 2020 - Statistical
Tables" spreadsheet bundle and extracts Figure 2's data file
(imprisonment rate per 100,000 U.S. residents of each race/ethnicity, 2010-2020).

Source: Bureau of Justice Statistics, Prisoners in 2020 (NCJ 302776),
        E. Ann Carson (2021).
Download: https://bjs.ojp.gov/content/pub/sheets/p20st.zip  (contains p20stf02.csv)
Landing:  https://bjs.ojp.gov/library/publications/prisoners-2020
License: Public domain (US Government)

This is THE marquee criminal-justice-by-race series: the Black imprisonment
rate runs ~5-6x the White rate -- the harshest of all the DuBois ratios.

OUTPUT (data/raw/bjs/):
  p20stf02.csv  -- raw Figure 2 CSV extracted from the zip (parsed by P08)

If the URL changes, find the current "Prisoners in 2020" data-page link on the
BJS publication page above and place the extracted p20stf02.csv under
data/raw/bjs/ manually.
"""

from __future__ import annotations

import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
OUT_DIR = RAW / "bjs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://bjs.ojp.gov/content/pub/sheets/p20st.zip"
TARGET = OUT_DIR / "p20stf02.csv"
USER_AGENT = "race-anu-replication/1.0"


def main() -> int:
    if TARGET.exists():
        print(f"{TARGET.name} already present, skipping download")
        return 0
    zip_path = OUT_DIR / "p20st.zip"
    print(f"Downloading {URL} ...")
    req = urllib.request.Request(URL, headers={"User-Agent": USER_AGENT})
    try:
        zip_path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    except Exception as e:
        print(f"ERROR: download failed: {repr(e)[:120]}", file=sys.stderr)
        return 1
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = [n for n in z.namelist() if n.lower().endswith("p20stf02.csv")]
            if not names:
                print(f"ERROR: p20stf02.csv not in zip; members: {z.namelist()[:10]}",
                      file=sys.stderr)
                return 1
            TARGET.write_bytes(z.read(names[0]))
    except zipfile.BadZipFile:
        print("ERROR: downloaded file is not a valid zip", file=sys.stderr)
        return 1
    zip_path.unlink()
    print(f"Extracted {TARGET} ({TARGET.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
