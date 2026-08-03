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
  - apply holds the checkout claim-store lock and revalidates durable authority
    immediately before every atomic claim transition;
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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_runtime import claim_store

import pane_event_log
import stop_events

REAPED_STATUS = "expired"
DEFAULT_GRACE_SECONDS = claim_store.DEFAULT_CLAIM_GRACE_SECONDS
GRACE_ENV = claim_store.CLAIM_GRACE_ENV
ORCHESTRATOR_ROLES = {"orchestrator", "release-orchestrator"}
# Skip reason for an orchestrator claim whose lease is provably dead. It stays a
# skip (never auto-reaped) but is surfaced separately so the deadlock is visible.
ORCHESTRATOR_EXPIRED_REASON = "orchestrator-claim-expired"
# Skip reasons that describe a claim no automated path can ever end. Each one
# needs an owner-bound `task_claim_dispatcher.py terminalize` to clear.
OWNER_RECOVERY_REASONS = frozenset({ORCHESTRATOR_EXPIRED_REASON, "no-lease-info"})

# Use the same closed status vocabulary as closure and dispatch. The reaped
# status (``expired``) is deliberately outside this active set.
REAPABLE_ACTIVE_STATUSES = claim_store.ACTIVE_CLAIM_STATUSES


class _ClaimStoreAuthorityChanged(RuntimeError):
    """The inspected store changed before an authorized reap mutation."""


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


def default_grace() -> int:
    return claim_store.resolve_claim_grace()


def _claim_dir(root: Path) -> Path:
    return Path(root) / "agents" / "runtime" / "task_claims"


def _read_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    base = _claim_dir(root)
    if not base.is_dir():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(base.glob("*.json"), key=lambda item: item.name.lower()):
        payload = claim_store.read_claim_payload(path)
        records.append((path, payload))
    return records


def _is_orchestrator(claim: dict[str, Any]) -> bool:
    role = str(claim.get("agent_role") or "").strip().lower()
    if role in ORCHESTRATOR_ROLES:
        return True
    mode = str(claim.get("mode") or "").strip().lower()
    scope = str(claim.get("worker_scope") or "").strip().lower()
    return mode == "orchestrator" or scope == "orchestrator"


def classify_claim(claim: dict[str, Any], now: datetime, grace_seconds: int) -> tuple[str, str]:
    """Return (decision, reason). decision in {"live", "dead", "skip"}."""
    liveness = claim_store.classify_claim_liveness(
        claim,
        now=now,
        grace_seconds=grace_seconds,
    )
    if _is_orchestrator(claim):
        # Orchestrator claims are never auto-reaped: only a human owner may end
        # one. But mode must not hide the lease state. Reporting a dead
        # orchestrator claim with the same reason as a healthy one is what let
        # CLAIM-20260803-002651-task-ar-655-5f27 sit expired and invisible for
        # 5.4h while it deadlocked its own taskset.
        if liveness.state == "expired":
            return "skip", ORCHESTRATOR_EXPIRED_REASON
        if liveness.state == "indeterminate" and liveness.reason == "deadline-missing":
            # Strictly worse than an expired claim: it has no deadline at all,
            # so it can never expire, never be reaped, and never be proven
            # live. Without surfacing it here it is an invisible permanent
            # deadlock. Do not let the orchestrator branch mask it.
            return "skip", "no-lease-info"
        return "skip", "orchestrator-claim"
    if liveness.state == "live":
        return "live", "lease-valid"
    if liveness.state == "expired":
        return "dead", "lease-expired"
    if liveness.state == "inactive":
        return "skip", "not-active"
    return "skip", "lease-indeterminate"


try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import atomic_io
except ModuleNotFoundError:  # pragma: no cover
    from scripts import atomic_io


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    # Shared durable primitive: temp -> fsync -> atomic rename (preserves unsorted keys).
    atomic_io.write_json_atomic(path, payload)


def _read_one(path: Path) -> dict[str, Any]:
    return claim_store.read_claim_payload(path)


def _reap_locked(
    root: Path,
    path: Path,
    now: datetime,
    grace_seconds: int,
    store_snapshot: object,
    audit_queue: list[dict[str, Any]],
) -> bool:
    """Transition one dead claim while the checkout store lock is held."""

    audit: dict[str, str] | None = None
    current = _read_one(path)
    if current is None:
        return False
    decision, _reason = classify_claim(current, now, grace_seconds)
    if decision != "dead":
        return False  # already reaped, or resurrected by a heartbeat
    if not claim_store.verify_snapshot(root, store_snapshot):
        raise _ClaimStoreAuthorityChanged(
            "claim-store authority changed before reap mutation"
        )
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

    if audit is None:
        return False
    audit_queue.append({"kind": "reaped", **audit, "now": now})
    return True


def _record_audit(root: Path, audit: dict[str, Any]) -> None:
    """Record one completed decision after releasing claim-store authority."""

    if audit["kind"] == "skipped":
        try:
            stop_events.record_stop_event(
                root,
                source="claim_reaper",
                reason_code="dead_claim",
                action="skipped",
                klass="recoverable",
                claim_id=audit["claim_id"],
                task_id=audit["task_id"],
                message=f"skipped: {audit['reason']}",
                now=audit["now"],
            )
        except Exception:  # noqa: BLE001 - audit is best-effort
            pass
        return

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
    try:
        stop_events.record_stop_event(
            root,
            source="claim_reaper",
            reason_code="dead_claim",
            action="reaped",
            klass="recoverable",
            claim_id=audit["claim_id"],
            task_id=audit["task_id"],
            message=f"was {audit['prior']}",
            now=audit["now"],
        )
    except Exception:  # noqa: BLE001 - authority mutation already succeeded
        pass


def _reap(
    root: Path,
    path: Path,
    claim: dict[str, Any],
    now: datetime,
    grace_seconds: int,
    _store_snapshot: object | None = None,
    _audit_queue: list[dict[str, Any]] | None = None,
) -> bool:
    """Compatibility entrypoint that always establishes store authority."""

    root = Path(root).resolve()
    if _store_snapshot is not None:
        return _reap_locked(
            root,
            path,
            now,
            grace_seconds,
            _store_snapshot,
            _audit_queue if _audit_queue is not None else [],
        )
    audit_queue: list[dict[str, Any]] = []
    with claim_store.store_lock(root):
        inspection = claim_store.inspect_store(root)
        if (
            inspection.state not in {"initialized", "pristine"}
            or inspection.snapshot is None
        ):
            reaped = False
        else:
            reaped = _reap_locked(
                root,
                path,
                now,
                grace_seconds,
                inspection.snapshot,
                audit_queue,
            )
    for audit in audit_queue:
        _record_audit(root, audit)
    return reaped


def _entry(path: Path, claim: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "claim_id": claim.get("claim_id") or path.stem,
        "task_id": claim.get("task_id", ""),
        "reason": reason,
        "worktree_path": claim.get("worktree_path", ""),
    }


def _bounded_claim_store_finding(value: object) -> str:
    text = " ".join(str(value or "claim-store authority is invalid").split())
    return text[:256] or "claim-store authority is invalid"


def _set_claim_store_report(
    report: dict[str, Any],
    *,
    state: str,
    finding: object = None,
) -> None:
    report["claim_store"] = {
        "state": state,
        "finding": (
            None if finding is None else _bounded_claim_store_finding(finding)
        ),
    }


def _authorized_sweep(
    root: Path,
    *,
    report: dict[str, Any],
    inspection: object,
    now: datetime,
    grace_seconds: int,
    apply: bool,
    audit_queue: list[dict[str, Any]],
) -> None:
    snapshot = inspection.snapshot
    if snapshot is None:
        raise _ClaimStoreAuthorityChanged("claim-store snapshot is missing")
    for path, claim in _read_claims(root):
        decision, reason = classify_claim(claim, now, grace_seconds)
        entry_reason = reason
        if reason == "lease-indeterminate":
            liveness = claim_store.classify_claim_liveness(
                claim,
                now=now,
                grace_seconds=grace_seconds,
            )
            if liveness.reason == "deadline-missing":
                entry_reason = "no-lease-info"
        entry = _entry(path, claim, entry_reason)
        if decision == "live":
            report["live"].append(entry)
        elif decision == "skip":
            report["skipped"].append(entry)
            if entry_reason in OWNER_RECOVERY_REASONS:
                # Never reaped, but never silent either: an owner-bound
                # `task_claim_dispatcher.py terminalize` is the registered exit.
                # `no-lease-info` belongs here too - a claim with no deadline
                # can never expire, so it is a permanent deadlock, not a
                # transient unknown.
                report["needs_owner_recovery"].append(entry)
            if apply and entry_reason in (
                "orchestrator-claim",
                ORCHESTRATOR_EXPIRED_REASON,
                "no-lease-info",
            ):
                if not claim_store.verify_snapshot(root, snapshot):
                    raise _ClaimStoreAuthorityChanged(
                        "claim-store authority changed before skip audit"
                    )
                audit_queue.append(
                    {
                        "kind": "skipped",
                        "claim_id": entry["claim_id"],
                        "task_id": entry["task_id"],
                        "reason": reason,
                        "now": now,
                    }
                )
        elif apply:
            if _reap(
                root,
                path,
                claim,
                now,
                grace_seconds,
                _store_snapshot=snapshot,
                _audit_queue=audit_queue,
            ):
                report["reaped"].append(entry)
                refreshed = claim_store.inspect_store(root)
                if (
                    refreshed.state not in {"initialized", "pristine"}
                    or refreshed.snapshot is None
                ):
                    raise _ClaimStoreAuthorityChanged(
                        refreshed.finding
                        or "claim-store authority changed after reap mutation"
                    )
                snapshot = refreshed.snapshot
            else:
                report["skipped"].append(
                    {**entry, "reason": "reap-superseded"}
                )
        else:
            report["would_reap"].append(entry)
    if not claim_store.verify_snapshot(root, snapshot):
        raise _ClaimStoreAuthorityChanged(
            "claim-store authority changed during reap sweep"
        )


def sweep(
    root: Path,
    *,
    now: str | datetime | None = None,
    apply: bool = False,
    grace_seconds: int | None = None,
) -> dict[str, Any]:
    grace = claim_store.resolve_claim_grace(grace_seconds)
    root = Path(root).resolve()
    now_dt = _coerce_now(now)
    report: dict[str, Any] = {
        "now": now_dt.isoformat(timespec="seconds"),
        "grace_seconds": grace,
        "apply": apply,
        "reaped": [],
        "would_reap": [],
        "live": [],
        "skipped": [],
        "needs_owner_recovery": [],
        "claim_store": {
            "state": "integrity-invalid",
            "finding": "claim-store inspection was not completed",
        },
    }
    audit_queue: list[dict[str, Any]] = []
    try:
        if apply:
            with claim_store.store_lock(root):
                inspection = claim_store.inspect_store(root)
                _set_claim_store_report(
                    report,
                    state=inspection.state,
                    finding=inspection.finding,
                )
                if inspection.state not in {"initialized", "pristine"}:
                    return report
                _authorized_sweep(
                    root,
                    report=report,
                    inspection=inspection,
                    now=now_dt,
                    grace_seconds=grace,
                    apply=True,
                    audit_queue=audit_queue,
                )
        else:
            inspection = claim_store.inspect_store(root)
            _set_claim_store_report(
                report,
                state=inspection.state,
                finding=inspection.finding,
            )
            if inspection.state not in {"initialized", "pristine"}:
                return report
            _authorized_sweep(
                root,
                report=report,
                inspection=inspection,
                now=now_dt,
                grace_seconds=grace,
                apply=False,
                audit_queue=audit_queue,
            )
    except (
        _ClaimStoreAuthorityChanged,
        claim_store.ClaimStoreError,
        OSError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as exc:
        _set_claim_store_report(
            report,
            state="integrity-invalid",
            finding=exc,
        )
    finally:
        for audit in audit_queue:
            _record_audit(root, audit)
    return report


# --------------------------------------------------------------------------- CLI


def _render_human(report: dict[str, Any]) -> str:
    lines = [
        "claim-reaper: " + ("apply" if report["apply"] else "dry-run"),
        f"now={report['now']} grace_seconds={report['grace_seconds']}",
    ]
    authority = report.get("claim_store") or {}
    lines.append(
        "claim_store="
        + str(authority.get("state") or "integrity-invalid")
        + (
            f" finding={authority['finding']}"
            if authority.get("finding")
            else ""
        )
    )
    reaped = report["reaped"] if report["apply"] else report["would_reap"]
    verb = "reaped" if report["apply"] else "would-reap"
    outstanding = report.get("needs_owner_recovery") or []
    lines.append(
        f"{verb}={len(reaped)} live={len(report['live'])} "
        f"skipped={len(report['skipped'])} needs_owner_recovery={len(outstanding)}"
    )
    for entry in reaped:
        lines.append(f"  {verb}: {entry['claim_id']} task={entry['task_id']} ({entry['reason']})")
    for entry in report["skipped"]:
        lines.append(f"  skipped: {entry['claim_id']} ({entry['reason']})")
    for entry in outstanding:
        lines.append(
            f"  needs-owner-recovery: {entry['claim_id']} task={entry['task_id']}; "
            "lease is dead and this claim is never auto-reaped -- run: "
            "task_claim_dispatcher.py terminalize --claim-id "
            f"{entry['claim_id']} --owner-id <owner> --reason <why>"
        )
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
    try:
        report = sweep(
            args.root,
            now=args.now,
            apply=args.apply,
            grace_seconds=args.grace_seconds,
        )
    except ValueError as exc:
        print(_bounded_claim_store_finding(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_render_human(report))
    authority_state = str((report.get("claim_store") or {}).get("state") or "")
    if args.apply and authority_state not in {"initialized", "pristine"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
