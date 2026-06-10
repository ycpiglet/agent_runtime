"""Create and release parallel-agent task claim records.

The dispatcher writes identity-rich claim records while keeping machine identity
separate from the human-facing display name:

- agent_role: durable role expectation, for policy/routing;
- agent_instance_id: unique execution unit;
- display_name: readable label for UI/status surfaces;
- callsite_id: terminal or launcher origin.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-task-claim/v1"
ACTIVE_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slug(value: str, *, sep: str = "-") -> str:
    text = re.sub(r"[^A-Za-z0-9]+", sep, value.strip().lower())
    text = re.sub(rf"{re.escape(sep)}+", sep, text)
    return text.strip(sep) or "item"


def _display_role(role: str) -> str:
    return _slug(role, sep="_")


def _role_initials(role: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", role.lower()) if part]
    if not parts:
        return "ag"
    if len(parts) == 1:
        return parts[0][:2].ljust(2, "x")
    return "".join(part[0] for part in parts)[:4]


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _tz_label(value: datetime) -> str:
    offset = value.utcoffset()
    if offset == timedelta(hours=9):
        return "kst"
    if offset == timedelta(0):
        return "utc"
    if offset is None:
        return "local"
    total_minutes = int(offset.total_seconds() // 60)
    sign = "p" if total_minutes >= 0 else "m"
    total_minutes = abs(total_minutes)
    return f"utc{sign}{total_minutes // 60:02d}{total_minutes % 60:02d}"


def _claim_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _claim_files(root: Path) -> list[Path]:
    base = _claim_dir(root)
    if not base.is_dir():
        return []
    return sorted(base.glob("*.json"), key=lambda path: path.name.lower())


def _read_claim(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _read_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in _claim_files(root):
        payload = _read_claim(path)
        if payload is not None:
            records.append((path, payload))
    return records


def _is_active(payload: dict[str, Any]) -> bool:
    return str(payload.get("status") or "").strip().lower() in ACTIVE_STATUSES


def _next_slot(records: list[tuple[Path, dict[str, Any]]], *, role: str, mode: str) -> int:
    display_prefix = f"{_display_role(role)}@{_slug(mode)}-"
    used: set[int] = set()
    for _, payload in records:
        if not _is_active(payload):
            continue
        if str(payload.get("agent_role") or "") != role:
            continue
        display_name = str(payload.get("display_name") or "")
        if not display_name.startswith(display_prefix):
            continue
        suffix = display_name[len(display_prefix) :]
        if suffix.isdigit():
            used.add(int(suffix))
    slot = 1
    while slot in used:
        slot += 1
    return slot


def _ensure_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(text, encoding="utf-8")


def _build_claim(args: argparse.Namespace, records: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    now = _parse_now(args.now)
    expires_at = now + timedelta(minutes=args.lease_minutes)
    suffix = _slug(args.suffix or uuid.uuid4().hex[:4])
    task_slug = _slug(args.task_id)
    mode = _slug(args.mode or "work")
    slot = _next_slot(records, role=args.agent_role, mode=mode)
    slot_text = f"{slot:02d}"
    display_name = args.display_name or f"{_display_role(args.agent_role)}@{mode}-{slot_text}"
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    agent_instance_id = args.agent_instance_id or (
        f"{_role_initials(args.agent_role)}-{timestamp}-{_tz_label(now)}-{suffix}"
    )
    claim_id = args.claim_id or f"CLAIM-{timestamp}-{task_slug}-{suffix}"
    worktree_path = args.worktree_path or f".worktrees/{args.task_id}"
    branch = args.branch or f"codex/{task_slug}-{mode}-{slot_text}"
    callsite_id = args.callsite_id or f"terminal:wt-{task_slug}:tab-{slot_text}"
    handoff_path = args.handoff_path or f"agents/runtime/task_claims/{claim_id}.handoff.md"
    log_path = args.log_path or f"agents/runtime/task_claims/{claim_id}.log.md"
    claimed_at = now.isoformat(timespec="seconds")
    expires_text = expires_at.isoformat(timespec="seconds")

    return {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "task_id": args.task_id,
        "agent_role": args.agent_role,
        "team_id": args.team_id,
        "agent_instance_id": agent_instance_id,
        "display_name": display_name,
        "callsite_id": callsite_id,
        "pane_id": args.pane_id or callsite_id,
        "mode": mode,
        "status": "claimed",
        "phase": args.phase,
        "progress_pct": args.progress_pct,
        "worktree_path": worktree_path,
        "branch": branch,
        "claimed_at": claimed_at,
        "last_heartbeat": claimed_at,
        "expires_at": expires_text,
        "lease": {
            "claimed_at": claimed_at,
            "heartbeat_at": claimed_at,
            "expires_at": expires_text,
        },
        "handoff_path": handoff_path,
        "log_path": log_path,
        "tags": list(args.tag or ()),
    }


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = payload.get("status")
    path = payload.get("path")
    claim = payload.get("claim") or {}
    print(f"task-claim-dispatcher: {status}")
    if path:
        print(f"path={path}")
    if isinstance(claim, dict):
        print(f"claim_id={claim.get('claim_id')}")
        print(f"display_name={claim.get('display_name')}")


def cmd_create(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    records = _read_claims(root)
    for path, payload in records:
        if not _is_active(payload):
            continue
        if str(payload.get("task_id") or "") == args.task_id:
            print(
                f"task already has an active claim: {args.task_id} ({_rel(root, path)})",
                file=sys.stderr,
            )
            return 1

    claim = _build_claim(args, records)
    claim_dir = _claim_dir(root)
    claim_dir.mkdir(parents=True, exist_ok=True)
    claim_path = claim_dir / f"{claim['claim_id']}.json"
    if claim_path.exists():
        print(f"claim file already exists: {_rel(root, claim_path)}", file=sys.stderr)
        return 1

    _ensure_text_file(
        root / str(claim["handoff_path"]),
        "\n".join(
            [
                f"# Handoff: {claim['display_name']}",
                "",
                f"- claim_id: {claim['claim_id']}",
                f"- task_id: {claim['task_id']}",
                f"- worktree_path: {claim['worktree_path']}",
                f"- branch: {claim['branch']}",
                "- status: claimed",
                "",
            ]
        ),
    )
    _ensure_text_file(
        root / str(claim["log_path"]),
        "\n".join(
            [
                f"# Claim Log: {claim['display_name']}",
                "",
                f"- claimed_at: {claim['claimed_at']}",
                f"- agent_instance_id: {claim['agent_instance_id']}",
                f"- callsite_id: {claim['callsite_id']}",
                "",
            ]
        ),
    )

    claim_path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _emit({"status": "created", "path": _rel(root, claim_path), "claim": claim}, as_json=args.json)
    return 0


def _find_claim(root: Path, claim_id: str) -> tuple[Path, dict[str, Any]] | None:
    for path, payload in _read_claims(root):
        if str(payload.get("claim_id") or "") == claim_id:
            return path, payload
    return None


def cmd_release(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    found = _find_claim(root, args.claim_id)
    if found is None:
        print(f"claim not found: {args.claim_id}", file=sys.stderr)
        return 1

    path, claim = found
    missing = [
        str(claim.get(field) or "")
        for field in ("handoff_path", "log_path")
        if not str(claim.get(field) or "").strip() or not (root / str(claim.get(field))).exists()
    ]
    if missing:
        print(f"handoff/log pointer is missing for claim: {args.claim_id}", file=sys.stderr)
        return 1

    now_text = _parse_now(args.now).isoformat(timespec="seconds")
    claim["status"] = "released"
    claim["released_at"] = now_text
    claim["last_heartbeat"] = now_text
    lease = claim.get("lease")
    if isinstance(lease, dict):
        lease["heartbeat_at"] = now_text
    path.write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _emit({"status": "released", "path": _rel(root, path), "claim": claim}, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create/release parallel agent task claims")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a task claim")
    create.add_argument("--task-id", required=True)
    create.add_argument("--agent-role", required=True)
    create.add_argument("--team-id", default="agent-runtime-core")
    create.add_argument("--mode", default="work")
    create.add_argument("--pane-id")
    create.add_argument("--phase", default="claim-created")
    create.add_argument("--progress-pct", type=int, default=0)
    create.add_argument("--tag", action="append", default=[])
    create.add_argument("--now")
    create.add_argument("--suffix")
    create.add_argument("--display-name")
    create.add_argument("--agent-instance-id")
    create.add_argument("--callsite-id")
    create.add_argument("--claim-id")
    create.add_argument("--worktree-path")
    create.add_argument("--branch")
    create.add_argument("--handoff-path")
    create.add_argument("--log-path")
    create.add_argument("--lease-minutes", type=int, default=30)
    create.add_argument("--json", action="store_true")
    create.set_defaults(func=cmd_create)

    release = sub.add_parser("release", help="Release a task claim after handoff/log files exist")
    release.add_argument("--claim-id", required=True)
    release.add_argument("--now")
    release.add_argument("--json", action="store_true")
    release.set_defaults(func=cmd_release)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
