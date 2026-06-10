"""Inject task-set dispatcher guidance for taskset-* user prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


TASKSET_RE = re.compile(r"\btaskset[-_: ]*([A-Za-z0-9][A-Za-z0-9_-]*)", re.IGNORECASE)
ACTION_RE = re.compile(r"(진행|시작|작업|run|start|work|execute)", re.IGNORECASE)


def _prompt_from_stdin() -> str:
    raw = sys.stdin.read()
    if not raw.strip():
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict):
        for key in ("prompt", "user_prompt", "text", "message"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
    return raw


def _context_for(prompt: str) -> str | None:
    match = TASKSET_RE.search(prompt)
    if not match:
        return None
    if not ACTION_RE.search(prompt):
        return None
    alias = match.group(1).strip().lower().replace("_", "-")
    return (
        "[taskset trigger]\n"
        f"- Detected taskset alias: {alias}\n"
        "- Before editing files, run `python scripts/taskset_dispatcher.py plan "
        f"{alias} --json` and use the returned task/worktree/claim fields.\n"
        "- To claim the lane, run `python scripts/taskset_dispatcher.py start "
        f"{alias} --json`; do not start another active claim in the same task set.\n"
        "- Work in the returned git worktree/branch, keep progress fields updated, "
        "and run `python scripts/taskset_work_gate.py --check` before handoff."
    )


def _emit_hook_context(context: str | None) -> None:
    if not context:
        print("{}")
        return
    payload: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task-set prompt trigger hook")
    parser.add_argument("--text", help="Prompt text for tests or manual checks")
    args = parser.parse_args(argv)
    prompt = args.text if args.text is not None else _prompt_from_stdin()
    _emit_hook_context(_context_for(prompt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
