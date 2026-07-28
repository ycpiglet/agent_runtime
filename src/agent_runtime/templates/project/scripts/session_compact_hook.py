"""Persist bounded derived state around compaction, never conversation content."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ACTIVE_CLAIM_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}
CHECKPOINT_SCHEMA = "agent-runtime-compact-checkpoint/v1"
SESSION_ID_LIMIT = 80
STATE_VALUE_LIMIT = 240
MAX_ACTIVE_CLAIMS = 12
GIT_TIMEOUT_SECONDS = 2


def _safe_session_id(value: object) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]", "_", str(value or "default"))
    return sanitized[:SESSION_ID_LIMIT] or "default"


def pointer_state(path: Path) -> dict[str, object]:
    state: dict[str, object] = {"pointer_exists": path.exists()}
    if not path.exists():
        return state
    try:
        text = path.read_text(encoding="utf-8")[:8000]
    except OSError:
        return state
    for field in ("active_task", "active_task_set"):
        match = re.search(
            rf"^\s*{field}\s*:\s*['\"]?([^\n'\"]+)",
            text,
            re.MULTILINE,
        )
        if match:
            state[field] = match.group(1).strip()[:STATE_VALUE_LIMIT]
    return state


def active_claims(root: Path) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    claim_dir = root / "agents" / "runtime" / "task_claims"
    for path in reversed(sorted(claim_dir.glob("*.json"))):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(record, dict):
            continue
        if str(record.get("status", "")).lower() not in ACTIVE_CLAIM_STATUSES:
            continue
        claims.append(
            {
                key: str(record[key])[:STATE_VALUE_LIMIT]
                for key in ("claim_id", "task_id", "branch")
                if record.get(key)
            }
        )
        if len(claims) >= MAX_ACTIVE_CLAIMS:
            break
    return claims


def atomic_json(path: Path, data: dict[str, object]) -> None:
    """Replace one checkpoint atomically and remove failed temp files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=".checkpoint-",
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _derived_state(root: Path, event: dict[str, object], session_id: str) -> dict[str, object]:
    status = _git_output(root, "status", "--porcelain")
    return {
        "schema": CHECKPOINT_SCHEMA,
        "session_id": session_id,
        "trigger": str(event.get("trigger") or event.get("source") or "unknown")[
            :SESSION_ID_LIMIT
        ],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **pointer_state(root / "agents" / "project" / "NEXT-SESSION-POINTER.yml"),
        "active_claims": active_claims(root),
        "git": {
            "branch": _git_output(root, "branch", "--show-current"),
            "head": _git_output(root, "rev-parse", "--short", "HEAD"),
            "dirty_count": len(status.splitlines()) if status is not None else None,
        },
    }


def _read_event() -> dict[str, object]:
    try:
        event = json.load(sys.stdin)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}
    return event if isinstance(event, dict) else {}


def _load_checkpoint(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--phase",
        choices=("pre-compact", "post-compact"),
        required=True,
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    event = _read_event()
    session_id = _safe_session_id(event.get("session_id"))

    directory = root / "agents" / "runtime" / "session_checkpoints"
    per_session = directory / f"{session_id}.json"
    latest = directory / "latest.json"

    data = _derived_state(root, event, session_id)
    if args.phase == "post-compact":
        # Preserve the pre-compact snapshot when available; PostCompact marks
        # that the next SessionStart must rebuild its injected context.
        data = _load_checkpoint(per_session) or data
    data.update(
        {
            "schema": CHECKPOINT_SCHEMA,
            "session_id": session_id,
            "phase": args.phase,
            "rebootstrap_required": args.phase == "post-compact",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    for target in (per_session, latest):
        atomic_json(target, data)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
