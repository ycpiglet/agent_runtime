"""Taskset boundary execution guard — stop after a taskset completes.

Owner observation: after a dispatched taskset finishes, work sometimes drifts
into out-of-scope / unregistered follow-on tasks instead of stopping and
reporting. This gate enforces the boundary as a runtime policy.

How it works (lazy / OFF by default):

  - A claim records its active taskset scope in the ``active_scope`` field
    (written by ``taskset_dispatcher.py`` → ``task_claim_dispatcher.py``).
  - When that taskset completes, the worker releases the claim with
    ``phase == taskset-completed`` and a ``taskset.completed`` event is
    emitted; from that point the active scope is CLOSED.
  - This gate BLOCKS only when a NEW active claim has been opened whose
    ``task_set_id`` differs from a just-completed scope AND the new claim
    was created after the completion, without an owner scope-transition
    approval. That is the "drifted into out-of-scope work after completion"
    state the Owner wants stopped.

The gate is a strict no-op when no claim has recorded a completed
``active_scope`` (the common case, including a clean repo), so it never
blocks existing flows or the stop-hook approve path.

Escape / transition path (consistent with other repo gates):
  - ``--allow-scope-transition`` downgrades blocks to one-line ``watch``
    findings (a loud transitional escape, printed to stderr).
  - A new claim that carries ``scope_transition_approved: true`` (recorded by
    the owner-approval flow) is treated as an approved transition and does
    not block.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CLAIMS_REL = "agents/runtime/task_claims"
PANE_EVENTS_REL = "agents/runtime/pane_events/pane-events.jsonl"

ACTIVE_CLAIM_STATUSES = {
    "active",
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "waiting_review",
    "working",
}
DONE_CLAIM_STATUSES = {"completed", "done", "released"}
COMPLETED_PHASE = "taskset-completed"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _claims_dir(root: Path) -> Path:
    return root / CLAIMS_REL


def _load_claims(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    base = _claims_dir(root)
    records: list[tuple[Path, dict[str, Any]]] = []
    if not base.is_dir():
        return records
    for path in sorted(base.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            records.append((path, payload))
    return records


def _status(payload: dict[str, Any]) -> str:
    return str(payload.get("status") or "").strip().lower()


def _phase(payload: dict[str, Any]) -> str:
    return str(payload.get("phase") or "").strip().lower()


def _active_scope(payload: dict[str, Any]) -> str:
    return str(payload.get("active_scope") or "").strip()


def _task_set_id(payload: dict[str, Any]) -> str:
    return str(payload.get("task_set_id") or "").strip()


def _claimed_at(payload: dict[str, Any]) -> str:
    return str(payload.get("claimed_at") or "").strip()


def _approved_transition(payload: dict[str, Any]) -> bool:
    value = payload.get("scope_transition_approved")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def _completed_scopes(records: list[tuple[Path, dict[str, Any]]]) -> dict[str, str]:
    """Map a completed taskset scope -> the completion timestamp.

    A scope is "completed" when a released claim recorded an ``active_scope``
    and reached ``phase == taskset-completed``. The latest completion wins.
    """
    completed: dict[str, str] = {}
    for _, payload in records:
        scope = _active_scope(payload)
        if not scope:
            continue
        if _status(payload) in DONE_CLAIM_STATUSES and _phase(payload) == COMPLETED_PHASE:
            ts = str(payload.get("released_at") or payload.get("updated_at") or "").strip()
            if scope not in completed or ts > completed[scope]:
                completed[scope] = ts
    return completed


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    records = _load_claims(root)
    completed = _completed_scopes(records)
    if not completed:
        # No taskset has closed its scope: the guard is OFF. This keeps the
        # gate a no-op for the common / clean-repo case.
        return []

    findings: list[str] = []
    for path, payload in records:
        if _status(payload) not in ACTIVE_CLAIM_STATUSES:
            continue
        claim_scope = _task_set_id(payload)
        claim_id = str(payload.get("claim_id") or _rel(root, path))
        for scope, completed_ts in sorted(completed.items()):
            if claim_scope == scope:
                # Same-scope follow-on (e.g. a remaining task in the set) is
                # in-scope and never blocked by the boundary guard.
                continue
            new_at = _claimed_at(payload)
            if completed_ts and new_at and new_at < completed_ts:
                # Pre-existing parallel work, not post-completion drift.
                continue
            if _approved_transition(payload):
                continue
            findings.append(
                f"{_rel(root, path)}: taskset:boundary-violation:"
                f"completed-scope={scope}:new-out-of-scope-claim={claim_id}:"
                f"task-set={claim_scope or 'unscoped'}"
            )
    return findings


def _finding_action() -> str:
    return (
        "action=taskset boundary reached. The dispatched taskset completed; STOP "
        "and report rather than starting out-of-scope follow-on work. Get an owner "
        "scope-transition approval (record scope_transition_approved on the new "
        "claim) before opening a claim in a different taskset. "
        "--allow-scope-transition is a loud transitional escape only."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Taskset boundary execution guard")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    parser.add_argument("--check", action="store_true", help="Return non-zero when findings exist")
    parser.add_argument(
        "--allow-scope-transition",
        action="store_true",
        help=(
            "Transitional escape: downgrade boundary violations to watch "
            "findings instead of blocking (prints a loud warning)"
        ),
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    blocking = findings and not args.allow_scope_transition
    status = "fail" if blocking else "pass"
    print(f"taskset-boundary-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        marker = "block" if blocking else "watch"
        print(f"- [{marker}] {finding}")
    if findings:
        if args.allow_scope_transition:
            print(
                "WARNING: --allow-scope-transition used: out-of-scope work after "
                "taskset completion is NOT blocked. This is a transitional escape; "
                "get owner approval for the scope change.",
                file=sys.stderr,
            )
        else:
            print(_finding_action(), file=sys.stderr)
    return 1 if (args.check and blocking) else 0


if __name__ == "__main__":
    raise SystemExit(main())
