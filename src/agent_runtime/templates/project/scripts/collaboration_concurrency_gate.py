"""Validate real-time pane collaboration concurrency records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-pane-event/v1"
EVENT_LOG = "agents/runtime/pane_events/pane-events.jsonl"
ORCHESTRATOR_ACTORS = {"orchestrator", "release-orchestrator"}
ACTIVE_CLAIM_STATUSES = {"active", "assigned", "claimed", "in_progress", "review", "running", "waiting_review", "working"}
DONE_CLAIM_STATUSES = {"completed", "done", "released"}
CLAIM_LIFECYCLE_EVENTS = {
    "claim_created",
    "claim_heartbeat",
    "claim_released",
    "pane_started",
    "pane_heartbeat",
    "pane_handoff",
    "pane_closed",
    "started",
    "claimed",
    "heartbeat",
    "handoff",
    "released",
    "closed",
}
SSOT_PATHS = {
    "BACKLOG.md",
    "BACKLOG-BOARD.md",
    "STATUS.md",
    "owner-docs.yml",
    "agents/project/NEXT-SESSION-POINTER.yml",
    "agents/project/ROADMAP.md",
    "agents/project/STATE-MACHINES.yml",
}


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_events(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = root / EVENT_LOG
    if not path.exists():
        return [], []
    events: list[dict[str, Any]] = []
    findings: list[str] = []
    previous_seq = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        location = f"{_rel(root, path)}:{line_number}"
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(f"{location}: collab-concurrency:invalid-json: {exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"{location}: collab-concurrency:invalid-record: pane event must be an object")
            continue
        if payload.get("schema") != SCHEMA:
            findings.append(f"{location}: collab-concurrency:invalid-schema: expected {SCHEMA}")
        try:
            seq = int(payload.get("seq"))
        except (TypeError, ValueError):
            findings.append(f"{location}: collab-concurrency:invalid-seq: seq must be an integer")
            seq = previous_seq
        if seq <= previous_seq:
            findings.append(f"{location}: collab-concurrency:non-monotonic-seq: seq must increase")
        previous_seq = max(previous_seq, seq)
        events.append(payload)
    return events, findings


def _validate_events(root: Path, events: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for event in events:
        event_name = str(event.get("event") or "").strip()
        actor = str(event.get("actor") or "").strip().lower()
        ssot_path = str(event.get("ssot_path") or "").strip().replace("\\", "/")
        if event_name == "ssot_write_attempted" and ssot_path in SSOT_PATHS:
            if actor not in ORCHESTRATOR_ACTORS or event.get("orchestrator_approved") is not True:
                seq = event.get("seq", "?")
                findings.append(
                    f"{EVENT_LOG}: collab-concurrency:ssot-write-not-orchestrator:{seq}: "
                    f"{ssot_path} can only be written by an approved orchestrator event"
                )
    return findings


def _load_claims(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    if not claims_dir.is_dir():
        return [], []
    claims: list[dict[str, Any]] = []
    findings: list[str] = []
    for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{_rel(root, path)}: collab-concurrency:claim-invalid-json: {exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"{_rel(root, path)}: collab-concurrency:claim-invalid-record")
            continue
        payload["_path"] = _rel(root, path)
        claims.append(payload)
    return claims, findings


def _validate_claim_lifecycle(root: Path, claims: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    events_by_claim: dict[str, set[str]] = {}
    for event in events:
        claim_id = str(event.get("claim_id") or "").strip()
        event_name = str(event.get("event") or "").strip()
        if claim_id and event_name:
            events_by_claim.setdefault(claim_id, set()).add(event_name)
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "").strip()
        if not claim_id:
            continue
        status = str(claim.get("status") or "").strip().lower()
        lifecycle_events = events_by_claim.get(claim_id, set()) & CLAIM_LIFECYCLE_EVENTS
        if status in ACTIVE_CLAIM_STATUSES and not lifecycle_events:
            findings.append(
                f"{claim.get('_path', 'agents/runtime/task_claims')}: pane-event:missing-lifecycle:{claim_id}: "
                "active claim has no pane lifecycle event"
            )
        task_set_id = str(claim.get("task_set_id") or "").strip()
        if task_set_id == "TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE" and status in DONE_CLAIM_STATUSES and not (
            lifecycle_events & {"claim_released", "pane_handoff", "pane_closed", "handoff", "released", "closed"}
        ):
            findings.append(
                f"{claim.get('_path', 'agents/runtime/task_claims')}: pane-event:missing-release-lifecycle:{claim_id}: "
                "released claim has no handoff/release/close event"
            )
    return findings


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    events, findings = _load_events(root)
    claims, claim_findings = _load_claims(root)
    findings.extend(claim_findings)
    findings.extend(_validate_events(root, events))
    findings.extend(_validate_claim_lifecycle(root, claims, events))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collaboration concurrency gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_root(args.root)
    status = "fail" if findings else "pass"
    print(f"collaboration-concurrency-gate: {status}")
    print(f"root={args.root.resolve()}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
