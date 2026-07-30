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
