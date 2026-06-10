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


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    events, findings = _load_events(root)
    findings.extend(_validate_events(root, events))
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
