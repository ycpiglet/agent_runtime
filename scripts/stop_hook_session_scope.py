"""Session-scoped Stop-hook guard.

The closeout gates are repo-wide by design, but Stop hooks fire for every pane.
This helper lets wrappers skip repo-wide closeout gates when the current session
only asked questions or ran read-only inspection commands.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "agent-runtime-stop-hook-session-scope/v1"
DISABLE_ENV = "AGENT_RUNTIME_STOP_SCOPE_DISABLE"
MUTATING_TOOL_MARKERS = (
    "apply_patch",
    "edit",
    "multiedit",
    "notebookedit",
    "write",
)
SHELL_TOOL_MARKERS = (
    "bash",
    "cmd",
    "powershell",
    "pwsh",
    "shell",
    "shell_command",
)
MUTATING_COMMAND_RE = re.compile(
    r"""(?ix)
    (
        \b(git|gh)\s+
            (
                add|commit|merge|rebase|reset|restore|checkout|switch|branch|
                push|pull|clean|
                worktree\s+(add|remove|prune|move)|
                stash\s+(push|pop|apply|drop|clear)
            )\b
      | \b(
            apply_patch|Set-Content|Add-Content|Out-File|New-Item|Remove-Item|
            Move-Item|Copy-Item|Rename-Item|Start-Process|Stop-Process
        )\b
      | \b(python|py)(\.exe)?\s+scripts[\\/](work\.py\s+(new|close)|task_claim_dispatcher\.py\s+(create|release)|work_item_classifier\.py\s+--write|evidence_index_generator\.py\s+--write|session_baseline\.py)
      | \b(npm|pnpm|yarn)\s+(install|add|remove|update|dedupe)\b
      | (^|[^<])>{1,2}[^>]
    )
    """,
)
ACTIVE_BACKGROUND_STATUSES = {"pending", "running", "active", "in_progress", "working"}
PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)
PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to: (.+)$", re.MULTILINE)
LOG_PREFIXES = ("agents/runtime/hook-logs/", "agents/runtime/session_baselines/")


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def read_hook_input(stdin: Any | None = None) -> dict[str, Any]:
    stream = stdin if stdin is not None else sys.stdin
    try:
        if hasattr(stream, "isatty") and stream.isatty():
            return {}
        if hasattr(stream, "buffer"):
            raw = stream.buffer.read()
        else:
            raw = stream.read()
    except OSError:
        return {}
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", "replace")
    else:
        text = str(raw or "")
    if not text.strip():
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text[0] not in "[{":
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _iter_tool_events(value: Any) -> Iterable[tuple[str, Any]]:
    value = _maybe_json(value)
    if isinstance(value, list):
        for item in value:
            yield from _iter_tool_events(item)
        return
    if not isinstance(value, dict):
        return

    if isinstance(value.get("tool_name"), str):
        yield value["tool_name"], value.get("tool_input")
    if value.get("type") in {"tool_use", "function_call"} and isinstance(value.get("name"), str):
        yield value["name"], value.get("input", value.get("arguments"))
    if isinstance(value.get("recipient_name"), str):
        yield value["recipient_name"], value.get("parameters", value.get("arguments"))

    for child in value.values():
        if isinstance(child, (dict, list)):
            yield from _iter_tool_events(child)


def _command_from_tool_input(tool_input: Any) -> str:
    tool_input = _maybe_json(tool_input)
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
        return ""
    return tool_input if isinstance(tool_input, str) else ""


def command_is_mutating(command: str) -> bool:
    return bool(MUTATING_COMMAND_RE.search(command or ""))


def tool_event_is_mutating(name: str, tool_input: Any = None) -> bool:
    normalized = (name or "").strip().lower().replace("-", "_")
    if any(marker in normalized for marker in MUTATING_TOOL_MARKERS):
        return True
    if any(marker in normalized for marker in SHELL_TOOL_MARKERS):
        return command_is_mutating(_command_from_tool_input(tool_input))
    return False


def _normalize_repo_path(value: str) -> str:
    text = value.strip().strip('"').strip("'").replace("\\", "/")
    if text.startswith("./"):
        text = text[2:]
    return text.rstrip("/")


def _path_values(value: Any) -> set[str]:
    value = _maybe_json(value)
    paths: set[str] = set()
    if isinstance(value, str):
        for pattern in (PATCH_FILE_RE, PATCH_MOVE_RE):
            paths.update(_normalize_repo_path(match.group(1)) for match in pattern.finditer(value))
        return {path for path in paths if path}
    if isinstance(value, list):
        for item in value:
            paths.update(_path_values(item))
        return paths
    if isinstance(value, dict):
        for key in ("file_path", "path"):
            item = value.get(key)
            if isinstance(item, str):
                paths.add(_normalize_repo_path(item))
        for key in ("edits", "files", "patches"):
            if key in value:
                paths.update(_path_values(value[key]))
    return {path for path in paths if path}


def _command_touched_paths(command: str) -> set[str]:
    normalized = command.replace("\\", "/")
    if "scripts/lock_merge_driver.py" in normalized and "post-merge" in normalized:
        return {"tests/fixtures/host/agent_runtime.lock.json"}
    if "scripts/evidence_index_generator.py" in normalized and "--write" in normalized:
        return {"reviews/INDEX.md"}
    return set()


def tool_event_touched_paths(name: str, tool_input: Any = None) -> set[str]:
    normalized = (name or "").strip().lower().replace("-", "_")
    if any(marker in normalized for marker in MUTATING_TOOL_MARKERS):
        return _path_values(tool_input)
    if any(marker in normalized for marker in SHELL_TOOL_MARKERS):
        return _command_touched_paths(_command_from_tool_input(tool_input))
    return set()


def _git_dirty_paths(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except (OSError, FileNotFoundError):
        return set()
    if result.returncode != 0:
        return set()
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            paths.update(_normalize_repo_path(part) for part in payload.split(" -> ", 1))
        else:
            paths.add(_normalize_repo_path(payload))
    return {path for path in paths if path}


def _paths_overlap(left: set[str], right: set[str]) -> bool:
    for a in left:
        for b in right:
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                return True
    return False


def _log_only_dirty(paths: set[str]) -> bool:
    return bool(paths) and all(path.startswith(LOG_PREFIXES) for path in paths)


def transcript_activity(transcript_path: Path) -> tuple[bool, set[str]]:
    mutating = False
    touched_paths: set[str] = set()
    try:
        with transcript_path.expanduser().open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for name, tool_input in _iter_tool_events(payload):
                    if tool_event_is_mutating(name, tool_input):
                        mutating = True
                        touched_paths.update(tool_event_touched_paths(name, tool_input))
    except OSError:
        return True, set()
    return mutating, touched_paths


def transcript_has_mutating_activity(transcript_path: Path) -> bool:
    return transcript_activity(transcript_path)[0]


def _has_active_background_work(hook_input: dict[str, Any]) -> bool:
    for task in hook_input.get("background_tasks") or []:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "").strip().lower()
        if status in ACTIVE_BACKGROUND_STATUSES:
            return True
    return False


def assess(hook_input: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    if _env_bool(DISABLE_ENV):
        return {
            "schema": SCHEMA,
            "bypass": False,
            "reason": "scope-guard-disabled",
        }
    if _has_active_background_work(hook_input):
        return {
            "schema": SCHEMA,
            "bypass": False,
            "reason": "background-work-active",
        }
    raw_path = str(hook_input.get("transcript_path") or "").strip()
    if not raw_path:
        return {
            "schema": SCHEMA,
            "bypass": False,
            "reason": "missing-transcript-path",
        }
    transcript_path = Path(raw_path)
    mutating, touched_paths = transcript_activity(transcript_path)
    if mutating and root is not None:
        dirty_paths = _git_dirty_paths(root)
        if not dirty_paths or _log_only_dirty(dirty_paths):
            return {
                "schema": SCHEMA,
                "bypass": True,
                "reason": "session-work-preserved",
                "transcript_path": transcript_path.as_posix(),
            }
        if touched_paths and not _paths_overlap(dirty_paths, touched_paths):
            return {
                "schema": SCHEMA,
                "bypass": True,
                "reason": "dirty-state-unrelated-to-session",
                "transcript_path": transcript_path.as_posix(),
            }
    return {
        "schema": SCHEMA,
        "bypass": not mutating,
        "reason": "question-only-session" if not mutating else "session-has-mutating-activity",
        "transcript_path": transcript_path.as_posix(),
    }


def approval_payload(gate_name: str, scope: dict[str, Any]) -> dict[str, str]:
    return {
        "decision": "approve",
        "reason": f"{gate_name} skipped for question-only session",
        "systemMessage": (
            "Stop hook scope guard approved without repo-wide closeout checks: "
            f"{scope.get('reason')} ({scope.get('transcript_path', 'no transcript path')})."
        ),
    }
