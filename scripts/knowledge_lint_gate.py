"""Volume-gated knowledge lint — enforce only on large knowledge-data changes.

knowledge_lint (#146) checks the knowledge graph for integrity/freshness. Small edits
are written in existing context and rarely break the graph, so enforcing on every commit
is noise; a *large batch* of work-item/review changes is when stale memory, dangling refs,
and duplicate ids actually creep in. This gate therefore runs lint as a hard check ONLY
when enough knowledge-data files changed in a recent window — otherwise it is watch-only
(reports, never blocks). Mirrors closure_gate's substantial-churn pattern.

Cheap by default: the (graph build + lint) only runs when the change count crosses the
threshold, so the common small-change commit pays only a couple of `git` calls.

All thresholds are env-tunable so the policy can be optimized over time:
  AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_DISABLE        truthy → always pass
  AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_THRESHOLD=N    changed-file count to enforce (default 10)
  AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_WINDOW_HOURS=H git look-back window (default 12)

CLI:
  python scripts/knowledge_lint_gate.py --check [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_graph as kg
import knowledge_lint as kl

DEFAULT_THRESHOLD = 10
DEFAULT_WINDOW_HOURS = 12
# Knowledge-data surfaces the graph is built from. A change here can drift the graph.
KNOWLEDGE_PATHS = (
    "reviews",
    "agents/project/work-items",
    "agents/project/initiatives",
    "agents/lead_engineer/tasks",
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() not in ("0", "false", "no", "off")


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""
    return result.stdout if result.returncode == 0 else ""


def count_changed_knowledge_files(root: Path, *, now: datetime | None = None, window_hours: int = DEFAULT_WINDOW_HOURS) -> int:
    """Distinct knowledge-data files touched in the window (committed + staged +
    unstaged + untracked). Best-effort: any git failure contributes nothing."""
    moment = now or _now()
    since = (moment - timedelta(hours=window_hours)).isoformat()
    paths = list(KNOWLEDGE_PATHS)
    changed: set[str] = set()
    for output in (
        _git(root, "log", f"--since={since}", "--name-only", "--pretty=format:", "--", *paths),
        _git(root, "diff", "--name-only", "--", *paths),
        _git(root, "diff", "--cached", "--name-only", "--", *paths),
        _git(root, "ls-files", "--others", "--exclude-standard", "--", *paths),
    ):
        for line in output.splitlines():
            line = line.strip()
            if line:
                changed.add(line)
    return len(changed)


def assess(
    root: Path,
    *,
    now: datetime | None = None,
    threshold: int | None = None,
    window_hours: int | None = None,
    disabled: bool | None = None,
) -> dict:
    threshold = _env_int("AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_THRESHOLD", DEFAULT_THRESHOLD) if threshold is None else threshold
    window_hours = _env_int("AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_WINDOW_HOURS", DEFAULT_WINDOW_HOURS) if window_hours is None else window_hours
    disabled = _env_bool("AGENT_RUNTIME_KNOWLEDGE_LINT_GATE_DISABLE", False) if disabled is None else disabled

    if disabled:
        return {"decision": "pass", "enforced": False, "reason": "gate-disabled", "changed": 0, "threshold": threshold}

    changed = count_changed_knowledge_files(Path(root), now=now, window_hours=window_hours)
    if changed < threshold:
        # Small change — watch-only. Skip the (graph build + lint) entirely to stay cheap.
        return {"decision": "pass", "enforced": False, "reason": "below-threshold",
                "changed": changed, "threshold": threshold}

    graph = kg.build_graph(Path(root))
    findings = kl.lint(Path(root), graph)
    summary = kl.summarize(findings)
    blocks = [f for f in findings if f["severity"] == "block"]
    decision = "block" if blocks else "pass"
    return {
        "decision": decision,
        "enforced": True,
        "reason": "substantial-knowledge-change",
        "changed": changed,
        "threshold": threshold,
        "summary": summary,
        "blocks": blocks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Volume-gated knowledge lint")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true", help="exit nonzero when enforcing and block findings exist")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = assess(Path(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not result["enforced"]:
        print(f"knowledge-lint-gate: watch ({result['reason']}; changed={result['changed']}/{result['threshold']})")
    elif result["decision"] == "block":
        print(f"knowledge-lint-gate: BLOCK — {len(result['blocks'])} integrity finding(s) in a large knowledge change "
              f"(changed={result['changed']}>={result['threshold']}). Run: python scripts/knowledge_lint.py check")
        for f in result["blocks"]:
            print(f"  - {f['code']} {f['id']}: {f['detail']}")
    else:
        print(f"knowledge-lint-gate: pass (enforced; changed={result['changed']}>={result['threshold']}; no block findings)")

    return 1 if args.check and result["decision"] == "block" else 0


if __name__ == "__main__":
    kg.enable_utf8_stdout()
    raise SystemExit(main())
