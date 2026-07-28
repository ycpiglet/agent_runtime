"""Portable, allowlisted dispatcher for tracked Agent Runtime hooks.

Tracked hook configuration invokes this module on every supported platform.
The dispatcher resolves the host repository, selects one fixed script, and
forwards the original client payload. Advisory lifecycle hooks fail open;
prompt and stop gates preserve the child process decision and streams.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence


SCRIPTS: dict[str, str] = {
    "session-start": "scripts/session_start_hook.py",
    "pre-compact": "scripts/session_compact_hook.py",
    "post-compact": "scripts/session_compact_hook.py",
    "prompt-submit": "scripts/taskset_prompt_hook.py",
    "stop-owner": "scripts/stop_hook_owner_governance.py",
    "stop-closure": "scripts/stop_hook_closure_gate.py",
    "stop-dirty": "scripts/stop_hook_dirty_intake.py",
    "posttool-owner-doc": "scripts/owner_doc_format_gate.py",
}

ADVISORY_MODES = frozenset({"session-start", "pre-compact", "post-compact"})

# Stay below the corresponding client hook timeout so a timed-out child does
# not survive after the dispatcher has returned.
CHILD_TIMEOUT_SECONDS: dict[str, int] = {
    "session-start": 43,
    "pre-compact": 8,
    "post-compact": 8,
    "prompt-submit": 18,
    "stop-owner": 118,
    "stop-closure": 28,
    "stop-dirty": 58,
    "posttool-owner-doc": 18,
}


def root_for(cwd: str) -> Path:
    """Resolve the containing Git root, falling back to the supplied cwd."""
    candidate = Path(cwd or ".").resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            timeout=2,
        )
        resolved = result.stdout.strip()
        return Path(resolved).resolve() if resolved else candidate
    except (OSError, subprocess.SubprocessError):
        return candidate


def session_start_payload(stdout: str) -> str:
    """Return valid SessionStart hook JSON with bounded fallback context."""
    try:
        parsed = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        parsed = None
    if isinstance(parsed, dict):
        return json.dumps(parsed, ensure_ascii=False)
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": str(stdout)[:6000],
            }
        },
        ensure_ascii=False,
    )


def _child_command(mode: str, root: Path) -> list[str]:
    command = [sys.executable, str(root / SCRIPTS[mode])]
    if mode == "session-start":
        command.extend(["--root", str(root)])
    elif mode in {"pre-compact", "post-compact"}:
        command.extend(["--root", str(root), "--phase", mode])
    elif mode == "posttool-owner-doc":
        command.extend(["--manifest", "owner-docs.yml"])
    return command


def _advisory_failure(mode: str, detail: str) -> int:
    diagnostic = f"agent-runtime {mode} unavailable: {detail}"
    if mode == "session-start":
        print(session_start_payload(diagnostic))
    else:
        # Compact stdout is ignored by Codex, but valid JSON keeps this safe for
        # other clients while stderr leaves a visible diagnostic.
        print("{}")
        print(diagnostic, file=sys.stderr)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in SCRIPTS:
        return 2
    mode = args[0]

    raw = sys.stdin.read()
    try:
        event = json.loads(raw or "{}")
    except json.JSONDecodeError:
        event = {}
    if not isinstance(event, dict):
        event = {}

    root = root_for(str(event.get("cwd") or ""))
    try:
        result = subprocess.run(
            _child_command(mode, root),
            input=raw,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=root,
            timeout=CHILD_TIMEOUT_SECONDS[mode],
        )
    except (OSError, subprocess.SubprocessError) as exc:
        if mode in ADVISORY_MODES:
            return _advisory_failure(mode, exc.__class__.__name__)
        print(f"agent-runtime {mode} failed: {exc}", file=sys.stderr)
        return 1

    if mode in ADVISORY_MODES:
        if result.returncode != 0:
            return _advisory_failure(mode, f"exit {result.returncode}")
        if mode == "session-start":
            output = result.stdout.strip()
            if not output:
                return _advisory_failure(mode, "empty output")
            print(session_start_payload(output))
            return 0
        print("{}")
        return 0

    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
