"""
Batch mode - audit a whole folder of papers, emit a triage table.

This is the editorial-workflow shape: point Rigor at a submission queue (a directory
of PDFs or text files) and get back one row per paper - integrity score, error and
warning counts, extraction agreement - as JSON and CSV, sorted worst-first so an
editor screens the riskiest submissions first. The single-paper audit is the demo;
this is how the tool actually slots into a journal's or lab's pipeline.

Run:
    python -m rigor.batch ./submissions
    python -m rigor.batch ./submissions --csv out.csv --json out.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from rigor.audit import audit_text
from rigor.ingest import load_text

SUFFIXES = {".pdf", ".txt", ".md"}


def audit_folder(folder: str | Path) -> list[dict]:
    """Audit every paper in `folder`; return one summary row per file, worst score first."""
    root = Path(folder)
    if not root.exists():
        raise FileNotFoundError(root)
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in SUFFIXES)
    rows: list[dict] = []
    for path in files:
        row: dict = {"file": path.name}
        try:
            report = audit_text(load_text(path)).to_dict()
            row.update({
                "score": report["score"],
                "errors": report["errors"],
                "warnings": report["warnings"],
                "tests": report["n_tests"],
                "means": report["n_means"],
                "root_causes": len(report.get("hypotheses", [])),
                "agreement": report.get("extraction", {}).get("agreement", 1.0),
                "status": "ok",
            })
        except Exception as exc:  # noqa: BLE001 - one bad file shouldn't sink the batch
            row.update({"score": None, "errors": None, "warnings": None, "tests": None,
                        "means": None, "root_causes": None, "agreement": None,
                        "status": f"error: {type(exc).__name__}"})
        rows.append(row)
    # worst (lowest score) first; failed files sink to the bottom
    rows.sort(key=lambda r: (r["score"] is None, r["score"] if r["score"] is not None else 0))
    return rows


def write_csv(rows: list[dict], path: str | Path) -> None:
    cols = ["file", "score", "errors", "warnings", "tests", "means", "root_causes",
            "agreement", "status"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Audit a folder of papers for statistical integrity.")
    ap.add_argument("folder", help="directory of .pdf/.txt/.md papers")
    ap.add_argument("--csv", help="write a CSV summary to this path")
    ap.add_argument("--json", help="write a JSON summary to this path")
    ap.add_argument("--min-score", type=int, default=None,
                    help="exit non-zero if any paper scores below this (for CI gating)")
    args = ap.parse_args(argv)

    rows = audit_folder(args.folder)
    if not rows:
        print(f"No papers ({'/'.join(sorted(SUFFIXES))}) found in {args.folder}")
        return 1

    print(f"\n  Audited {len(rows)} paper(s), worst first:\n")
    print(f"  {'score':>5}  {'err':>3} {'warn':>4}  {'agree':>5}  file")
    print("  " + "-" * 60)
    for r in rows:
        score = "  -  " if r["score"] is None else f"{r['score']:>3}  "
        agree = "  -  " if r["agreement"] is None else f"{r['agreement']:>4.0%}"
        print(f"  {score}  {str(r['errors'] if r['errors'] is not None else '-'):>3} "
              f"{str(r['warnings'] if r['warnings'] is not None else '-'):>4}  {agree}  {r['file']}")

    if args.csv:
        write_csv(rows, args.csv)
        print(f"\n  CSV  -> {args.csv}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"  JSON -> {args.json}")

    if args.min_score is not None:
        below = [r for r in rows if r["score"] is not None and r["score"] < args.min_score]
        if below:
            print(f"\n  FAIL: {len(below)} paper(s) below the {args.min_score} threshold:")
            for r in below:
                print(f"    {r['score']:>3}  {r['file']}")
            return 1
        print(f"\n  PASS: all papers scored >= {args.min_score}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
