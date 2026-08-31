"""
L01 -- Federal Reserve SCF Summary-File Loader (Panel 1: Wealth)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Downloads every triennial SCF summary file (the full public microdata extract)
used for the wealth-by-race series, the decompositions, and the reparations
counterfactual:

  ALL waves       : https://www.federalreserve.gov/econres/files/scfp{year}s.zip  (Stata .dta summary file inside)

Source: Board of Governors of the Federal Reserve System, Survey of Consumer Finances
Landing page: https://www.federalreserve.gov/econres/scfindex.htm
License: Public domain (US Federal Reserve)

OUTPUT (data/raw/scf/):
  {year}/...   -- each wave extracted into its own directory
                  (one .dta summary file per wave)

SCF RACE variable (2022 codebook; harmonized across waves in P01):
  1 = White non-Hispanic   2 = Black non-Hispanic   3 = Hispanic
  4 = Asian (2022 only)    5 = Other

NOTES:
  - Total download is roughly 150-250 MB across the 12 waves; each wave is
    skipped if its extraction directory already exists (idempotent re-runs).
  - The files are the FULL summary microdata (all five implicates). All
    statistics derived from them must use the sample weight (WGT); SCF
    oversamples wealthy households, so unweighted statistics are meaningless.
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
OUT_DIR = RAW / "scf"

HIST_YEARS = [1989, 1992, 1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019]
URL_HIST = "https://www.federalreserve.gov/econres/files/scfp{y}s.zip"
URL_2022 = "https://www.federalreserve.gov/econres/files/scfp2022s.zip"

USER_AGENT = "race-anu-replication/1.0"


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=180) as resp, dest.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def _fetch_wave(label: str, url: str) -> bool:
    """Download one wave zip and extract it to data/raw/scf/{label}/."""
    wave_dir = OUT_DIR / label
    if wave_dir.exists() and any(wave_dir.iterdir()):
        print(f"  {label}: already extracted, skipping")
        return True
    zip_path = OUT_DIR / f"{label}.zip"
    print(f"  {label}: downloading {url.rsplit('/', 1)[-1]} ...", flush=True)
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        _download(url, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            if bad is not None:
                print(f"  {label}: CORRUPT member {bad}", file=sys.stderr)
                return False
            wave_dir.mkdir(parents=True, exist_ok=True)
            z.extractall(wave_dir)
        zip_path.unlink()  # keep only the extracted wave
        n = len(list(wave_dir.rglob("*")))
        print(f"  {label}: extracted {n} files")
        return True
    except Exception as e:
        print(f"  {label}: FAILED {repr(e)[:120]}", file=sys.stderr)
        return False


def main() -> int:
    print("=== L01: Federal Reserve SCF summary files ===")
    ok = True
    for y in HIST_YEARS:
        ok &= _fetch_wave(str(y), URL_HIST.format(y=y))
    ok &= _fetch_wave("2022", URL_2022)
    if not ok:
        print("ERROR: one or more SCF waves failed to download", file=sys.stderr)
        return 1
    print(f"\nAll 12 SCF waves available under {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
