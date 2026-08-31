"""
V14 -- Registry Contract Validator (final gate)
Project: DuBois (Race, Stratification & Economic Disparities) -- public replication package

Checks the data/processed/ outputs against series_registry.json -- the data
contract of this package -- and on success promotes the validated series
files to data/final/. Exits non-zero on any failure.

CHECKS (per the Anu replication-package template):
  1. Series presence: every registry series' output file(s) exist under data/processed/
  2. Count match: files present == files declared (and 27 registry series)
  3. Unit sanity: per-series range/positivity rules from the registry's
     validation block (percent series in [0,100], ratios in their plausible
     bands, counts strictly positive)
  4. Coverage: each time-series file's year range matches the declared
     coverage (tolerance: min <= start+2, max >= end-2, accounting for
     data vintage); cross-sectionals must be non-empty
  5. No nulls in required columns
  6. Package hygiene: no workspace/internal path strings inside any shipped
     script, DPR, README, or the registry itself

OUTPUT: data/processed/VALIDATION_registry.md + data/final/ (on success)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # anu/
RAW = PKG_ROOT / "data" / "raw"
PROC = PKG_ROOT / "data" / "processed"
FINAL = PKG_ROOT / "data" / "final"
PROC.mkdir(parents=True, exist_ok=True)

REGISTRY = PKG_ROOT / "series_registry.json"
REPORT = PROC / "VALIDATION_registry.md"

RANGES = {
    "range_0_100": (0.0, 100.0),
    "range_0_40": (0.0, 40.0),
    "range_0_50": (0.0, 50.0),
    "range_0_1": (0.0, 1.0),
    "range_0_1_5": (0.0, 1.5),
    "range_0_3": (0.0, 3.0),
    "range_0_30": (0.0, 30.0),
    "range_1_3": (1.0, 3.0),
    "range_1_3_5": (1.0, 3.5),
    "range_3_8": (3.0, 8.0),
    "range_1_5_3": (1.5, 3.0),
    "range_0_4_0_8": (0.4, 0.8),
    "range_20_70": (20.0, 70.0),
    "range_open_35": (0.0, 35.0),   # open at 0 (exclusive)
    "range_open_30": (0.0, 30.0),
}

# Built from fragments so this file does not itself contain the literals it bans.
FORBIDDEN_STRINGS = tuple("".join(parts) for parts in [
    ("D:", "/", "Arcanum"),
    ("D:", "\\", "Arcanum"),
    ("Council", "/", "Robin"),
    ("clair", "_", "database"),
    ("34698fc", "70a13bd2943ebbd4e720192030e5a824f"),
])


def _load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def check_series(entry: dict, lines: list[str], fails: list[str]) -> None:
    sid = entry["series_id"]
    v = entry["validation"]
    f = PROC / v["file"]
    if not f.exists():
        lines.append(f"- **{sid}.presence**: FAIL -- missing {v['file']}")
        fails.append(f"{sid}.presence")
        return

    rows = _load_csv(f)
    if not rows:
        lines.append(f"- **{sid}.presence**: FAIL -- {v['file']} is empty")
        fails.append(f"{sid}.presence")
        return

    problems: list[str] = []

    # 5. no nulls in required columns
    for col in v.get("required_non_null", []):
        n_null = sum(1 for r in rows if r.get(col) in (None, "", "nan", "NaN"))
        if n_null:
            problems.append(f"{n_null} null(s) in {col}")

    # 3. unit sanity
    for col in v.get("positive", []):
        for r in rows:
            try:
                if float(r.get(col) or "nan") <= 0:
                    problems.append(f"non-positive {col}={r.get(col)}")
                    break
            except ValueError:
                problems.append(f"non-numeric {col}={r.get(col)}")
                break
    for key, cols in v.items():
        if key.startswith("range_") and key in RANGES:
            lo, hi = RANGES[key]
            for col in cols:
                for r in rows:
                    try:
                        x = float(r.get(col) or "nan")
                    except ValueError:
                        problems.append(f"non-numeric {col}={r.get(col)}")
                        break
                    if not (lo < x <= hi if key.startswith("range_open") else lo <= x <= hi):
                        problems.append(f"{col}={x} outside [{lo},{hi}]")
                        break

    # 4. coverage
    ycol = v.get("year_column")
    if ycol:
        try:
            years = sorted(int(float(r[ycol])) for r in rows if r.get(ycol))
            start, end = int(entry["coverage"]["start"]), int(entry["coverage"]["end"])
            if years[0] > start + 2:
                problems.append(f"first year {years[0]} > declared start {start}+2")
            if years[-1] < end - 2:
                problems.append(f"last year {years[-1]} < declared end {end}-2")
        except (ValueError, KeyError, TypeError):
            problems.append(f"year column {ycol} unparseable")

    status = "PASS" if not problems else "FAIL"
    if problems:
        fails.append(sid)
    lines.append(f"- **{sid}**: {status} -- {v['file']} ({len(rows)} rows)"
                 + (f" [{'; '.join(problems[:4])}]" if problems else ""))


def check_package_hygiene(lines: list[str], fails: list[str]) -> None:
    hits = []
    for p in sorted(PKG_ROOT.rglob("*")):
        rel = p.relative_to(PKG_ROOT).as_posix()
        if p.is_dir() or rel.startswith("data/"):
            continue
        if p.suffix not in {".py", ".md", ".json", ".txt", ".cff", ""}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for needle in FORBIDDEN_STRINGS:
            if needle in text:
                hits.append(f"{p.relative_to(PKG_ROOT)} contains {needle[:24]!r}")
    if hits:
        fails.append("package_hygiene")
        lines.append(f"- **package_hygiene**: FAIL -- " + "; ".join(hits[:6]))
    else:
        lines.append("- **package_hygiene**: PASS -- no workspace paths or secrets in shipped files")


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    series = reg["series"]
    lines = [f"# V14 Registry Contract Validation\n",
             f"Registry: {len(series)} series\n"]

    # 1+2+3+4+5 per series
    fails: list[str] = []
    for entry in series:
        check_series(entry, lines, fails)

    # 2. count match: every declared file present
    declared = {out for e in series for out in e["output"]}
    present = {p.name for p in PROC.glob("*.csv")}
    missing = declared - present
    if missing:
        fails.append("count_match")
        lines.append(f"- **count_match**: FAIL -- declared outputs not produced: {sorted(missing)}")
    else:
        lines.append(f"- **count_match**: PASS -- all {len(declared)} declared output files present")

    # 6. package hygiene
    check_package_hygiene(lines, fails)

    lines.append(f"\n## Result: {'PASS' if not fails else 'FAIL (' + ', '.join(fails) + ')'}")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    # promote to final/ only on full success
    if not fails:
        FINAL.mkdir(parents=True, exist_ok=True)
        import shutil
        promoted = 0
        for e in series:
            for out in e["output"]:
                src, dst = PROC / out, FINAL / out
                if src.exists():
                    shutil.copy2(src, dst)
                    promoted += 1
        print(f"\nPromoted {promoted} validated files to {FINAL}")
        return 0
    print(f"\nNOT promoted to data/final/ ({len(fails)} failing checks)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
