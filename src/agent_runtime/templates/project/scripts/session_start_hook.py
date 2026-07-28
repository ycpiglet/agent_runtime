"""Bounded, non-blocking SessionStart continuity summary."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Sequence

from agent_runtime import state_projection


COLLECTOR_TIMEOUT_SECONDS = 8
COLLECTOR_OUTPUT_LIMIT = 500
CHECKPOINT_OUTPUT_LIMIT = 800
CONTEXT_OUTPUT_LIMIT = 6000
COMPOUND_READ_LIMIT = 12_000
SESSION_ID_LIMIT = 80


def run(root: Path, script: str, *, root_arg: bool = True) -> str:
    """Run one bounded advisory collector and return one compact line."""
    if script == "update-notify":
        command = [
            sys.executable,
            "-m",
            "agent_runtime.cli",
            "update-notify",
            "--root",
            str(root),
        ]
    else:
        command = [sys.executable, str(root / "scripts" / script)]
        if root_arg:
            command.extend(["--root", str(root)])

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COLLECTOR_TIMEOUT_SECONDS,
            cwd=root,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"

    text = (result.stdout or result.stderr).strip().replace("\n", " ")
    if result.returncode != 0:
        return "unavailable"
    return text[:COLLECTOR_OUTPUT_LIMIT] if text else "none"


def _safe_session_id(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(value))[:SESSION_ID_LIMIT]


def checkpoint_summary(path: Path, session_id: str) -> str:
    """Summarize this session's compact checkpoint, or the latest fallback."""
    try:
        candidate = path.parent / f"{_safe_session_id(session_id)}.json" if session_id else path
        checkpoint_path = candidate if candidate.exists() else path
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("checkpoint must be an object")
        fields = ("session_id", "active_task", "active_task_set", "rebootstrap_required")
        details = [f"{field}={data[field]}" for field in fields if field in data]
        active = ", ".join(
            str(item.get("task_id") or item.get("task") or item.get("claim_id"))
            for item in data.get("active_claims", [])[:4]
            if isinstance(item, dict)
        )
        if active:
            details.append(f"active_work={active}")
        return ("checkpoint: " + ", ".join(details))[:CHECKPOINT_OUTPUT_LIMIT]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return "checkpoint: unavailable"


def compound_summary(path: Path) -> str:
    """Read only a bounded prefix of the legacy compound log."""
    try:
        text = path.read_text(encoding="utf-8")[:COMPOUND_READ_LIMIT]
    except OSError:
        return "compound: unavailable"
    headings = [
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## COMPOUND-")
    ]
    latest = headings[-1][:240] if headings else "none"
    return f"compound: count={len(headings)}, latest={latest}"


def scribe_summary(root: Path) -> str:
    """Evaluate Scribe readiness without writing sources or projection."""

    try:
        evaluation = state_projection.evaluate_state(root)
    except Exception:
        return "scribe: unavailable"
    return f"scribe: {state_projection.compact_summary(evaluation)}"


def _read_event() -> dict[str, object]:
    try:
        event = json.load(sys.stdin)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}
    return event if isinstance(event, dict) else {}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()

    event = _read_event()
    session_id = str(event.get("session_id") or "")[:SESSION_ID_LIMIT]
    source = str(event.get("source") or event.get("trigger") or "unknown")[:SESSION_ID_LIMIT]
    checkpoint = root / "agents" / "runtime" / "session_checkpoints" / "latest.json"
    lines = [
        f"agent-runtime host={root} source={source}",
        checkpoint_summary(checkpoint, session_id),
    ]

    # These state-refreshing checks must remain deterministic and ordered.
    lines.extend(
        [
            f"baseline: {run(root, 'session_baseline.py')}",
            f"claim-reaper: {run(root, 'claim_reaper_hook.py')}",
        ]
    )

    # The remaining checks are independent advisory collectors. Update notice
    # may refresh its bounded local cache; none edits canonical work state.
    collectors = (
        ("dashboard", "session_dashboard.py"),
        ("interrupted", "interrupted_run_detector.py"),
        ("resume", "session_resume_check.py"),
        ("update-notify", "update-notify"),
    )
    with ThreadPoolExecutor(max_workers=len(collectors)) as pool:
        futures = [
            (label, pool.submit(run, root, script))
            for label, script in collectors
        ]
        lines.extend(f"{label}: {future.result()}" for label, future in futures)

    lines.append(
        compound_summary(root / "agents" / "lead_engineer" / "compound_log.md")
    )
    lines.append(scribe_summary(root))
    context = "\n".join(lines)[:CONTEXT_OUTPUT_LIMIT]
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
