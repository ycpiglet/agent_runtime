"""Recover dead-worker claims so a stalled wave/goal can make progress again.

The deadlock: when a worker process/pane dies mid-task, its claim JSON stays in
an *active* status. ``wave_dispatcher`` then skips that task forever ("task
already has an active claim"), so the wave never completes and downstream work
stalls. There is no other safe recovery path — ``task_claim_dispatcher release``
requires independent cross-verification and is meant for *completed* work, not
*abandoned* work.

This reaper breaks that deadlock safely. A claim is **provably dead** only when
its lease deadline (``expires_at`` / ``lease.expires_at``, which a live worker
keeps refreshing via heartbeat) has passed by more than a grace period. Such a
claim is transitioned to the terminal ``expired`` status — which is in none of
the dispatcher/footprint active sets nor the done set, so the unit becomes
``pending`` and re-dispatchable. The original status is preserved in
``recovered_from_status`` and every reap is audited (pane event + stop event).

Guardrails (safety first):
  - a claim whose lease is still valid (heartbeating, or within grace) is NEVER touched;
  - orchestrator claims are never reaped;
  - claims with no lease info are skipped (death cannot be proven), not reaped;
  - dry-run by default — only ``--apply`` mutates state;
  - the sweep processes ALL claims, skipping the un-actionable and recovering the rest;
  - reaping is idempotent (an already-``expired`` claim is left alone).

Usage:
  python scripts/claim_reaper.py                 # dry-run report (no writes)
  python scripts/claim_reaper.py --apply         # recover provably-dead claims
  python scripts/claim_reaper.py --grace-seconds 1800 --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pane_event_log
import stop_events

REAPED_STATUS = "expired"
DEFAULT_GRACE_SECONDS = 600
GRACE_ENV = "AGENT_RUNTIME_REAPER_GRACE_SECONDS"
ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}

# Union of every "active" status the dispatchers/footprint gate recognize, so a
# claim that blocks dispatch is a reap candidate. The reaped status (``expired``)
# is deliberately in none of these.
REAPABLE_ACTIVE_STATUSES = {
    "active",
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "running",
    "waiting_review",
    "working",
}


def _parse_now(value: str | None = None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _coerce_now(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    return _parse_now(value)


def _try_parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return _parse_now(text)
    except ValueError:
        return None


def default_grace() -> int:
    raw = os.environ.get(GRACE_ENV)
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            pass
    return DEFAULT_GRACE_SECONDS


def _claim_dir(root: Path) -> Path:
    return Path(root) / "agents" / "runtime" / "task_claims"


def _read_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    base = _claim_dir(root)
    if not base.is_dir():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(base.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            records.append((path, payload))
    return records


def _is_orchestrator(claim: dict[str, Any]) -> bool:
    role = str(claim.get("agent_role") or "").strip().lower()
    if role in ORCHESTRATOR_ROLES:
        return True
    mode = str(claim.get("mode") or "").strip().lower()
    scope = str(claim.get("worker_scope") or "").strip().lower()
    return mode == "orchestrator" or scope == "orchestrator"


def _latest_deadline(claim: dict[str, Any]) -> datetime | None:
    """The furthest-future lease deadline on the claim (refreshed by heartbeat)."""
    candidates: list[datetime] = []
    top = _try_parse(claim.get("expires_at"))
    if top is not None:
        candidates.append(top)
    lease = claim.get("lease")
    if isinstance(lease, dict):
        leased = _try_parse(lease.get("expires_at"))
        if leased is not None:
            candidates.append(leased)
    return max(candidates) if candidates else None


def classify_claim(claim: dict[str, Any], now: datetime, grace_seconds: int) -> tuple[str, str]:
    """Return (decision, reason). decision in {"live", "dead", "skip"}."""
    status = str(claim.get("status") or "").strip().lower()
    if status not in REAPABLE_ACTIVE_STATUSES:
        return "skip", "not-active"
    if _is_orchestrator(claim):
        return "skip", "orchestrator-claim"
    deadline = _latest_deadline(claim)
    if deadline is None:
        return "skip", "no-lease-info"
    if now <= deadline + timedelta(seconds=grace_seconds):
        return "live", "lease-valid"
    return "dead", "lease-expired"


try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import atomic_io
except ModuleNotFoundError:  # pragma: no cover
    from scripts import atomic_io


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    # Shared durable primitive: temp -> fsync -> atomic rename (preserves unsorted keys).
    atomic_io.write_json_atomic(path, payload)


LOCK_TIMEOUT_SECONDS = 5.0
LOCK_POLL_SECONDS = 0.01


def _acquire_lock(path: Path):
    """Exclusive per-claim lock so concurrent reapers transition a claim once."""
    import time

    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    while True:
        try:
            return os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            # Windows can raise PermissionError while another thread/process is
            # mid-unlink of the lock file; treat it like "held" and retry.
            if time.monotonic() >= deadline:
                raise TimeoutError(f"reap lock timeout: {path}")
            import time as _t

            _t.sleep(LOCK_POLL_SECONDS)


def _release_lock(path: Path, fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        path.unlink()
    except OSError:
        pass


def _read_one(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _reap(root: Path, path: Path, claim: dict[str, Any], now: datetime, grace_seconds: int) -> bool:
    """Atomically transition a provably-dead claim to ``expired``.

    Returns True iff THIS call performed the transition. A per-claim lock plus a
    re-classification under the lock guarantee that, under concurrent reapers, a
    claim is reaped at most once and is never reaped if a heartbeat resurrected it
    (re-classified live) in the race window between the initial read and the lock.
    """
    lock = path.with_name(f"{path.name}.reap.lock")
    fd = _acquire_lock(lock)
    audit: dict[str, str] | None = None
    try:
        current = _read_one(path)
        if current is None:
            return False
        decision, _reason = classify_claim(current, now, grace_seconds)
        if decision != "dead":
            return False  # already reaped, or resurrected by a heartbeat
        prior = str(current.get("status") or "")
        now_text = now.isoformat(timespec="seconds")
        current["status"] = REAPED_STATUS
        current["recovered_from_status"] = prior
        current["reaped_at"] = now_text
        current["reaped_by"] = "claim_reaper"
        current["reaped_reason"] = "lease-expired"
        current["updated_at"] = now_text
        _write_json_atomic(path, current)
        audit = {
            "claim_id": current.get("claim_id", ""),
            "task_id": current.get("task_id", ""),
            "task_set_id": current.get("task_set_id", ""),
            "worktree_path": current.get("worktree_path", ""),
            "prior": prior,
            "now_text": now_text,
        }
    finally:
        _release_lock(lock, fd)

    if audit is None:
        return False
    # Audit trail is best-effort and runs outside the lock: a logging failure must
    # never block recovery, and only the winning reaper records (no double audit).
    try:
        pane_event_log.append_event(
            root,
            {
                "event": "claim_reaped",
                "actor": "claim_reaper",
                "actor_role": "orchestrator",
                "claim_id": audit["claim_id"],
                "task_id": audit["task_id"],
                "task_set_id": audit["task_set_id"],
                "worktree_path": audit["worktree_path"],
                "message": (
                    f"Reaped dead claim (was {audit['prior']}); lease expired beyond grace. "
                    "Unit is now re-dispatchable."
                ),
                "ts": audit["now_text"],
            },
        )
    except Exception:  # noqa: BLE001
        pass
    stop_events.record_stop_event(
        root,
        source="claim_reaper",
        reason_code="dead_claim",
        action="reaped",
        klass="recoverable",
        claim_id=audit["claim_id"],
        task_id=audit["task_id"],
        message=f"was {audit['prior']}",
        now=now,
    )
    return True


def _entry(path: Path, claim: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "claim_id": claim.get("claim_id") or path.stem,
        "task_id": claim.get("task_id", ""),
        "reason": reason,
        "worktree_path": claim.get("worktree_path", ""),
    }


def sweep(
    root: Path,
    *,
    now: str | datetime | None = None,
    apply: bool = False,
    grace_seconds: int | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    now_dt = _coerce_now(now)
    grace = default_grace() if grace_seconds is None else int(grace_seconds)
    report: dict[str, Any] = {
        "now": now_dt.isoformat(timespec="seconds"),
        "grace_seconds": grace,
        "apply": apply,
        "reaped": [],
        "would_reap": [],
        "live": [],
        "skipped": [],
    }
    for path, claim in _read_claims(root):
        decision, reason = classify_claim(claim, now_dt, grace)
        entry = _entry(path, claim, reason)
        if decision == "live":
            report["live"].append(entry)
        elif decision == "skip":
            report["skipped"].append(entry)
            # Surface active claims we declined to reap (not terminal ones).
            if apply and reason in ("orchestrator-claim", "no-lease-info"):
                stop_events.record_stop_event(
                    root,
                    source="claim_reaper",
                    reason_code="dead_claim",
                    action="skipped",
                    klass="recoverable",
                    claim_id=entry["claim_id"],
                    task_id=entry["task_id"],
                    message=f"skipped: {reason}",
                    now=now_dt,
                )
        else:  # dead
            if apply:
                if _reap(root, path, claim, now_dt, grace):
                    report["reaped"].append(entry)
                else:
                    # Another concurrent reaper won the race, or a heartbeat
                    # resurrected the claim under the lock.
                    report["skipped"].append({**entry, "reason": "reap-superseded"})
            else:
                report["would_reap"].append(entry)
    return report


# --------------------------------------------------------------------------- CLI


def _render_human(report: dict[str, Any]) -> str:
    lines = [
        "claim-reaper: " + ("apply" if report["apply"] else "dry-run"),
        f"now={report['now']} grace_seconds={report['grace_seconds']}",
    ]
    reaped = report["reaped"] if report["apply"] else report["would_reap"]
    verb = "reaped" if report["apply"] else "would-reap"
    lines.append(f"{verb}={len(reaped)} live={len(report['live'])} skipped={len(report['skipped'])}")
    for entry in reaped:
        lines.append(f"  {verb}: {entry['claim_id']} task={entry['task_id']} ({entry['reason']})")
    for entry in report["skipped"]:
        lines.append(f"  skipped: {entry['claim_id']} ({entry['reason']})")
    if not report["apply"] and reaped:
        lines.append("re-run with --apply to recover the claims above")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recover dead-worker claims (deadlock breaker). Dry-run by default."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="perform reaping (default: dry-run report)")
    parser.add_argument(
        "--grace-seconds",
        type=int,
        default=None,
        help=f"seconds past lease expiry before a claim is provably dead (default {DEFAULT_GRACE_SECONDS} or ${GRACE_ENV})",
    )
    parser.add_argument("--now", help="ISO timestamp override (testing/determinism)")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = sweep(args.root, now=args.now, apply=args.apply, grace_seconds=args.grace_seconds)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_render_human(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
