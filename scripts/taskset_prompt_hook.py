"""Inject dispatcher and closeout guidance for recognized Owner prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


TASKSET_RE = re.compile(r"\btaskset[-_: ]*([A-Za-z0-9][A-Za-z0-9_-]*)", re.IGNORECASE)
ACTION_RE = re.compile(r"(진행|시작|작업|run|start|work|execute)", re.IGNORECASE)
FINISH_RE = re.compile(
    r"(마무리|마무리해|정리해|정리해줘|정리해주세요|정리해달|깔끔하게|"
    r"finish|wrap\s*up|close\s*out|clean\s*up|clean\s+working\s+tree)",
    re.IGNORECASE,
)


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


def _taskset_context_for(prompt: str) -> str | None:
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


def _finish_context_for(prompt: str) -> str | None:
    if not FINISH_RE.search(prompt):
        return None
    return (
        "[finish trigger]\n"
        "- Owner standing instruction: expressions such as `마무리`, `정리해줘`, "
        "`finish`, `wrap up`, `close out`, or `clean up` mean commit + PR + merge "
        "+ clean working tree by default.\n"
        "- Default workflow: inspect `git status`/diff scope, stage only intended "
        "changes, run relevant local gates/tests, commit, push, create a PR, merge "
        "the PR when required checks allow, sync the default branch, remove owned "
        "merged worktrees/branches, and leave the working tree clean.\n"
        "- Do not stop at a summary or handoff when this trigger fires. Continue "
        "autonomously through safe reversible steps.\n"
        "- Ask for approval only for critical boundaries: destructive discard/delete, "
        "secrets or credentials, production data changes, irreversible external "
        "side effects, mixed unrelated changes that cannot be scoped safely, failed "
        "gates that would require an override, or missing/expired remote auth."
    )


def _context_for(prompt: str) -> str | None:
    contexts = [
        context
        for context in (_taskset_context_for(prompt), _finish_context_for(prompt))
        if context
    ]
    if not contexts:
        return None
    return "\n\n".join(contexts)


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
