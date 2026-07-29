"""Thin security-service helper for the packaged Agent Runtime producer."""
from __future__ import annotations

import argparse
import functools
import json
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_TIMEOUT_SECONDS = 8

__all__ = ["EventPolicyError", "emit_event", "notify", "notify_on_complete"]


class EventPolicyError(ValueError):
    """The packaged producer rejected structured input before enqueue."""


def _unavailable(reason: str = "producer_unavailable") -> dict[str, str | None]:
    return {"status": "unavailable", "event_id": None, "reason": reason}


def emit_event(
    event_type: str,
    data: Mapping[str, Any],
    *,
    root: str | Path = ROOT,
    session_id: str | None = None,
    turn_id: str | None = None,
    dedupe_key: str | None = None,
) -> dict[str, str | None]:
    if not isinstance(data, Mapping):
        raise EventPolicyError("structured event data must be an object")
    payload = {
        "event_type": event_type,
        "data": dict(data),
        "session_id": session_id,
        "turn_id": turn_id,
        "dedupe_key": dedupe_key,
    }
    command = [
        sys.executable,
        "-m",
        "agent_runtime.allimbot",
        "--stdin",
        "--json",
        "--root",
        str(Path(root).resolve()),
    ]
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(payload, separators=(",", ":")),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=Path(root).resolve(),
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
        result = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, UnicodeError, json.JSONDecodeError):
        return _unavailable()
    if (
        completed.returncode == 2
        and isinstance(result, dict)
        and result.get("status") == "rejected"
    ):
        raise EventPolicyError("structured event rejected by managed policy")
    if completed.returncode != 0 or not isinstance(result, dict):
        return _unavailable()
    if result.get("status") not in {"spooled", "unavailable"}:
        return _unavailable()
    return {
        "status": str(result["status"]),
        "event_id": result.get("event_id"),
        "reason": result.get("reason"),
    }


def _legacy_result() -> dict[str, str | None]:
    return emit_event(
        "attention.required",
        {
            "task_id": "agent-runtime",
            "attention_kind": "legacy-notification",
            "owner_role": "owner",
            "state": "attention",
        },
    )


def notify(
    message: str,
    title: str = "agent_runtime",
    provider: str | None = None,
    timeout: float = 3.0,
) -> bool:
    """Compatibility signal that deliberately ignores all supplied free text."""

    del message, title, provider, timeout
    return _legacy_result()["status"] == "spooled"


def notify_on_complete(
    title: str | None = None,
    provider: str | None = None,
) -> Callable:
    del title, provider

    def decorator(function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = function(*args, **kwargs)
            except Exception:
                try:
                    emit_event(
                        "task.state.changed",
                        {
                            "task_id": "agent-runtime",
                            "from_state": "running",
                            "to_state": "failed",
                            "owner_role": "runtime",
                        },
                    )
                except Exception:
                    pass
                raise
            try:
                emit_event(
                    "task.state.changed",
                    {
                        "task_id": "agent-runtime",
                        "from_state": "running",
                        "to_state": "completed",
                        "owner_role": "runtime",
                    },
                )
            except Exception:
                pass
            return result

        return wrapper

    return decorator


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enqueue a strict native Allimbot project event")
    parser.add_argument("message", nargs="?", help="legacy message (ignored)")
    parser.add_argument("-t", "--title", default="agent_runtime", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--provider", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.stdin:
            payload = json.loads(sys.stdin.read())
            if not isinstance(payload, dict):
                raise EventPolicyError("structured input must be an object")
            if set(payload) - {
                "event_type",
                "data",
                "session_id",
                "turn_id",
                "dedupe_key",
            }:
                raise EventPolicyError("structured input contains unexpected fields")
            result = emit_event(
                payload.get("event_type"),
                payload.get("data"),
                session_id=payload.get("session_id"),
                turn_id=payload.get("turn_id"),
                dedupe_key=payload.get("dedupe_key"),
            )
        elif args.message is not None:
            result = _legacy_result()
        else:
            parser.error("provide --stdin or a legacy positional message")
    except (EventPolicyError, OSError, UnicodeError, json.JSONDecodeError):
        if args.json:
            print(json.dumps({"status": "rejected", "reason": "policy_error"}))
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
