#!/usr/bin/env python3
"""Read-only Scribe advisory with explicit projection and receipt write modes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent_runtime import state_projection

try:  # Keep Windows consoles deterministic.
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HOT_KEEP = state_projection.MAX_SELECTED_ITEMS
DUE_AT = state_projection.DUE_AT
OVERDUE_AT = state_projection.OVERDUE_AT


def count_hot_entries(text: str) -> int:
    """Compatibility wrapper over the generic Markdown parser."""

    return int(state_projection.parse_markdown(text)["hot_count"])


def classify(count: int) -> str:
    return state_projection.classify_hot_count(count)


def status_path(root: Path = ROOT) -> Path | None:
    settings = state_projection.resolve_settings(root)
    for source in settings.sources:
        path = root / source.path
        if path.is_file():
            return path
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Scribe source debt, projection coverage, cleanup plans, "
            "and authorized cleanup outcomes"
        )
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    writes = parser.add_mutually_exclusive_group()
    writes.add_argument(
        "--write-projection",
        action="store_true",
        help=(
            "atomically refresh only the configured generated view; this does "
            "not clean canonical source state"
        ),
    )
    writes.add_argument(
        "--record-cleanup",
        action="store_true",
        help=(
            "record an authorized cleanup outcome in the generated projection; "
            "canonical source edits must already be complete"
        ),
    )
    parser.add_argument(
        "--authorization-ref",
        default="",
        help="repo-relative existing task or record authorizing --record-cleanup",
    )
    parser.add_argument(
        "--owner-decision-ref",
        default="",
        help=(
            "repo-relative existing owner decision permitting no reduction; "
            "valid only with --record-cleanup"
        ),
    )
    parser.add_argument("--now", help="deterministic ISO-8601 projection timestamp")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.record_cleanup and not args.authorization_ref:
        parser.error("--record-cleanup requires --authorization-ref")
    if args.owner_decision_ref and not args.record_cleanup:
        parser.error("--owner-decision-ref requires --record-cleanup")
    if args.authorization_ref and not args.record_cleanup:
        parser.error("--authorization-ref requires --record-cleanup")
    try:
        if args.record_cleanup:
            result = state_projection.record_cleanup(
                args.root,
                authorization_ref=args.authorization_ref,
                owner_decision_ref=args.owner_decision_ref,
                now=args.now,
            )
        elif args.write_projection:
            result = state_projection.write_projection(args.root, now=args.now)
        else:
            result = state_projection.evaluate_state(args.root)
    except state_projection.StateProjectionError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "schema": state_projection.EVALUATION_SCHEMA,
                        "state": "unavailable",
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
            )
        else:
            print(f"[scribe_due] unavailable — {exc}")
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    print(f"[scribe_due] {state_projection.compact_summary(result)}")
    if not args.quiet and result["readiness"] != "ready":
        print(
            "  → Refresh the bounded view with "
            "`python scripts/scribe_due.py --write-projection`; "
            "this never cleans canonical source debt. Execute cleanup only "
            "under an explicit task, then record its outcome with "
            "`--record-cleanup --authorization-ref <repo-relative-path>`."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
