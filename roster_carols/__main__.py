"""CLI:  python -m roster_carols samples/lopsided-band.xlsx --piece joy-to-the-world --grade 1 --out out/"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import roster as rmod
from .arrange import arrange, fit_report_text


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="roster_carols", description=__doc__)
    ap.add_argument("roster", help=".xlsx or .csv roster (one row per student, or instrument + count)")
    ap.add_argument("--piece", default="joy-to-the-world", help="carol id or title, or a Bach chorale's BWV number (e.g. 368)")
    ap.add_argument("--grade", default="1", choices=["0.5", "1", "2", "3", "4", "5"])
    ap.add_argument("--parts", default="single", choices=["single", "multiple"],
                    help="single: one part per instrument; multiple: split sections (Flute 1, Flute 2...)")
    ap.add_argument("--key", default=None,
                    help='concert key to use, e.g. "Bb major" (default: pick the best-fitting key)')
    ap.add_argument("--out", default="out", help="output folder")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    path = Path(a.roster)
    r = rmod.parse_upload(path.name, path.read_bytes())
    print("Roster:", ", ".join(f"{k} {v}" for k, v in r.ordered_counts().items()))
    if r.unrecognized:
        print("Unrecognised (left out):", ", ".join(f"{k} x{v}" for k, v in r.unrecognized.items()))

    chorale_id = a.piece
    res = arrange(chorale_id, r.ordered_counts(), a.grade, parts_mode=a.parts, key_choice=a.key)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in res["parts"]:
        (out / p["filename"]).write_text(p["musicxml"], encoding="utf-8")
    report = fit_report_text(res)
    (out / "fit-report.txt").write_text(report, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print()
    print(report)
    print(f"Wrote {len(res['parts'])} parts + fit-report.txt to {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
