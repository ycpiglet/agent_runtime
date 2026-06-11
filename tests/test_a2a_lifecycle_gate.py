from __future__ import annotations

import json
from pathlib import Path

from scripts import a2a_lifecycle_gate


def write_jsonl(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def valid_events() -> list[dict[str, object]]:
    base = {
        "context_id": "CTX-RSI-OS-001",
        "task_id": "TASK-AR-302",
        "access_boundary": "local",
        "idempotency_key": "CTX-RSI-OS-001",
    }
    return [
        {**base, "event_type": "request", "actor_role": "owner"},
        {**base, "event_type": "review", "actor_role": "evaluation-office"},
        {**base, "event_type": "decision", "actor_role": "lead-engineer"},
        {**base, "event_type": "correction", "actor_role": "qa"},
        {
            **base,
            "event_type": "proposal_routing",
            "actor_role": "planning-coordinator",
            "reconstruction_result": "pass",
        },
    ]


def test_a2a_lifecycle_gate_passes_and_writes_evidence_record(tmp_path: Path) -> None:
    fixture = tmp_path / "a2a.jsonl"
    write_jsonl(fixture, valid_events())

    result = a2a_lifecycle_gate.run(tmp_path, fixture=fixture, write_record=True)

    assert result["status"] == "pass"
    assert result["evidence_record"]["source_type"] == "A2A"
    record_path = tmp_path / result["record_path"]
    assert record_path.exists()
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["dedupe_key"] == "a2a-lifecycle-CTX-RSI-OS-001"
    assert record["proposed_routing"] == "archive"


def test_a2a_lifecycle_gate_blocks_missing_decision(tmp_path: Path) -> None:
    fixture = tmp_path / "a2a.jsonl"
    events = [event for event in valid_events() if event["event_type"] != "decision"]
    write_jsonl(fixture, events)

    result = a2a_lifecycle_gate.run(tmp_path, fixture=fixture)

    assert result["status"] == "block"
    assert any("missing event_type: decision" in finding for finding in result["findings"])
