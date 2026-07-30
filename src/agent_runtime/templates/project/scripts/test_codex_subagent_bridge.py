"""Unit tests for the Codex session subagent bridge (TASK-135)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_messages as cm  # noqa: E402
import codex_subagent_bridge as bridge  # noqa: E402
import subagent_council as sc  # noqa: E402
import subagent_dispatch as sd  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_execution_receipts(tmp_path, monkeypatch):
    receipt_log = tmp_path / "execution-receipts.jsonl"
    monkeypatch.setattr(bridge.eval_harness, "EVAL_LOG", receipt_log)
    return receipt_log


def test_dispatch_packet_writes_packet_call_and_event(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    packet = bridge.create_dispatch_packet(
        role_id="reviewer",
        task_id="TASK-135",
        intent="review Codex bridge",
        emit_call=True,
    )
    path = bridge.BRIDGE_DIR / f"{packet['id']}.json"
    assert path.exists()
    assert packet["schema_version"] == 2
    assert packet["runtime"] == "codex-session"
    assert packet["execution"]["capability"] == "native_subagent_spawn"
    assert packet["execution"]["tool_hint"] == "collaboration.spawn_agent"
    assert packet["execution"]["pre_spawn_guard"]["required"] is True
    assert bridge.authorize_dispatch(bridge_id=packet["id"])["authorized"] is True
    assert packet["execution"]["spawn_args"]["model"] == "gpt-5.6-sol"
    assert packet["execution"]["spawn_args"]["reasoning_effort"] == "high"
    assert packet["execution"]["spawn_args"]["message"] == packet["prompt"]
    assert packet["routing"]["requested_tier"] == "reviewer_standard"
    assert packet["routing"]["application_status"] == "configured_unverified"
    assert "REVIEWER subagent" in packet["prompt"]
    call = tmp_path / packet["call_message"]
    meta, err = cm.load_frontmatter(call)
    assert err == "" and meta is not None
    assert meta["type"] == "subagent_call"
    assert meta["to"] == "subagent-reviewer"
    assert meta["provider"] == "native-codex"
    assert meta["requested_model_tier"] == "reviewer_standard"
    assert meta["selected_model_tier"] == "reviewer_standard"
    assert meta["resolved_model"] == "gpt-5.6-sol"


def test_record_reply_writes_reply_and_marks_call_answered(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    packet = bridge.create_dispatch_packet(
        role_id="auditor",
        task_id="TASK-135",
        intent="audit",
        emit_call=True,
    )
    result = bridge.record_reply(
        bridge_id=packet["id"],
        verdict="APPROVED",
        summary="no issues",
    )
    reply = tmp_path / result["reply_message"]
    meta, err = cm.load_frontmatter(reply)
    assert err == "" and meta is not None
    assert meta["type"] == "subagent_reply"
    assert meta["in_reply_to"] == Path(packet["call_message"]).stem
    call_text = (tmp_path / packet["call_message"]).read_text(encoding="utf-8")
    assert "status: answered" in call_text
    assert result["completion_observation"]["observed_model"] is None
    assert result["completion_observation"]["model_observation_status"] == "unverified"
    assert result["completion_observation"]["token_usage_status"] == "unavailable"
    assert result["completion_observation"]["billed_cost_status"] == "unavailable"
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["source"] == "native_codex_reply"
    assert result["execution_receipt"]["receipt_id"] == receipts[0]["receipt_id"]


def test_implementer_packet_defaults_to_terra_low(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-646",
        intent="implement one bounded file change",
        dry_run=True,
    )
    assert packet["routing"]["requested_tier"] == "worker_low"
    assert packet["routing"]["selected_tier"] == "worker_low"
    assert packet["execution"]["spawn_args"]["model"] == "gpt-5.6-terra"
    assert packet["execution"]["spawn_args"]["reasoning_effort"] == "low"
    assert "resolved_request_model=gpt-5.6-terra" in packet["prompt"]
    assert "selected_pm_tier=worker_low" in packet["prompt"]
    assert "Agent tool model: sonnet" not in packet["prompt"]


def test_scribe_packet_uses_registered_low_cost_role_policy(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_dispatch_packet(
        role_id="scribe",
        task_id="TASK-SCRIBE",
        intent="archive bounded state",
        requested_tier="reviewer_high",
        dry_run=True,
    )
    assert packet["routing"]["role_policy_id"] == "scribe"
    assert packet["routing"]["selected_tier"] == "worker_low"
    assert packet["routing"]["routing_status"] == "high_tier_denied"
    assert packet["execution"]["spawn_args"]["model"] == "gpt-5.6-terra"


def test_lookup_dispatch_requires_preflight_and_completed_lookup_emits_no_spawn(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    with pytest.raises(ValueError, match="deterministic preflight"):
        bridge.create_dispatch_packet(
            role_id="explorer",
            task_id="TASK-646",
            intent="find and list routing files",
        )
    packet = bridge.create_dispatch_packet(
        role_id="explorer",
        task_id="TASK-646",
        intent="find and list routing files",
        preflight_status="completed_sufficient",
        preflight_evidence=["rg result recorded"],
    )
    assert packet["status"] == "deterministic_complete_no_spawn"
    assert packet["execution"] is None
    assert not (tmp_path / "packets").exists()
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 2
    assert {receipt["source"] for receipt in receipts} == {
        "deterministic_preflight_blocked",
        "deterministic_preflight_complete",
    }
    assert all(receipt["status"] == "skipped" for receipt in receipts)


def test_record_reply_records_only_explicit_completion_observations(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-646",
        intent="implement bounded change",
        emit_call=True,
    )
    result = bridge.record_reply(
        bridge_id=packet["id"],
        verdict="APPROVED",
        summary="done",
        observed_provider="codex",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
        tokens_in=120,
        tokens_out=30,
        latency_ms=250.5,
        billed_cost=0.012,
        currency="usd",
    )
    observation = result["completion_observation"]
    assert observation == {
        "observed_provider": "codex",
        "observed_model": "gpt-5.6-terra",
        "observed_reasoning_effort": "low",
        "model_observation_status": "observed",
        "token_usage_status": "observed",
        "tokens_in": 120,
        "tokens_out": 30,
        "latency_status": "observed",
        "latency_ms": 250.5,
        "billed_cost_status": "observed",
        "billed_cost": 0.012,
        "currency": "USD",
    }
    lines = next((tmp_path / "events").glob("*.jsonl")).read_text(
        encoding="utf-8"
    ).splitlines()
    completion = json.loads(lines[-1])
    assert completion["dispatch_id"] == packet["id"]
    assert completion["observed_model"] == "gpt-5.6-terra"
    assert completion["application_status"] == "applied"
    assert completion["tokens_in"] == 120
    saved = json.loads(
        (bridge.BRIDGE_DIR / f"{packet['id']}.json").read_text(encoding="utf-8")
    )
    assert saved["completion_observation"]["billed_cost"] == 0.012
    receipt = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)[0]
    assert receipt["observed_reasoning_effort"] == "low"
    assert receipt["tokens"] == 150
    assert receipt["billed_cost"] == 0.012
    assert receipt["finish_reason"] is None
    assert receipt["application_status"] == "unverified"
    assert receipt["route_status"] == "unverified"


@pytest.mark.parametrize(
    (
        "status",
        "error",
        "finish_reason",
        "application_status",
        "route_status",
        "eligible_records",
    ),
    [
        (
            "completed",
            None,
            "stop",
            "applied",
            "effective",
            1,
        ),
        (
            "completed",
            None,
            "completed",
            "applied",
            "effective",
            1,
        ),
        (
            "completed",
            None,
            "end_turn",
            "applied",
            "effective",
            1,
        ),
        (
            "completed",
            None,
            "stop_sequence",
            "applied",
            "effective",
            1,
        ),
        (
            "completed",
            None,
            "success",
            "applied",
            "effective",
            1,
        ),
        (
            "completed",
            None,
            "",
            "unverified",
            "unverified",
            0,
        ),
        (
            "error",
            "synthetic provider failure",
            "error",
            "unverified",
            "unverified",
            0,
        ),
        (
            "skipped",
            None,
            "skipped",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            "synthetic provider failure",
            "stop",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            None,
            "incomplete",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            None,
            "in_progress",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            None,
            "queued",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            None,
            "requires_action",
            "unverified",
            "unverified",
            0,
        ),
        (
            "completed",
            None,
            "unknown_terminal",
            "unverified",
            "unverified",
            0,
        ),
    ],
    ids=(
        "completed",
        "completed-finish",
        "end-turn-finish",
        "stop-sequence-finish",
        "success-finish",
        "explicit-empty-finish",
        "error",
        "skipped",
        "completed-with-error",
        "incomplete-finish",
        "in-progress-finish",
        "queued-finish",
        "requires-action-finish",
        "unknown-finish",
    ),
)
def test_record_reply_execution_status_gates_economic_evidence(
    tmp_path,
    monkeypatch,
    status,
    error,
    finish_reason,
    application_status,
    route_status,
    eligible_records,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    path = bridge.eval_harness.EVAL_LOG
    workload_id = f"workload-{status}-{bool(error)}"
    baseline = bridge.eval_harness.record_execution_receipt(
        dispatch_id=f"baseline-{status}-{bool(error)}",
        task_id="TASK-TERMINAL-INTEGRITY",
        workload_id=workload_id,
        provider="native-codex",
        resolved_model="gpt-5.6-sol",
        resolved_reasoning_effort="high",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        observed_reasoning_effort="high",
        tokens_in=80,
        tokens_out=20,
        billed_cost=0.10,
        currency="USD",
        source="native_codex_reply",
        status="completed",
        finish_reason="stop",
        path=path,
    )
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-TERMINAL-INTEGRITY",
        intent="implement bounded change",
        workload_id=workload_id,
        baseline_receipt_id=baseline["receipt_id"],
        receipt_log_path=path,
    )

    result = bridge.record_reply(
        bridge_id=packet["id"],
        verdict="APPROVED",
        summary="synthetic terminal result",
        observed_provider="native-codex",
        observed_model=packet["routing"]["resolved_model"],
        observed_reasoning_effort=packet["routing"]["reasoning_effort"],
        tokens_in=10,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        status=status,
        finish_reason=finish_reason,
        error=error,
        receipt_log_path=path,
    )

    receipts = bridge.eval_harness.read_outcomes(path)
    actual = next(
        receipt
        for receipt in receipts
        if receipt["receipt_id"] == result["execution_receipt"]["receipt_id"]
    )
    report = bridge.eval_harness.report(receipts)
    assert actual["baseline_reference_status"] == "verified"
    assert actual["application_status"] == application_status
    assert actual["route_status"] == route_status
    assert report["token_delta"]["eligible_records"] == eligible_records
    assert report["monetary_delta"]["eligible_records"] == eligible_records
    if eligible_records:
        assert report["token_delta"]["saved_tokens"] == 85
        assert report["monetary_delta"]["by_currency"]["USD"][
            "saved_billed_cost"
        ] == 0.08
    else:
        assert report["token_delta"]["saved_tokens"] == 0
        assert (
            report["token_delta"]["exclusion_reasons"][
                "actual_execution_not_successful"
            ]
            == 1
        )


def test_record_reply_without_bus_call_still_settles_receipt(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-NO-BUS",
        intent="implement bounded change",
    )

    result = bridge.record_reply(
        bridge_id=packet["id"],
        verdict="APPROVED",
        summary="done",
    )

    assert result["reply_message"] is None
    assert result["reply_event"] is None
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["dispatch_id"] == packet["id"]


def test_record_reply_rejects_cost_without_currency(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    packet = bridge.create_dispatch_packet(
        role_id="auditor",
        task_id="TASK-646",
        intent="audit",
        emit_call=True,
    )
    with pytest.raises(ValueError, match="currency"):
        bridge.record_reply(
            bridge_id=packet["id"],
            verdict="APPROVED",
            summary="ok",
            billed_cost=0.01,
        )


def test_council_packet_and_record(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(sc, "MESSAGES_INBOX", tmp_path / "inbox")
    packet = bridge.create_council_packet(
        task_id="TASK-135",
        members=["reviewer", "skeptic"],
        intent="judge bridge",
        emit_calls=True,
    )
    assert set(packet["prompts"]) == {"reviewer", "skeptic"}
    assert len(packet["call_messages"]) == 2
    assert (
        packet["member_execution"]["reviewer"]["spawn_args"]["model"]
        == "gpt-5.6-sol"
    )
    assert (
        packet["execution"]["pre_spawn_guard_by_member"]["reviewer"]["required"]
        is True
    )
    authorization = bridge.authorize_dispatch(
        bridge_id=packet["id"],
        role_id="reviewer",
    )
    assert authorization["authorized"] is True
    marker = authorization["checks"]["reviewer"]["provider_call_start"]
    assert marker["schema"] == bridge.eval_harness.PROVIDER_CALL_START_SCHEMA
    assert marker["reservation_source"] == "codex_subagent_council"
    assert marker["source"] == "native_codex_authorize"
    result = bridge.record_council(
        bridge_id=packet["id"],
        task_id=None,
        method=None,
        verdicts=[
            sc.Verdict("reviewer", "approve", "ok"),
            sc.Verdict("skeptic", "approve", "ok"),
        ],
        observations={
            "reviewer": {
                "provider": "codex",
                "model": "gpt-5.6-sol",
                "reasoning_effort": "high",
                "tokens_in": 10,
                "tokens_out": 5,
                "latency_ms": 100,
            }
        },
    )
    assert result["final"] == "approved"
    assert len(result["parent_calls_marked_answered"]) == 2
    assert (
        result["member_observations"]["reviewer"]["token_usage_status"]
        == "observed"
    )
    assert (
        result["member_observations"]["skeptic"]["token_usage_status"]
        == "unavailable"
    )
    assert (
        result["member_routing_completion"]["reviewer"]["application_status"]
        == "applied"
    )
    assert set(result["execution_receipts"]) == {"reviewer", "skeptic"}
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 2
    assert {receipt["role"] for receipt in receipts} == {"reviewer", "skeptic"}
    verdict_event = json.loads(
        next((tmp_path / "events").glob("*.jsonl")).read_text(
            encoding="utf-8"
        ).splitlines()[-1]
    )
    assert verdict_event["requested_tier"] == "per_member"
    assert set(verdict_event["member_routing"]) == {"reviewer", "skeptic"}
    for call in packet["call_messages"]:
        call_text = (tmp_path / call["call_message"]).read_text(encoding="utf-8")
        assert "status: answered" in call_text
    consensus = tmp_path / result["consensus_message"]
    meta, err = cm.load_frontmatter(consensus)
    assert err == "" and meta is not None
    assert meta["type"] == "consensus"


def test_dispatch_budget_block_emits_no_spawn_packet_and_records_receipt(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-BUDGET",
        intent="implement bounded change",
        dispatch_ceiling=10,
        task_token_budget=0,
    )

    assert packet["status"] == "budget_blocked_no_spawn"
    assert packet["execution"] is None
    assert packet["budget_preflight"]["reason"] == "task_budget_insufficient"
    assert not (tmp_path / "packets").exists()
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["status"] == "skipped"
    assert receipts[0]["source"] == "budget_preflight"


def test_council_reserves_each_member_and_zero_budget_emits_no_spawn(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-COUNCIL.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-COUNCIL",
                "task_id": "TASK-COUNCIL-BUDGET",
                "status": "claimed",
                "task_token_budget": 0,
                "claim_token_budget": None,
            }
        ),
        encoding="utf-8",
    )
    packet = bridge.create_council_packet(
        task_id="TASK-COUNCIL-BUDGET",
        members=["reviewer", "skeptic"],
        intent="review budget boundary",
        claim_id="CLAIM-COUNCIL",
        dispatch_ceiling=10,
        task_token_budget=0,
    )

    assert packet["status"] == "budget_blocked_no_spawn"
    assert packet["execution"] is None
    assert set(packet["member_budget_preflights"]) == {"reviewer", "skeptic"}
    assert all(
        result["reason"] == "task_budget_insufficient"
        for result in packet["member_budget_preflights"].values()
    )
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(receipts) == 2
    assert {receipt["role"] for receipt in receipts} == {
        "reviewer",
        "skeptic",
    }
    assert all(receipt["status"] == "skipped" for receipt in receipts)


def test_council_aggregate_budget_denial_leaves_no_partial_reservation(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-COUNCIL-AGGREGATE.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-COUNCIL-AGGREGATE",
                "task_id": "TASK-COUNCIL-AGGREGATE",
                "status": "claimed",
                "task_token_budget": 15,
                "claim_token_budget": None,
            }
        ),
        encoding="utf-8",
    )

    packet = bridge.create_council_packet(
        task_id="TASK-COUNCIL-AGGREGATE",
        members=["reviewer", "skeptic"],
        intent="review aggregate budget boundary",
        claim_id="CLAIM-COUNCIL-AGGREGATE",
        dispatch_ceiling=10,
    )

    assert packet["status"] == "budget_blocked_no_spawn"
    assert packet["execution"] is None
    preflights = packet["member_budget_preflights"]
    assert preflights["reviewer"]["batch_reason"] == "batch_budget_denied"
    assert preflights["skeptic"]["reason"] == "task_budget_insufficient"
    records = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert len(records) == 2
    assert all(
        record["schema"] != bridge.eval_harness.BUDGET_RESERVATION_SCHEMA
        for record in records
    )
    assert all(record["status"] == "skipped" for record in records)


def test_council_all_member_errors_close_receipts_without_verdicts(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    monkeypatch.setattr(sc, "MESSAGES_INBOX", tmp_path / "inbox")
    packet = bridge.create_council_packet(
        task_id="TASK-COUNCIL-ERROR",
        members=["reviewer", "skeptic"],
        intent="review bounded failure",
    )

    result = bridge.record_council(
        bridge_id=packet["id"],
        task_id=None,
        method=None,
        verdicts=[],
        observations={
            "reviewer": {"status": "error", "error": "spawn failed"},
            "skeptic": {"status": "error", "error": "spawn failed"},
        },
    )

    assert result["final"] == "incomplete"
    receipts = bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)
    assert {receipt["status"] for receipt in receipts} == {"error"}
    assert {receipt["role"] for receipt in receipts} == {
        "reviewer",
        "skeptic",
    }
    assert "--observation" in packet["execution"]["after_completion"]


def test_record_reply_rejects_duplicate_before_second_reply(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-ONCE",
        intent="implement once",
        emit_call=True,
    )
    bridge.record_reply(
        bridge_id=packet["id"],
        verdict="APPROVED",
        summary="done",
    )
    reply_count = len(list((tmp_path / "inbox").glob("*.md")))

    with pytest.raises(bridge.eval_harness.ReceiptConflictError):
        bridge.record_reply(
            bridge_id=packet["id"],
            verdict="APPROVED",
            summary="duplicate",
        )

    assert len(list((tmp_path / "inbox").glob("*.md"))) == reply_count
    assert len(bridge.eval_harness.read_outcomes(bridge.eval_harness.EVAL_LOG)) == 1


def test_pre_spawn_authorization_records_idempotent_provider_call_start(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-AUTHORIZE-MARKER",
        intent="implement bounded change",
        dispatch_ceiling=10,
        task_token_budget=10,
    )

    first = bridge.authorize_dispatch(bridge_id=packet["id"])
    second = bridge.authorize_dispatch(bridge_id=packet["id"])

    assert first["authorized"] is True
    assert second["authorized"] is True
    assert first["provider_call_start"]["schema"] == (
        bridge.eval_harness.PROVIDER_CALL_START_SCHEMA
    )
    assert (
        second["provider_call_start"]["call_start_id"]
        == first["provider_call_start"]["call_start_id"]
    )
    raw = [
        json.loads(line)
        for line in bridge.eval_harness.EVAL_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        bridge.eval_harness.BUDGET_RESERVATION_SCHEMA,
        bridge.eval_harness.PROVIDER_CALL_START_SCHEMA,
    ]
    marker = raw[-1]
    assert marker["source"] == "native_codex_authorize"
    assert marker["provider"] == "native-codex"
    assert marker["execution_surface"] == "native_subagent_spawn"
    assert bridge.eval_harness.read_outcomes(
        bridge.eval_harness.EVAL_LOG
    ) == []


def test_council_bulk_authorization_is_atomic_before_call_start(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    packet = bridge.create_council_packet(
        task_id="TASK-COUNCIL-AUTH-ATOMIC",
        members=["reviewer", "skeptic"],
        intent="review bounded change",
        dispatch_ceiling=10,
        task_token_budget=20,
    )
    bridge.eval_harness.record_execution_receipt(
        dispatch_id=f"{packet['id']}:skeptic",
        task_id="TASK-COUNCIL-AUTH-ATOMIC",
        role="skeptic",
        provider="native-codex",
        execution_surface="native_subagent_spawn",
        source="native_codex_council_reply",
        status="skipped",
        finish_reason="skipped",
        error="synthetic pre-spawn cancellation",
        path=bridge.eval_harness.EVAL_LOG,
    )

    authorization = bridge.authorize_dispatch(bridge_id=packet["id"])

    assert authorization["authorized"] is False
    assert authorization["checks"]["reviewer"]["authorized"] is True
    assert authorization["checks"]["skeptic"]["authorized"] is False
    assert "provider_call_start" not in authorization["checks"]["reviewer"]
    raw = [
        json.loads(line)
        for line in bridge.eval_harness.EVAL_LOG.read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert not any(
        row.get("schema")
        == bridge.eval_harness.PROVIDER_CALL_START_SCHEMA
        for row in raw
    )


def test_skipped_observed_zero_reply_without_authorize_keeps_budget_reserved(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-NO-SPAWN.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-NO-SPAWN",
                "task_id": "TASK-NO-SPAWN",
                "status": "claimed",
                "task_token_budget": 10,
                "claim_token_budget": 10,
            }
        ),
        encoding="utf-8",
    )
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-NO-SPAWN",
        intent="implement bounded change",
        claim_id="CLAIM-NO-SPAWN",
        dispatch_ceiling=10,
    )

    result = bridge.record_reply(
        bridge_id=packet["id"],
        verdict="INCOMPLETE",
        summary="spawn did not occur",
        tokens_in=0,
        tokens_out=0,
        status="skipped",
        finish_reason="skipped",
        error="synthetic spawn did not occur",
    )

    receipt = bridge.eval_harness.read_outcomes(
        bridge.eval_harness.EVAL_LOG
    )[0]
    assert receipt["receipt_id"] == result["execution_receipt"]["receipt_id"]
    assert receipt["budget_settlement_basis"] == "conservative_ceiling"
    usage = bridge.eval_harness.cumulative_usage(
        path=bridge.eval_harness.EVAL_LOG,
        task_id="TASK-NO-SPAWN",
        claim_id="CLAIM-NO-SPAWN",
    )
    assert usage["task"]["committed_tokens"] == 10
    assert usage["claim"]["committed_tokens"] == 10
    second = bridge.eval_harness.budget_preflight(
        path=bridge.eval_harness.EVAL_LOG,
        root=tmp_path,
        task_id="TASK-NO-SPAWN",
        claim_id="CLAIM-NO-SPAWN",
        dispatch_id="dispatch-second",
        dispatch_ceiling=1,
    )
    assert second["allowed"] is False


def test_pre_spawn_authorization_blocks_released_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    claim_path = claim_dir / "CLAIM-AUTHORIZE.json"
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-AUTHORIZE",
        "task_id": "TASK-AUTHORIZE",
        "status": "claimed",
        "task_token_budget": 100,
        "claim_token_budget": 100,
    }
    claim_path.write_text(json.dumps(claim), encoding="utf-8")
    packet = bridge.create_dispatch_packet(
        role_id="implementer",
        task_id="TASK-AUTHORIZE",
        intent="implement bounded change",
        claim_id="CLAIM-AUTHORIZE",
        dispatch_ceiling=10,
    )
    assert bridge.authorize_dispatch(
        bridge_id=packet["id"]
    )["authorized"] is True

    claim["status"] = "released"
    claim_path.write_text(json.dumps(claim), encoding="utf-8")
    with pytest.raises(
        bridge.eval_harness.ReceiptIntegrityError,
        match="not active",
    ):
        bridge.authorize_dispatch(bridge_id=packet["id"])


def test_cli_dispatch_dry_run_json(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, "BRIDGE_DIR", tmp_path / "packets")
    rc = bridge.main([
        "dispatch",
        "--role",
        "implementer",
        "--task-id",
        "TASK-135",
        "--intent",
        "implement",
        "--dry-run",
        "--json",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"runtime": "codex-session"' in out
    assert not (tmp_path / "packets").exists()
