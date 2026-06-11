from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "agents" / "project" / "evidence" / "a2a" / "A2A-LIFECYCLE-2026-06-12.json"
REQUIRED_EVENTS = ("request", "review", "decision", "correction", "proposal_routing")
REQUIRED_TOP_LEVEL = (
    "context_id",
    "task_id",
    "task_set_id",
    "owner_boundary",
    "retry_idempotency_key",
    "events",
    "reconstruction_result",
    "inbox_record",
)
REQUIRED_EVENT_FIELDS = ("event_id", "event_type", "actor_role", "access_boundary", "summary")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_record(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [f"{path}: read-error:{exc}"]
    except json.JSONDecodeError as exc:
        return None, [f"{path}: json-error:{exc}"]
    if not isinstance(payload, dict):
        return None, [f"{path}: payload-not-object"]
    return payload, []


def validate_record(payload: dict[str, Any], *, path: Path, root: Path) -> list[str]:
    findings: list[str] = []
    rel = _rel(root, path)
    for field in REQUIRED_TOP_LEVEL:
        if field not in payload:
            findings.append(f"{rel}: missing-field:{field}")

    events = payload.get("events")
    if not isinstance(events, list):
        findings.append(f"{rel}: events-not-list")
        return findings

    event_types: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            findings.append(f"{rel}: event-{index}:not-object")
            continue
        for field in REQUIRED_EVENT_FIELDS:
            if not str(event.get(field) or "").strip():
                findings.append(f"{rel}: event-{index}:missing-field:{field}")
        event_type = str(event.get("event_type") or "").strip()
        if event_type:
            event_types.add(event_type)

    for event_type in REQUIRED_EVENTS:
        if event_type not in event_types:
            findings.append(f"{rel}: missing-event:{event_type}")

    if str(payload.get("reconstruction_result") or "").strip() not in {"pass", "watch", "block"}:
        findings.append(f"{rel}: invalid-reconstruction-result")

    inbox = payload.get("inbox_record")
    if not isinstance(inbox, dict):
        findings.append(f"{rel}: inbox-record-not-object")
    else:
        for field in ("source_type", "source_path", "task_ref", "task_set_id", "dedupe_key", "quality_check"):
            if not str(inbox.get(field) or "").strip():
                findings.append(f"{rel}: inbox-record-missing:{field}")
        if str(inbox.get("source_type") or "").lower() != "a2a":
            findings.append(f"{rel}: inbox-record-source-type-not-a2a")

    return findings


def run(record: Path = DEFAULT_RECORD, *, root: Path = ROOT) -> dict[str, Any]:
    payload, findings = load_record(record)
    if payload is not None:
        findings.extend(validate_record(payload, path=record, root=root))
    status = "pass" if not findings else "block"
    return {
        "status": status,
        "score": 100 if status == "pass" else 0,
        "record": _rel(root, record),
        "required_events": list(REQUIRED_EVENTS),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic A2A lifecycle evidence")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    payload = run(args.record, root=args.root.resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"a2a-lifecycle-gate: {payload['status']}")
        print(f"record={payload['record']}")
        print(f"findings={len(payload['findings'])}")
        for finding in payload["findings"]:
            print(f"- {finding}")
    return 1 if args.check and payload["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

