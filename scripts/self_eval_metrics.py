"""Cross-version self-eval metrics (agent_runtime#128).

Computes the AVAILABLE objective fixed metrics for one agent_runtime version
window -- the commit range between two refs (defaults: latest tag .. HEAD) --
straight from git. The companion methodology is in
``docs/AGENT_RUNTIME_EVAL_METRICS.md`` (fixed = spine, variable = limbs).

This is a watch-only signal, not a gate:
- ``--check`` always exits 0 and never mutates state.
- Metrics with no upstream instrumentation are emitted honestly as
  ``status: not_collected`` with ``value: null`` (e.g. ``tokens_per_task``),
  never faked or estimated.

Boundaries (deliberate):
- Source-repo tool only. NOT wired into ``owner_governance_gate.py`` and never
  hardcodes ``src/agent_runtime/...`` consumer paths.
- Reuses the git helpers from ``release_cadence_trigger.py`` rather than forking
  them, so cadence and self-eval stay consistent.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reuse the audited git/format helpers from the cadence trigger.
import release_cadence_trigger as cadence  # noqa: E402

_git = cadence._git
_ascii = cadence._ascii
_latest_tag = cadence._latest_tag
_conventional_counts = cadence._conventional_counts
_days_since_tag = cadence._days_since_tag

SCHEMA = "agent-runtime-self-eval/v1"
MUTATION_BOUNDARY = "watch-only; no version bump, tag, push, publish, or release execution"

# A commit counts as "rework" when its subject signals a follow-up correction:
# revert/hotfix, or a conventional fix:. This is a PROXY for true rework rounds
# (the WORK-SCHEMA measurement group is the exact source -- see the methodology
# doc), usable from git alone with no extra instrumentation.
_REWORK_RE = re.compile(
    r"^(?:revert|hotfix)\b|^revert[:!(]|^fix(?:\([^)]*\))?!?:",
    re.IGNORECASE,
)


def _range(from_ref: str, to_ref: str) -> str:
    return f"{from_ref}..{to_ref}"


def _commit_subjects(root: Path, rng: str) -> list[str]:
    """Subjects of NON-merge commits in the range (rework/feat/fix proxies)."""
    out = _git(root, "log", "--no-merges", "--format=%s", rng)
    if not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _commit_count(root: Path, rng: str) -> int:
    out = _git(root, "rev-list", "--no-merges", "--count", rng)
    try:
        return int((out or "").strip())
    except (ValueError, TypeError):
        return 0


def _merge_commit_count(root: Path, rng: str) -> int:
    out = _git(root, "rev-list", "--merges", "--count", rng)
    try:
        return int((out or "").strip())
    except (ValueError, TypeError):
        return 0


def _rework_count(subjects: list[str]) -> int:
    return sum(1 for s in subjects if _REWORK_RE.search(s.strip()))


def _fixed(value: Any, source: str, note: str = "") -> dict[str, Any]:
    return {"value": value, "status": "collected", "source": source, "note": note}


def _not_collected(reason: str) -> dict[str, Any]:
    return {"value": None, "status": "not_collected", "source": None, "note": reason}


def build_report(
    root: Path,
    *,
    from_ref: str | None = None,
    to_ref: str = "HEAD",
    now_ts: float | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema": SCHEMA,
        "mutation_boundary": MUTATION_BOUNDARY,
    }

    resolved_from = from_ref or _latest_tag(root)
    if resolved_from is None:
        base.update(
            {
                "status": "pass",
                "from_ref": None,
                "to_ref": to_ref,
                "reason": "no-baseline-tag",
                "fixed_metrics": None,
                "variable_metrics_note": (
                    "variable (per-version) metrics are defined in"
                    " docs/AGENT_RUNTIME_EVAL_METRICS.md and collected per version;"
                    " not derivable from git alone"
                ),
            }
        )
        return base

    rng = _range(resolved_from, to_ref)
    subjects = _commit_subjects(root, rng)
    commit_count = _commit_count(root, rng)
    counts = _conventional_counts(subjects)
    rework = _rework_count(subjects)
    merges = _merge_commit_count(root, rng)
    days = _days_since_tag(root, resolved_from, now_ts=now_ts)

    rework_ratio = (rework / commit_count) if commit_count else 0.0
    first_pass_proxy = max(0.0, 1.0 - rework_ratio) if commit_count else None

    fixed_metrics: dict[str, Any] = {
        "commit_count": _fixed(commit_count, "git rev-list --no-merges --count"),
        "feat_count": _fixed(counts["feat"], "conventional-commit subjects"),
        "fix_count": _fixed(counts["fix"], "conventional-commit subjects"),
        "merge_commit_count": _fixed(merges, "git rev-list --merges --count"),
        "rework_count": _fixed(
            rework,
            "subject proxy (revert/hotfix/fix:)",
            "proxy for WORK-SCHEMA rework rounds; not a precise count",
        ),
        "rework_ratio": _fixed(
            round(rework_ratio, 6),
            "rework_count / commit_count",
            "lower is better",
        ),
        "first_pass_rate_proxy": _fixed(
            round(first_pass_proxy, 6) if first_pass_proxy is not None else None,
            "1 - rework_ratio",
            "PROXY only; true first-pass needs per-task CI oracle (see doc)",
        ),
        "days_since_from_tag": _fixed(
            days, "commit timestamp of from_ref", "calendar span of the window"
        ),
        "tokens_per_task": _not_collected(
            "no upstream token instrumentation yet (agent_runtime#128 follow-up)"
        ),
    }

    base.update(
        {
            "status": "pass",
            "from_ref": resolved_from,
            "to_ref": to_ref,
            "range": rng,
            "fixed_metrics": fixed_metrics,
            "variable_metrics_note": (
                "variable (per-version) metrics are defined in"
                " docs/AGENT_RUNTIME_EVAL_METRICS.md and collected per version;"
                " not derivable from git alone"
            ),
        }
    )
    return base


def _print_report(report: dict[str, Any]) -> None:
    if report.get("reason") == "no-baseline-tag":
        print(_ascii("self-eval: pass no-baseline-tag (no tag found; nothing to compare)"))
        return

    print(
        _ascii(
            f"self-eval: window {report['from_ref']}..{report['to_ref']}"
            f" (schema {report['schema']})"
        )
    )
    metrics = report["fixed_metrics"] or {}
    for name, payload in metrics.items():
        if payload["status"] == "not_collected":
            print(_ascii(f"self-eval:   {name} = NOT COLLECTED ({payload['note']})"))
        else:
            value = payload["value"]
            value_text = "n/a" if value is None else str(value)
            print(_ascii(f"self-eval:   {name} = {value_text}"))
    print(_ascii(f"self-eval: {MUTATION_BOUNDARY}"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-version self-eval metrics (watch-only)")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--from", dest="from_ref", default=None, help="base ref (default: latest tag)")
    parser.add_argument("--to", dest="to_ref", default="HEAD", help="head ref (default: HEAD)")
    parser.add_argument("--check", action="store_true", help="watch-only mode; always exit 0")
    parser.add_argument("--json", action="store_true", help="print full JSON payload")
    args = parser.parse_args(argv)

    try:
        report = build_report(
            Path(args.root).resolve(),
            from_ref=args.from_ref,
            to_ref=args.to_ref,
        )
    except Exception as exc:  # noqa: BLE001 - watch-only tool must not block sessions
        print(_ascii(f"self-eval: error {type(exc).__name__}: {exc}"), file=sys.stderr)
        return 0 if args.check else 1

    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
