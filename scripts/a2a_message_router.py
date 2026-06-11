"""Local A2A message routing API for agent_runtime.

The router records explicit agent-to-agent lifecycle messages as append-only
JSONL.  It is intentionally file-backed so local workers, gates, and tests can
share one deterministic transport without inferring handoffs from task notes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "agent-runtime-a2a-message/v1"
DEFAULT_MESSAGE_LOG = Path("agents/runtime/a2a/messages.jsonl")
EVENT_TYPES = ("request", "review", "decision", "correction")
ACCESS_LEVELS = {"public", "project", "restricted", "owner-required"}
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.05


class A2AMessageError(ValueError):
    """Raised when an A2A message would break the routing contract."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise A2AMessageError(f"{field} is required")
    return text


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise A2AMessageError(f"invalid jsonl at {path}:{idx}: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise A2AMessageError(f"jsonl row at {path}:{idx} is not an object")
        rows.append(value)
    return rows


def read_messages(
    log_path: Path = DEFAULT_MESSAGE_LOG,
    *,
    context_id: str | None = None,
    task_id: str | None = None,
    decision_cycle_id: str | None = None,
) -> list[dict[str, Any]]:
    rows = _load_jsonl(log_path)
    if context_id is not None:
        rows = [row for row in rows if row.get("contextId") == context_id]
    if task_id is not None:
        rows = [row for row in rows if row.get("taskId") == task_id]
    if decision_cycle_id is not None:
        rows = [row for row in rows if row.get("decision_cycle_id") == decision_cycle_id]
    return rows


def _default_retry_policy(event_type: str) -> dict[str, Any]:
    return {
        "retry_after": "PT5M",
        "max_retries": 2,
        "reason_code": f"a2a-{event_type}",
    }


def _normalize_retry_policy(
    retry_policy: dict[str, Any] | None,
    *,
    event_type: str,
) -> dict[str, Any]:
    policy = dict(retry_policy or _default_retry_policy(event_type))
    if not str(policy.get("retry_after") or "").strip():
        raise A2AMessageError("retry_policy.retry_after is required")
    if not str(policy.get("reason_code") or "").strip():
        raise A2AMessageError("retry_policy.reason_code is required")
    try:
        max_retries = int(policy.get("max_retries"))
    except (TypeError, ValueError) as exc:
        raise A2AMessageError("retry_policy.max_retries must be an integer") from exc
    if max_retries < 0:
        raise A2AMessageError("retry_policy.max_retries must be non-negative")
    policy["max_retries"] = max_retries
    return policy


def _acquire_lock(path: Path, *, timeout_seconds: float = LOCK_TIMEOUT_SECONDS) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            return os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"could not acquire A2A message lock: {path}")
            time.sleep(LOCK_POLL_SECONDS)


def _release_lock(path: Path, fd: int) -> None:
    os.close(fd)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _assert_unique(rows: list[dict[str, Any]], *, event_id: str, idempotency_key: str) -> None:
    for row in rows:
        if row.get("event_id") == event_id:
            raise A2AMessageError(f"duplicate event_id: {event_id}")
        if row.get("idempotency_key") == idempotency_key:
            raise A2AMessageError(f"duplicate idempotency_key: {idempotency_key}")


def build_message(
    *,
    context_id: str,
    task_id: str,
    decision_cycle_id: str,
    event_type: str,
    sender: str,
    receiver: str,
    payload_ref: str,
    access_level: str = "project",
    retry_policy: dict[str, Any] | None = None,
    event_id: str | None = None,
    parent_event_id: str | None = None,
    idempotency_key: str | None = None,
    timestamp: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_id = _require_text(context_id, "context_id")
    task_id = _require_text(task_id, "task_id")
    decision_cycle_id = _require_text(decision_cycle_id, "decision_cycle_id")
    event_type = _require_text(event_type, "event_type")
    sender = _require_text(sender, "sender")
    receiver = _require_text(receiver, "receiver")
    payload_ref = _require_text(payload_ref, "payload_ref")
    access_level = _require_text(access_level, "access_level")
    if event_type not in EVENT_TYPES:
        raise A2AMessageError(f"event_type must be one of {', '.join(EVENT_TYPES)}")
    if access_level not in ACCESS_LEVELS:
        raise A2AMessageError(f"access_level must be one of {', '.join(sorted(ACCESS_LEVELS))}")

    event_id = event_id or f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    idempotency_key = idempotency_key or (
        f"{context_id}:{task_id}:{decision_cycle_id}:{event_type}:{event_id}"
    )
    message = {
        "schema_version": SCHEMA_VERSION,
        "message_id": event_id,
        "event_id": event_id,
        "parent_event_id": parent_event_id or "",
        "contextId": context_id,
        "taskId": task_id,
        "decision_cycle_id": decision_cycle_id,
        "event_type": event_type,
        "sender": sender,
        "receiver": receiver,
        "timestamp": timestamp or _now_iso(),
        "access_level": access_level,
        "idempotency_key": idempotency_key,
        "retry_policy": _normalize_retry_policy(retry_policy, event_type=event_type),
        "payload_ref": payload_ref,
        "route": {"from": sender, "to": receiver},
        "task_context": {
            "contextId": context_id,
            "taskId": task_id,
            "decision_cycle_id": decision_cycle_id,
        },
        "metadata": dict(metadata or {}),
    }
    return message


def emit_message(
    *,
    log_path: Path = DEFAULT_MESSAGE_LOG,
    context_id: str,
    task_id: str,
    decision_cycle_id: str,
    event_type: str,
    sender: str,
    receiver: str,
    payload_ref: str,
    access_level: str = "project",
    retry_policy: dict[str, Any] | None = None,
    event_id: str | None = None,
    parent_event_id: str | None = None,
    idempotency_key: str | None = None,
    timestamp: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message = build_message(
        context_id=context_id,
        task_id=task_id,
        decision_cycle_id=decision_cycle_id,
        event_type=event_type,
        sender=sender,
        receiver=receiver,
        payload_ref=payload_ref,
        access_level=access_level,
        retry_policy=retry_policy,
        event_id=event_id,
        parent_event_id=parent_event_id,
        idempotency_key=idempotency_key,
        timestamp=timestamp,
        metadata=metadata,
    )

    lock_path = log_path.with_name(f"{log_path.name}.lock")
    fd = _acquire_lock(lock_path)
    try:
        rows = _load_jsonl(log_path)
        _assert_unique(
            rows,
            event_id=str(message["event_id"]),
            idempotency_key=str(message["idempotency_key"]),
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message, ensure_ascii=False, sort_keys=True) + "\n")
    finally:
        _release_lock(lock_path, fd)
    return message


def _parse_metadata(items: list[str]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw in items:
        key, sep, value = raw.partition("=")
        if not sep or not key.strip():
            raise A2AMessageError("--metadata entries must be KEY=VALUE")
        metadata[key.strip()] = value.strip()
    return metadata


def _main_emit(args: argparse.Namespace) -> int:
    message = emit_message(
        log_path=args.log,
        context_id=args.context_id,
        task_id=args.task_id,
        decision_cycle_id=args.decision_cycle_id,
        event_type=args.event_type,
        sender=args.sender,
        receiver=args.receiver,
        payload_ref=args.payload_ref,
        access_level=args.access_level,
        retry_policy={
            "retry_after": args.retry_after,
            "max_retries": args.max_retries,
            "reason_code": args.reason_code,
        },
        event_id=args.event_id,
        parent_event_id=args.parent_event_id,
        idempotency_key=args.idempotency_key,
        timestamp=args.timestamp,
        metadata=_parse_metadata(args.metadata),
    )
    print(json.dumps(message, ensure_ascii=False, indent=2))
    return 0


def _main_list(args: argparse.Namespace) -> int:
    rows = read_messages(
        args.log,
        context_id=args.context_id,
        task_id=args.task_id,
        decision_cycle_id=args.decision_cycle_id,
    )
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit and inspect local A2A runtime messages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit = subparsers.add_parser("emit")
    emit.add_argument("--log", type=Path, default=DEFAULT_MESSAGE_LOG)
    emit.add_argument("--context-id", required=True)
    emit.add_argument("--task-id", required=True)
    emit.add_argument("--decision-cycle-id", required=True)
    emit.add_argument("--event-type", choices=EVENT_TYPES, required=True)
    emit.add_argument("--sender", required=True)
    emit.add_argument("--receiver", required=True)
    emit.add_argument("--payload-ref", required=True)
    emit.add_argument("--access-level", choices=sorted(ACCESS_LEVELS), default="project")
    emit.add_argument("--retry-after", default="PT5M")
    emit.add_argument("--max-retries", type=int, default=2)
    emit.add_argument("--reason-code", default="a2a-message")
    emit.add_argument("--event-id")
    emit.add_argument("--parent-event-id")
    emit.add_argument("--idempotency-key")
    emit.add_argument("--timestamp")
    emit.add_argument("--metadata", action="append", default=[])
    emit.set_defaults(func=_main_emit)

    list_cmd = subparsers.add_parser("list")
    list_cmd.add_argument("--log", type=Path, default=DEFAULT_MESSAGE_LOG)
    list_cmd.add_argument("--context-id")
    list_cmd.add_argument("--task-id")
    list_cmd.add_argument("--decision-cycle-id")
    list_cmd.set_defaults(func=_main_list)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (A2AMessageError, TimeoutError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
