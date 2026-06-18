"""Stop hook wrapper for dirty-intake closeout classification."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import stop_hook_session_scope


ROOT = Path(__file__).resolve().parents[1]
MAX_MESSAGE_CHARS = 6000


def _clip(text: str) -> str:
    if len(text) <= MAX_MESSAGE_CHARS:
        return text
    return text[:MAX_MESSAGE_CHARS] + "\n...[truncated]"


def _run_dirty_intake(extra_args: list[str]) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, "scripts/dirty_intake.py", "--root", ".", "--json", *extra_args]
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _payload_from_result(result: subprocess.CompletedProcess[str]) -> dict[str, str]:
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    try:
        plan = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        plan = {}
    decision = str(plan.get("decision") or plan.get("status") or "").strip().lower()
    if result.returncode != 0 and not decision:
        return {
            "decision": "block",
            "reason": f"dirty intake hook failed with code {result.returncode}",
            "systemMessage": _clip(output),
        }
    if decision == "block":
        return {
            "decision": "block",
            "reason": "dirty intake requires preservation before closeout",
            "systemMessage": _clip(output),
        }
    return {
        "decision": "approve",
        "reason": "dirty intake did not require closeout block",
        "systemMessage": _clip(output),
    }


def main(argv: list[str] | None = None) -> int:
    scope = stop_hook_session_scope.assess(stop_hook_session_scope.read_hook_input(), root=ROOT)
    if scope.get("bypass"):
        print(json.dumps(stop_hook_session_scope.approval_payload("dirty intake", scope), ensure_ascii=False))
        return 0
    result = _run_dirty_intake(list(argv or []))
    print(json.dumps(_payload_from_result(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

