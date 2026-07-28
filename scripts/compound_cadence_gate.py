"""Compound cadence advisory gate.

Counts reviews/REVIEW-* vs reviews/COMPOUND-* + reviews/RETRO-* files and
emits a non-blocking watch finding when the ratio exceeds --ratio (default 20),
indicating that lessons are being reviewed but rarely compounded.

Exit 0 always (advisory/watch-only). ASCII output.

JSON report shape (--json)
--------------------------
    {
      "schema": "agent-runtime-compound-cadence/v1",
      "root": "<absolute repo root>",
      "generated_at": "<local iso timestamp>",
      "status": "pass" | "watch",
      "counts": {
        "reviews": N,
        "compounds": N,
        "retros": N,
        "compound_retro_total": N,
        "ratio": N.N          # reviews / compound_retro_total, null when 0 compounds
      },
      "findings": [
        {
          "severity": "watch",
          "code": "compound-cadence",
          "reviews": N,
          "compound_retro_total": N,
          "ratio": N.N,
          "threshold_ratio": N,
          "detail": "<human text>"
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

try:
    import compound_record
except ImportError:  # imported as scripts.<name>
    from scripts import compound_record

REPORT_SCHEMA = "agent-runtime-compound-cadence/v1"
REVIEWS_DIR = Path("reviews")
DEFAULT_RATIO = 20


def _local_iso() -> str:
    text = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )
    if len(text) >= 5 and text[-5] in "+-":
        text = text[:-2] + ":" + text[-2:]
    return text


def _count_files(reviews_dir: Path) -> tuple[int, int, int]:
    """Return (review_count, compound_count, retro_count)."""
    if not reviews_dir.is_dir():
        return 0, 0, 0
    review_count = sum(1 for _ in reviews_dir.glob("REVIEW-*"))
    compound_count = sum(1 for _ in reviews_dir.glob("COMPOUND-*"))
    retro_count = sum(1 for _ in reviews_dir.glob("RETRO-*"))
    return review_count, compound_count, retro_count


def _count_all(root: Path) -> tuple[int, int, int, int]:
    review_count, legacy_compounds, retro_count = _count_files(root / REVIEWS_DIR)
    try:
        canonical_compounds = len(compound_record.load_records(root))
    except compound_record.CompoundRecordError:
        # Invalid records are not credited toward cadence. The compound-record
        # integrity check reports the concrete malformed-store finding.
        canonical_compounds = 0
    return (
        review_count,
        legacy_compounds + canonical_compounds,
        retro_count,
        canonical_compounds,
    )


def analyze(root: Path, *, ratio: int = DEFAULT_RATIO) -> list[dict[str, Any]]:
    """Analyze reviews under root and return a list of finding dicts."""
    root = root.resolve()
    review_count, compound_count, retro_count, _canonical_count = _count_all(root)

    compound_retro_total = compound_count + retro_count
    findings: list[dict[str, Any]] = []

    if review_count == 0:
        return findings

    if compound_retro_total == 0:
        actual_ratio: float | None = None
        triggered = True
    else:
        actual_ratio = review_count / compound_retro_total
        triggered = actual_ratio > ratio

    if triggered:
        ratio_display = f"{actual_ratio:.1f}" if actual_ratio is not None else "inf (no compounds/retros)"
        findings.append(
            {
                "severity": "watch",
                "code": "compound-cadence",
                "reviews": review_count,
                "compound_retro_total": compound_retro_total,
                "ratio": actual_ratio,
                "threshold_ratio": ratio,
                "detail": (
                    f"{review_count} REVIEW-* vs {compound_retro_total} COMPOUND-*/RETRO-*"
                    f" (ratio {ratio_display}, threshold {ratio});"
                    " consider compounding lessons into COMPOUND-* or RETRO-* documents"
                ),
            }
        )

    return findings


def build_report(
    root: Path,
    findings: list[dict[str, Any]],
    *,
    ratio: int = DEFAULT_RATIO,
) -> dict[str, Any]:
    root = root.resolve()
    review_count, compound_count, retro_count, canonical_count = _count_all(root)
    compound_retro_total = compound_count + retro_count

    if review_count > 0 and compound_retro_total > 0:
        actual_ratio: float | None = review_count / compound_retro_total
    elif review_count > 0:
        actual_ratio = None
    else:
        actual_ratio = None

    return {
        "schema": REPORT_SCHEMA,
        "root": str(root),
        "generated_at": _local_iso(),
        "status": "watch" if findings else "pass",
        "counts": {
            "reviews": review_count,
            "compounds": compound_count,
            "canonical_compounds": canonical_count,
            "retros": retro_count,
            "compound_retro_total": compound_retro_total,
            "ratio": actual_ratio,
        },
        "findings": findings,
    }


def render(
    root: Path,
    findings: list[dict[str, Any]],
    *,
    ratio: int = DEFAULT_RATIO,
) -> str:
    report = build_report(root, findings, ratio=ratio)
    counts = report["counts"]
    ratio_str = f"{counts['ratio']:.1f}" if counts["ratio"] is not None else "inf"
    lines = [
        f"compound-cadence-gate: {report['status']}",
        f"root={report['root']}",
        f"reviews={counts['reviews']}",
        f"compounds={counts['compounds']}",
        f"retros={counts['retros']}",
        f"compound_retro_total={counts['compound_retro_total']}",
        f"ratio={ratio_str}",
        f"threshold={ratio}",
        f"watch={len([f for f in findings if f['severity'] == 'watch'])}",
    ]
    for finding in findings:
        lines.append(
            f"- {finding['severity']} [{finding['code']}]: {finding['detail']}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compound cadence advisory gate (watch-only, exit 0)"
    )
    parser.add_argument("--check", action="store_true", help="Run check (always exits 0)")
    parser.add_argument(
        "--obligation",
        action="store_true",
        help="Soft obligation: exit 1 when a compound is overdue (--check stays exit 0)",
    )
    parser.add_argument(
        "--ratio",
        type=int,
        default=DEFAULT_RATIO,
        help="REVIEW/COMPOUND+RETRO ratio above which watch fires (default: 20)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    findings = analyze(root, ratio=args.ratio)
    if args.as_json:
        report = build_report(root, findings, ratio=args.ratio)
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(render(root, findings, ratio=args.ratio))
    # --obligation escalates the advisory to a soft non-zero when a compound is
    # overdue; --check (and bare invocation) always exit 0 (watch-only).
    if args.obligation and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
