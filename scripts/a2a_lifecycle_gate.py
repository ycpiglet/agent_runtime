from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_EVENT_TYPES = ("request", "review", "decision", "correction", "proposal_routing")
EVENT_ALIASES = {"proposal": "proposal_routing", "routing": "proposal_routing"}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _stable_suffix(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()


def load_events(path: Path) -> list[dict[str, Any]]:
    text = _read(path).strip()
    if not text:
        return []
    if text.startswith("["):
        payload = json.loads(text)
        return [item for item in payload if isinstance(item, dict)]
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _event_type(event: dict[str, Any]) -> str:
    raw = str(event.get("event_type") or event.get("type") or "").strip()
    return EVENT_ALIASES.get(raw, raw)


def _first_value(events: list[dict[str, Any]], key: str) -> str:
    for event in events:
        value = str(event.get(key) or "").strip()
        if value:
            return value
    return ""


def _evidence_record(
    *,
    root: Path,
    fixture: Path,
    status: str,
    context_id: str,
    task_id: str,
    findings: list[str],
) -> dict[str, Any]:
    signal = "pass" if status == "pass" else "block"
    observed_failure = "none" if status == "pass" else "; ".join(findings)
    return {
        "record_id": f"A2A-LIFECYCLE-{_stable_suffix([context_id, task_id, findings])}",
        "source_type": "A2A",
        "source_path": _rel(root, fixture),
        "task_ref": task_id or "none",
        "task_set_id": "TASKSET-AR-RSI-OPERATING-SYSTEM",
        "dedupe_key": f"a2a-lifecycle-{context_id or 'missing-context'}",
        "summary": "A2A request, review, decision, correction, and proposal routing lifecycle reconstruction.",
        "observed_failure": observed_failure,
        "observed_signal": status,
        "signal": signal,
        "candidate_action": "no_action" if status == "pass" else "task_proposal",
        "proposed_routing": "archive" if status == "pass" else "proposal",
        "owner_boundary": "local",
        "quality_check": "dedupe_key present; deterministic local fixture; full lifecycle reconstruction required before proposal use.",
        "context_id": context_id,
        "reconstruction_result": status,
    }


def run(root: Path = ROOT, *, fixture: Path | None = None, write_record: bool = False) -> dict[str, Any]:
    root = root.resolve()
    fixture = fixture or root / "agents" / "project" / "a2a" / "a2a-lifecycle-fixture-2026-06-11.jsonl"
    if not fixture.is_absolute():
        fixture = root / fixture
    events = load_events(fixture)
    event_types = {_event_type(event) for event in events}
    findings: list[str] = []

    if not events:
        findings.append("no lifecycle events found")
    for event_type in REQUIRED_EVENT_TYPES:
        if event_type not in event_types:
            findings.append(f"missing event_type: {event_type}")
    for index, event in enumerate(events, start=1):
        for field in ("context_id", "task_id", "actor_role", "access_boundary"):
            if not str(event.get(field) or "").strip():
                findings.append(f"event {index} missing field: {field}")
        if not (str(event.get("retry_id") or "").strip() or str(event.get("idempotency_key") or "").strip()):
            findings.append(f"event {index} missing retry/idempotency marker")
    routing_events = [event for event in events if _event_type(event) == "proposal_routing"]
    if routing_events and not str(routing_events[-1].get("reconstruction_result") or "").strip():
        findings.append("proposal_routing event missing reconstruction_result")

    status = "block" if findings else "pass"
    context_id = _first_value(events, "context_id")
    task_id = _first_value(events, "task_id")
    record = _evidence_record(
        root=root,
        fixture=fixture,
        status=status,
        context_id=context_id,
        task_id=task_id,
        findings=findings,
    )
    result: dict[str, Any] = {
        "status": status,
        "score": 100 if status == "pass" else 0,
        "fixture": _rel(root, fixture),
        "context_id": context_id,
        "task_id": task_id,
        "event_types": sorted(event_types),
        "findings": findings,
        "evidence_record": record,
    }
    if write_record:
        out = root / "agents" / "project" / "evidence" / "inbox" / f"{record['record_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["record_path"] = _rel(root, out)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a local A2A lifecycle fixture")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--write-record", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = run(args.root, fixture=args.fixture, write_record=args.write_record)
    if args.out:
        out = args.out if args.out.is_absolute() else args.root / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"a2a-lifecycle-gate: {payload['status']}")
        print(f"root={args.root.resolve()}")
        print(f"findings={len(payload['findings'])}")
        for finding in payload["findings"]:
            print(f"- {finding}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
