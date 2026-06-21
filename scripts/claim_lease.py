"""Atomic lease primitives for race-safe local claim ownership."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-claim-lease/v1"
CLAIMS_DIR = Path("agents/runtime/claims")
LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.02


def _parse_now(value: str | None = None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "claim"


def _lease_path(root: Path, resource_id: str) -> Path:
    return root / CLAIMS_DIR / f"{_slug(resource_id)}.lease.json"


def _lock_path(lease_path: Path) -> Path:
    return lease_path.with_name(f"{lease_path.name}.lock")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _acquire_lock(path: Path, *, timeout_seconds: float = LOCK_TIMEOUT_SECONDS) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii", errors="ignore"))
            return fd
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"could not acquire lease lock: {path}")
            time.sleep(LOCK_POLL_SECONDS)


def _release_lock(path: Path, fd: int) -> None:
    os.close(fd)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import atomic_io
except ModuleNotFoundError:  # pragma: no cover
    from scripts import atomic_io


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    # Shared durable primitive: temp -> fsync -> atomic rename (TASK crash-recovery).
    atomic_io.write_json_atomic(path, payload, sort_keys=True)


def _is_expired(lease: dict[str, Any], now: datetime) -> bool:
    raw = str(lease.get("expires_at") or "")
    if not raw:
        return True
    try:
        expires_at = _parse_now(raw)
    except ValueError:
        return True
    return expires_at <= now


def _source_exists(root: Path, source_path: str | None) -> bool:
    if not source_path:
        return True
    path = Path(source_path)
    if not path.is_absolute():
        path = root / path
    return path.exists()


def _build_lease(
    *,
    resource_id: str,
    owner_id: str,
    now: datetime,
    ttl_seconds: int,
    source_path: str | None,
    recovered_from: str | None = None,
) -> dict[str, Any]:
    expires_at = now + timedelta(seconds=ttl_seconds)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "resource_id": resource_id,
        "owner_id": owner_id,
        "claimed_at": now.isoformat(timespec="seconds"),
        "heartbeat_at": now.isoformat(timespec="seconds"),
        "expires_at": expires_at.isoformat(timespec="seconds"),
        "ttl_seconds": ttl_seconds,
        "source_path": source_path or "",
    }
    if recovered_from:
        payload["recovered_from"] = recovered_from
    return payload


def acquire_claim(
    root: Path,
    *,
    resource_id: str,
    owner_id: str,
    ttl_seconds: int = 1800,
    source_path: str | None = None,
    recover_stale: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now = now or _parse_now()
    lease_path = _lease_path(root, resource_id)
    lock = _lock_path(lease_path)
    fd = _acquire_lock(lock)
    try:
        existing = _read_json(lease_path) if lease_path.exists() else None
        if existing and not _is_expired(existing, now):
            return {
                "status": "blocked",
                "reason": "lease-active",
                "acquired": False,
                "lease_path": _rel(root, lease_path),
                "owner_id": existing.get("owner_id", ""),
                "expires_at": existing.get("expires_at", ""),
            }
        if existing and not recover_stale:
            return {
                "status": "blocked",
                "reason": "lease-stale-recovery-not-enabled",
                "acquired": False,
                "lease_path": _rel(root, lease_path),
                "owner_id": existing.get("owner_id", ""),
            }
        if existing and recover_stale and not _source_exists(root, source_path or str(existing.get("source_path") or "")):
            return {
                "status": "blocked",
                "reason": "source-missing",
                "acquired": False,
                "lease_path": _rel(root, lease_path),
                "owner_id": existing.get("owner_id", ""),
            }
        if not existing and not _source_exists(root, source_path):
            return {
                "status": "blocked",
                "reason": "source-missing",
                "acquired": False,
                "lease_path": _rel(root, lease_path),
            }
        recovered_from = str(existing.get("owner_id") or "") if existing else None
        lease = _build_lease(
            resource_id=resource_id,
            owner_id=owner_id,
            now=now,
            ttl_seconds=ttl_seconds,
            source_path=source_path or (str(existing.get("source_path") or "") if existing else None),
            recovered_from=recovered_from,
        )
        _write_json_atomic(lease_path, lease)
        return {
            "status": "acquired",
            "reason": "ok",
            "acquired": True,
            "lease_path": _rel(root, lease_path),
            "lease": lease,
        }
    finally:
        _release_lock(lock, fd)


def release_claim(root: Path, *, resource_id: str, owner_id: str) -> dict[str, Any]:
    root = root.resolve()
    lease_path = _lease_path(root, resource_id)
    lock = _lock_path(lease_path)
    fd = _acquire_lock(lock)
    try:
        lease = _read_json(lease_path)
        if not lease:
            return {"status": "missing", "released": False, "lease_path": _rel(root, lease_path)}
        if str(lease.get("owner_id") or "") != owner_id:
            return {
                "status": "blocked",
                "reason": "owner-mismatch",
                "released": False,
                "lease_path": _rel(root, lease_path),
                "owner_id": lease.get("owner_id", ""),
            }
        lease_path.unlink(missing_ok=True)
        return {"status": "released", "released": True, "lease_path": _rel(root, lease_path)}
    finally:
        _release_lock(lock, fd)


def heartbeat_claim(
    root: Path,
    *,
    resource_id: str,
    owner_id: str,
    ttl_seconds: int = 1800,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    now = now or _parse_now()
    lease_path = _lease_path(root, resource_id)
    lock = _lock_path(lease_path)
    fd = _acquire_lock(lock)
    try:
        lease = _read_json(lease_path)
        if not lease:
            return {"status": "missing", "updated": False, "lease_path": _rel(root, lease_path)}
        if str(lease.get("owner_id") or "") != owner_id:
            return {
                "status": "blocked",
                "reason": "owner-mismatch",
                "updated": False,
                "lease_path": _rel(root, lease_path),
                "owner_id": lease.get("owner_id", ""),
            }
        lease["heartbeat_at"] = now.isoformat(timespec="seconds")
        lease["expires_at"] = (now + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds")
        lease["ttl_seconds"] = ttl_seconds
        _write_json_atomic(lease_path, lease)
        return {"status": "updated", "updated": True, "lease_path": _rel(root, lease_path), "lease": lease}
    finally:
        _release_lock(lock, fd)


def _print(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atomic local claim lease primitive")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    acquire = sub.add_parser("acquire")
    acquire.add_argument("--resource-id", required=True)
    acquire.add_argument("--owner-id", required=True)
    acquire.add_argument("--ttl-seconds", type=int, default=1800)
    acquire.add_argument("--source-path")
    acquire.add_argument("--recover-stale", action="store_true")
    acquire.add_argument("--now")

    release = sub.add_parser("release")
    release.add_argument("--resource-id", required=True)
    release.add_argument("--owner-id", required=True)

    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("--resource-id", required=True)
    heartbeat.add_argument("--owner-id", required=True)
    heartbeat.add_argument("--ttl-seconds", type=int, default=1800)
    heartbeat.add_argument("--now")

    args = parser.parse_args(argv)
    try:
        if args.command == "acquire":
            return _print(
                acquire_claim(
                    args.root,
                    resource_id=args.resource_id,
                    owner_id=args.owner_id,
                    ttl_seconds=args.ttl_seconds,
                    source_path=args.source_path,
                    recover_stale=args.recover_stale,
                    now=_parse_now(args.now),
                )
            )
        if args.command == "release":
            return _print(release_claim(args.root, resource_id=args.resource_id, owner_id=args.owner_id))
        if args.command == "heartbeat":
            return _print(
                heartbeat_claim(
                    args.root,
                    resource_id=args.resource_id,
                    owner_id=args.owner_id,
                    ttl_seconds=args.ttl_seconds,
                    now=_parse_now(args.now),
                )
            )
    except TimeoutError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
