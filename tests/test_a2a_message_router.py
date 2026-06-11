from __future__ import annotations

import importlib.util
import json
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = REPO_ROOT / "scripts" / "a2a_message_router.py"
GATE_PATH = REPO_ROOT / "scripts" / "a2a_trace_gate.py"


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"module_{uuid.uuid4().hex}", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _emit_two_agent_chain(router, log_path: Path, *, broken_parent: bool = False) -> list[dict]:
    parent_event_id = ""
    rows: list[dict] = []
    steps = [
        ("request", "lead-engineer", "qa", "agents/lead_engineer/tasks/TASK-AR-311.md"),
        ("review", "qa", "lead-engineer", "reviews/TASK-AR-311-review.md"),
        ("decision", "lead-engineer", "qa", "reviews/TASK-AR-311-decision.md"),
        ("correction", "qa", "lead-engineer", "reviews/TASK-AR-311-correction.md"),
    ]
    for idx, (event_type, sender, receiver, payload_ref) in enumerate(steps, start=1):
        current_parent = parent_event_id
        if broken_parent and event_type == "decision":
            current_parent = "evt-wrong-parent"
        message = router.emit_message(
            log_path=log_path,
            context_id="ctx-task-ar-311",
            task_id="TASK-AR-311",
            decision_cycle_id="cycle-a2a-local-routing",
            event_type=event_type,
            sender=sender,
            receiver=receiver,
            payload_ref=payload_ref,
            event_id=f"evt-task-ar-311-{idx:03d}",
            parent_event_id=current_parent,
            idempotency_key=f"ctx-task-ar-311:TASK-AR-311:{event_type}:{idx}",
            timestamp=f"2026-06-11T14:0{idx}:00+00:00",
        )
        rows.append(message)
        parent_event_id = str(message["event_id"])
    return rows


def test_emit_message_records_explicit_runtime_route_and_context(tmp_path: Path) -> None:
    router = _load_module(ROUTER_PATH)
    log_path = tmp_path / "agents" / "runtime" / "a2a" / "messages.jsonl"

    rows = _emit_two_agent_chain(router, log_path)
    stored = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

    assert stored == rows
    assert stored[0]["schema_version"] == "agent-runtime-a2a-message/v1"
    assert stored[0]["contextId"] == "ctx-task-ar-311"
    assert stored[0]["taskId"] == "TASK-AR-311"
    assert stored[1]["parent_event_id"] == stored[0]["event_id"]
    assert stored[1]["route"] == {"from": "qa", "to": "lead-engineer"}
    assert stored[1]["task_context"]["decision_cycle_id"] == "cycle-a2a-local-routing"


def test_emit_message_rejects_duplicate_idempotency(tmp_path: Path) -> None:
    router = _load_module(ROUTER_PATH)
    log_path = tmp_path / "messages.jsonl"
    router.emit_message(
        log_path=log_path,
        context_id="ctx-task-ar-311",
        task_id="TASK-AR-311",
        decision_cycle_id="cycle-a2a-local-routing",
        event_type="request",
        sender="lead-engineer",
        receiver="qa",
        payload_ref="agents/lead_engineer/tasks/TASK-AR-311.md",
        event_id="evt-task-ar-311-001",
        idempotency_key="idem-task-ar-311-request",
        timestamp="2026-06-11T14:01:00+00:00",
    )

    with pytest.raises(router.A2AMessageError, match="duplicate idempotency_key"):
        router.emit_message(
            log_path=log_path,
            context_id="ctx-task-ar-311",
            task_id="TASK-AR-311",
            decision_cycle_id="cycle-a2a-local-routing",
            event_type="request",
            sender="lead-engineer",
            receiver="qa",
            payload_ref="agents/lead_engineer/tasks/TASK-AR-311.md",
            event_id="evt-task-ar-311-002",
            idempotency_key="idem-task-ar-311-request",
            timestamp="2026-06-11T14:01:30+00:00",
        )


def test_a2a_trace_gate_accepts_explicit_message_handoff_chain(tmp_path: Path) -> None:
    router = _load_module(ROUTER_PATH)
    gate = _load_module(GATE_PATH)
    log_path = tmp_path / "messages.jsonl"

    _emit_two_agent_chain(router, log_path)
    report = gate.evaluate(log_path)

    assert report["status"] == "pass"
    assert report["message_events"] == 4
    assert report["chains"] == 1
    assert report["chain_results"][0]["event_types"] == [
        "request",
        "review",
        "decision",
        "correction",
    ]


def test_a2a_trace_gate_blocks_broken_message_handoff_link(tmp_path: Path) -> None:
    router = _load_module(ROUTER_PATH)
    gate = _load_module(GATE_PATH)
    log_path = tmp_path / "messages.jsonl"

    _emit_two_agent_chain(router, log_path, broken_parent=True)
    report = gate.evaluate(log_path)

    assert report["status"] == "block"
    assert any("message-parent-link:decision" in finding for finding in report["findings"])
