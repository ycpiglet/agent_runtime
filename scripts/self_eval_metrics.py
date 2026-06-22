"""Cross-version self-eval metrics (agent_runtime#128).

Computes the AVAILABLE objective fixed metrics for one agent_runtime version
window -- the commit range between two refs (defaults: latest tag .. HEAD).
Two families are emitted:
- git-derived metrics straight from the commit range, and
- WORK-SCHEMA record metrics (gate failures, reopen/rework, actual_*,
  lead_time) read from the repo's task/verification artifacts and filtered to
  the SAME window by record timestamp.

The companion methodology is in ``docs/AGENT_RUNTIME_EVAL_METRICS.md`` (fixed =
spine, variable = limbs).

This is a watch-only signal, not a gate:
- ``--check`` always exits 0 and never mutates state.
- Metrics with no source in the repo are emitted honestly as
  ``status: not_collected`` with ``value: null`` (e.g. ``owner_interventions``),
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
from datetime import datetime, timezone
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


# --- WORK-SCHEMA record metrics (agent_runtime#128 deferred-metric wiring) ----
#
# The fixed metrics above are git-only. The closure/measurement group of the
# WORK-SCHEMA (gate_failure, reopened, actual_*, lead_time) lives in the repo's
# task/unit records and independent verification artifacts, NOT in git history.
# We read the REAL source for the metrics that have one, filtered to the same
# version window by record timestamp, and leave the rest honestly not_collected.
#
# Sources (canonical, see agents/.../WORK-SCHEMA.yml):
#   - reviews/VERIFY-*.json  -> verification signal (pass/fail) per attempt
#   - agents/lead_engineer/tasks/*.md frontmatter -> closure/measurement fields

TASKS_GLOB = "agents/lead_engineer/tasks/*.md"
VERIFY_GLOB = "reviews/VERIFY-*.json"

_FM_RE = re.compile(r"^---\s*$(.*?)^---\s*$", re.DOTALL | re.MULTILINE)
# Flat "key: value" frontmatter lines (the closure/measurement fields we need
# are all scalar; nested blocks like `verification:` are ignored by design).
_FM_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]+(.+?)\s*$")


def _parse_iso(text: str) -> datetime | None:
    """Parse an ISO timestamp to a NAIVE-UTC datetime (so all values compare).

    Records mix tz-aware (``+09:00``) and occasionally naive stamps; normalizing
    everything to naive-UTC here avoids offset-naive/aware comparison errors.
    """
    text = (text or "").strip().strip('"').strip("'")
    if not text:
        return None
    # Python < 3.11 cannot parse a trailing 'Z'; normalize to an explicit offset.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _ref_timestamp(root: Path, ref: str) -> datetime | None:
    """Committer datetime (tz-aware ISO) of a ref, or None if unresolvable."""
    out = _git(root, "log", "-1", "--format=%cI", ref)
    return _parse_iso((out or "").strip())


def _in_window(ts: datetime | None, lo: datetime | None, hi: datetime | None) -> bool:
    """True when ts is in (lo, hi]. Open bounds (None) are treated as -/+inf.

    All timestamps are naive-UTC (see ``_parse_iso``), so they compare directly.
    """
    if ts is None:
        return False
    if lo is not None and ts <= lo:
        return False
    if hi is not None and ts > hi:
        return False
    return True


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = _FM_RE.search(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line[:1] in (" ", "\t", "#"):
            continue  # skip nested/indented and comment lines
        m = _FM_LINE_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2)
    return fields


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def _to_int(value: str | None) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None


def _collect_verify(root: Path, lo: datetime | None, hi: datetime | None) -> dict[str, int]:
    """Gate failures and re-verification rounds from in-window VERIFY records."""
    gate_failures = 0
    rounds: dict[str, int] = {}
    for path in sorted(root.glob(VERIFY_GLOB)):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not _in_window(_parse_iso(record.get("verified_at", "")), lo, hi):
            continue
        failed = record.get("signal") == "fail" or record.get("status") == "failed"
        if failed:
            gate_failures += 1
        key = record.get("task_id") or record.get("work_id") or record.get("id") or ""
        if key:
            rounds[key] = rounds.get(key, 0) + 1
    # A re-verification is any attempt beyond the first for a given work item -- a
    # real proxy for rework/reopen rounds (the populated reopened_count field is
    # rarely set in practice, so this complements it).
    reverifications = sum(max(0, n - 1) for n in rounds.values())
    return {"gate_failure_count": gate_failures, "reverification_count": reverifications}


def _collect_tasks(root: Path, lo: datetime | None, hi: datetime | None) -> dict[str, Any]:
    """Measurement/closure aggregates from tasks COMPLETED in the window."""
    tokens_total = 0
    hours_total = 0.0
    wall_total = 0.0
    reopened_total = 0
    measured = 0  # tasks with at least one actual_* measurement
    wall_measured = 0  # tasks with a derivable lead_time
    for path in sorted(root.glob(TASKS_GLOB)):
        try:
            fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not fm:
            continue
        completed = _parse_iso(fm.get("completed_at", ""))
        if not _in_window(completed, lo, hi):
            continue

        tokens = _to_int(fm.get("actual_tokens"))
        hours = _to_float(fm.get("actual_hours"))
        if tokens is not None or hours is not None:
            measured += 1
            tokens_total += tokens or 0
            hours_total += hours or 0.0

        reopened = _to_int(fm.get("reopened_count"))
        if reopened:
            reopened_total += reopened

        started = _parse_iso(fm.get("started_at", ""))
        if started is not None and completed is not None and completed > started:
            wall_total += (completed - started).total_seconds() / 3600.0
            wall_measured += 1

    return {
        "actual_tokens_total": tokens_total,
        "actual_hours_total": round(hours_total, 6),
        "measured_task_count": measured,
        "reopened_count": reopened_total,
        "wall_clock_hours_total": round(wall_total, 6),
        "wall_clock_task_count": wall_measured,
    }


def _work_schema_metrics(
    root: Path, lo: datetime | None, hi: datetime | None
) -> dict[str, dict[str, Any]]:
    """Build the WORK-SCHEMA-derived fixed metrics for the window."""
    verify = _collect_verify(root, lo, hi)
    tasks = _collect_tasks(root, lo, hi)

    measured = tasks["measured_task_count"]
    wall_n = tasks["wall_clock_task_count"]
    tokens_per_task = (tasks["actual_tokens_total"] / measured) if measured else None
    hours_per_task = (tasks["actual_hours_total"] / measured) if measured else None
    wall_per_task = (tasks["wall_clock_hours_total"] / wall_n) if wall_n else None

    verify_src = f"{VERIFY_GLOB} (in-window verified_at)"
    task_src = f"{TASKS_GLOB} frontmatter (in-window completed_at)"

    metrics: dict[str, dict[str, Any]] = {
        "gate_failure_count": _fixed(
            verify["gate_failure_count"],
            verify_src,
            "WORK-SCHEMA verification: VERIFY records with signal=fail/status=failed",
        ),
        "reverification_count": _fixed(
            verify["reverification_count"],
            verify_src,
            "re-verification rounds (attempts>1 per work item); proxy for rework/reopen",
        ),
        "reopened_count": _fixed(
            tasks["reopened_count"],
            task_src,
            "WORK-SCHEMA closure reopened_count summed over in-window tasks",
        ),
        "measured_task_count": _fixed(
            measured, task_src, "tasks with actual_hours/actual_tokens populated"
        ),
        "actual_tokens_total": _fixed(
            tasks["actual_tokens_total"], task_src, "WORK-SCHEMA measurement actual_tokens"
        ),
        "actual_hours_total": _fixed(
            tasks["actual_hours_total"], task_src, "WORK-SCHEMA measurement actual_hours"
        ),
        "wall_clock_hours_total": _fixed(
            tasks["wall_clock_hours_total"],
            task_src,
            "lead_time = completed_at - started_at, summed",
        ),
    }

    # Per-task means: collected only when there is real data, else not_collected
    # (no measured tasks in window) -- never a fabricated zero-denominator value.
    if measured:
        metrics["tokens_per_task"] = _fixed(
            round(tokens_per_task, 6), task_src, "actual_tokens_total / measured_task_count"
        )
        metrics["hours_per_task"] = _fixed(
            round(hours_per_task, 6), task_src, "actual_hours_total / measured_task_count"
        )
    else:
        metrics["tokens_per_task"] = _not_collected(
            "no in-window tasks carry actual_tokens (WORK-SCHEMA measurement)"
        )
        metrics["hours_per_task"] = _not_collected(
            "no in-window tasks carry actual_hours (WORK-SCHEMA measurement)"
        )

    if wall_n:
        metrics["wall_clock_per_task"] = _fixed(
            round(wall_per_task, 6), task_src, "wall_clock_hours_total / tasks with lead_time"
        )
    else:
        metrics["wall_clock_per_task"] = _not_collected(
            "no in-window tasks carry both started_at and completed_at"
        )

    # Genuinely unsourced: nothing in the repo records owner decisions per task.
    metrics["owner_interventions"] = _not_collected(
        "no owner-intervention instrumentation in repo records (agent_runtime#128 follow-up)"
    )
    return metrics


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
    }

    # WORK-SCHEMA-derived metrics: read the real closure/measurement source for
    # the same window (bounded by the from/to ref commit timestamps).
    lo = _ref_timestamp(root, resolved_from)
    hi = _ref_timestamp(root, to_ref)
    fixed_metrics.update(_work_schema_metrics(root, lo, hi))

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
    parser.add_argument(
        "--from", "--since", dest="from_ref", default=None,
        help="base ref / window start (default: latest tag)",
    )
    parser.add_argument(
        "--to", "--until", dest="to_ref", default="HEAD",
        help="head ref / window end (default: HEAD)",
    )
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
