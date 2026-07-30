"""Unit tests for subagent_dispatch (TASK-116).

Covers:
  - 7 standard roles registered
  - render_prompt includes role-specific system prompt + output contract
  - emit_call_message produces a frontmatter that passes check_messages.py
  - emit_reply_message links via in_reply_to and uses type=subagent_reply
  - emit_event appends valid JSON to subagent-YYYY-MM-DD.jsonl
  - get_default_subagents resolves roles.yml default_subagents field
  - CLI: --list-roles, --for-worker, --role + --emit-call dry-run
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import subagent_dispatch as sd  # noqa: E402
import check_messages as cm  # noqa: E402


def test_seven_roles_registered():
    assert set(sd.list_roles()) == {
        "scribe",
        "explorer",
        "implementer",
        "reviewer",
        "auditor",
        "strategist",
        "skeptic",
    }


def test_explorer_role_is_read_only():
    role = sd.get_role("explorer")
    assert "Read-only" in role.description
    assert "Do not edit files" in role.system_prompt


def test_get_role_unknown_raises():
    with pytest.raises(KeyError):
        sd.get_role("doesnotexist")


def test_render_prompt_includes_role_pieces():
    prompt = sd.render_prompt(
        role_id="reviewer",
        task_id="TASK-116",
        intent="review subagent_dispatch.py",
        context_packet_path="some/path.md",
    )
    assert "REVIEWER subagent" in prompt
    assert "VERDICT" in prompt  # reviewer's output contract
    assert "TASK-116" in prompt
    assert "some/path.md" in prompt


def test_render_prompt_includes_auto_model_routing():
    prompt = sd.render_prompt(
        role_id="reviewer",
        task_id="TASK-239",
        intent="find and list the routing integration points",
        grade="Medium",
        model="auto",
    )
    assert "provider=native-codex" in prompt
    assert "requested_pm_tier=reviewer_standard" in prompt
    assert "selected_pm_tier=reviewer_standard" in prompt
    assert "resolved_request_model=gpt-5.6-sol" in prompt
    assert "reasoning_effort=high" in prompt
    assert "Agent tool model:" not in prompt


def test_render_prompt_defaults_to_auto_model_routing():
    prompt = sd.render_prompt(
        role_id="reviewer",
        task_id="TASK-239",
        intent="review routing integration",
        grade="High",
    )
    assert "## Model routing" in prompt
    assert "provider=native-codex" in prompt
    assert "selected_pm_tier=reviewer_standard" in prompt
    assert "resolved_request_model=gpt-5.6-sol" in prompt


def test_render_prompt_uses_provider_aware_route_without_legacy_tier_conflict():
    tier = sd.model_routing.resolve_subagent_tier("implementer")
    route = sd.model_routing.resolve_provider_route(
        "native-codex",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    prompt = sd.render_prompt(
        role_id="implementer",
        task_id="TASK-646",
        intent="implement one bounded change",
        tier_route=tier,
        provider_route=route,
    )
    assert "requested_pm_tier=worker_low" in prompt
    assert "selected_pm_tier=worker_low" in prompt
    assert "resolved_request_model=gpt-5.6-terra" in prompt
    assert "reasoning_effort=low" in prompt
    assert "Agent tool model: sonnet" not in prompt


def test_render_prompt_rejects_forged_high_route_assertions_for_scribe():
    forged_tier = sd.model_routing.resolve_subagent_tier("auditor")
    forged_provider = sd.model_routing.resolve_provider_route(
        "native-codex",
        "planner_high",
        requested_tier="planner_high",
    )

    with pytest.raises(ValueError, match="route assertion"):
        sd.render_prompt(
            role_id="scribe",
            task_id="TASK-652",
            intent="archive bounded state",
            tier_route=forged_tier,
            provider_route=forged_provider,
        )


def test_render_prompt_rejects_forged_raw_provider_route_assertion():
    tier = sd.model_routing.resolve_subagent_tier("scribe")
    forged_provider = sd.model_routing.resolve_provider_route(
        "native-codex",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    forged_provider["resolved_model"] = "vendor/raw-expensive-model"

    with pytest.raises(ValueError, match="route assertion"):
        sd.render_prompt(
            role_id="scribe",
            task_id="TASK-652",
            intent="archive bounded state",
            tier_route=tier,
            provider_route=forged_provider,
        )


def test_render_prompt_skeptic_has_severity():
    prompt = sd.render_prompt("skeptic", "TASK-116", "find holes")
    assert "SKEPTIC subagent" in prompt
    assert "severity" in prompt


def test_emit_call_message_dry_run_returns_path(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    path = sd.emit_call_message(
        role_id="reviewer",
        task_id="TASK-116",
        intent="review dispatch helper",
        dry_run=True,
    )
    assert path.parent == tmp_path
    assert not path.exists()  # dry_run does not write


def test_emit_call_message_writes_valid_frontmatter(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    path = sd.emit_call_message(
        role_id="auditor",
        task_id="TASK-116",
        intent="independent audit of TASK-116",
        evidence=["scripts/subagent_dispatch.py"],
        next_items=["check frontmatter", "verify event log"],
    )
    assert path.exists()
    meta, err = cm.load_frontmatter(path)
    assert err == "" and meta is not None, err
    for field in cm.REQUIRED_FIELDS:
        assert field in meta, f"missing {field}"
    assert meta["type"] == "subagent_call"
    assert meta["status"] == "open"
    assert meta["to"] == "subagent-auditor"
    assert meta["task_id"] == "TASK-116"
    assert meta["evidence"] == ["scripts/subagent_dispatch.py"]
    assert "check frontmatter" in meta["next"]


def test_emit_call_message_carries_dispatch_claim_budget_and_eval_authority(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    tier = sd.model_routing.resolve_subagent_tier(
        "scribe",
        escalation_triggers=["data_integrity"],
    )
    route = sd.model_routing.resolve_provider_route(
        "native-codex",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    path = sd.emit_call_message(
        role_id="scribe",
        task_id="TASK-652",
        intent="archive bounded state",
        dispatch_id="dispatch-standard-contract",
        claim_id="CLAIM-652",
        task_token_budget=1200,
        claim_token_budget=300,
        workload_id="WORKLOAD-652",
        baseline_receipt_id="receipt-baseline-652",
        tier_route=tier,
        provider_route=route,
        requested_tier="worker_low",
        escalation_triggers=["data_integrity"],
        provider="native-codex",
    )

    meta, err = cm.load_frontmatter(path)
    assert err == "" and meta is not None
    assert meta["dispatch_id"] == "dispatch-standard-contract"
    assert meta["claim_id"] == "CLAIM-652"
    assert meta["task_token_budget"] == "1200"
    assert meta["claim_token_budget"] == "300"
    assert meta["eval_workload_id"] == "WORKLOAD-652"
    assert meta["eval_baseline_receipt_id"] == "receipt-baseline-652"
    assert meta["escalation_triggers"] == ["data_integrity"]


def test_provider_aware_dispatch_records_role_policy_and_reasoning(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    tier = sd.model_routing.resolve_subagent_tier("explorer")
    route = sd.model_routing.resolve_provider_route(
        "native-codex",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    path = sd.emit_call_message(
        role_id="explorer",
        task_id="TASK-652",
        intent="inspect bounded files",
        tier_route=tier,
        provider_route=route,
    )

    meta, err = cm.load_frontmatter(path)
    assert err == "" and meta is not None
    assert meta["role_policy_id"] == "exploration"
    assert meta["role_policy_status"] == "explicit"
    assert meta["high_tier_authorized"] == "true"
    assert meta["reasoning_effort"] == "low"
    assert meta["reasoning_source"].startswith("adapter_default:")

    fields = sd.routing_event_fields(
        None,
        dispatch_id=path.stem,
        provider="native-codex",
        route={**tier, **route},
    )
    assert fields["role_policy_id"] == "exploration"
    assert fields["role_policy_status"] == "explicit"
    assert fields["reasoning_effort"] == "low"
    assert fields["reasoning_source"].startswith("adapter_default:")
    assert fields["route_changed"] is None


def test_emit_call_message_rejects_forged_high_route_assertions_for_scribe(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    forged_tier = sd.model_routing.resolve_subagent_tier("auditor")
    forged_provider = sd.model_routing.resolve_provider_route(
        "native-codex",
        "planner_high",
        requested_tier="planner_high",
    )

    with pytest.raises(ValueError, match="route assertion"):
        sd.emit_call_message(
            role_id="scribe",
            task_id="TASK-652",
            intent="archive bounded state",
            tier_route=forged_tier,
            provider_route=forged_provider,
        )
    assert not list(tmp_path.iterdir())


def test_emit_call_message_rejects_forged_raw_provider_route_assertion(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    tier = sd.model_routing.resolve_subagent_tier("scribe")
    forged_provider = sd.model_routing.resolve_provider_route(
        "native-codex",
        tier["selected_tier"],
        requested_tier=tier["requested_tier"],
    )
    forged_provider["resolved_model"] = "vendor/raw-expensive-model"

    with pytest.raises(ValueError, match="route assertion"):
        sd.emit_call_message(
            role_id="scribe",
            task_id="TASK-652",
            intent="archive bounded state",
            tier_route=tier,
            provider_route=forged_provider,
        )
    assert not list(tmp_path.iterdir())


def test_emit_reply_message_links_to_parent(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    parent = sd.emit_call_message(
        role_id="reviewer", task_id="TASK-116", intent="review"
    )
    parent_id = parent.stem
    reply = sd.emit_reply_message(
        parent_id=parent_id,
        role_id="reviewer",
        task_id="TASK-116",
        verdict="APPROVED",
        summary="no issues found",
    )
    meta, err = cm.load_frontmatter(reply)
    assert err == "" and meta is not None
    assert meta["type"] == "subagent_reply"
    assert meta["status"] == "answered"
    assert meta["in_reply_to"] == parent_id
    assert "APPROVED" in reply.read_text(encoding="utf-8")


def test_emit_event_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path)
    path = sd.emit_event(
        role_id="auditor",
        task_id="TASK-116",
        kind="dispatch",
        extra={"message_id": "MSG-20260526-220000-abcdef", "intent": "test"},
    )
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["kind"] == "dispatch"
    assert record["role"] == "auditor"
    assert record["task_id"] == "TASK-116"
    assert record["message_id"] == "MSG-20260526-220000-abcdef"


def test_emit_event_rejects_unknown_kind():
    with pytest.raises(ValueError):
        sd.emit_event(
            role_id="reviewer", task_id="TASK-116", kind="bogus", dry_run=True
        )


def test_get_default_subagents_qa_includes_reviewer():
    """qa worker's default_subagents must include reviewer per roles.yml."""
    defaults = sd.get_default_subagents("qa")
    assert "reviewer" in defaults


def test_get_default_subagents_unknown_role_returns_empty():
    assert sd.get_default_subagents("not-a-real-role") == []


def test_cli_list_roles(capsys):
    rc = sd.main(["--list-roles"])
    assert rc == 0
    out = capsys.readouterr().out
    for role in sd.list_roles():
        assert role in out


def test_cli_for_worker_qa(capsys):
    rc = sd.main(["--for-worker", "qa"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "reviewer" in out


def test_cli_dispatch_dry_run(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role",
            "implementer",
            "--task-id",
            "TASK-116",
            "--intent",
            "implement dispatch helper",
            "--emit-call",
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "IMPLEMENTER subagent" in out
    assert "provider=native-codex" in out
    assert "selected_pm_tier=worker_low" in out
    assert "resolved_request_model=gpt-5.6-terra" in out
    assert "would write" in out
    # dry-run must not create files
    assert not (tmp_path / "inbox").exists() or not any(
        (tmp_path / "inbox").iterdir()
    )


def test_cli_dispatch_dry_run_accepts_auto_model(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role", "reviewer",
            "--task-id", "TASK-239",
            "--intent", "investigate why routing failed",
            "--grade", "High",
            "--model", "auto",
            "--emit-call",
            "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "requested_pm_tier=reviewer_standard" in out
    assert "selected_pm_tier=reviewer_standard" in out
    assert "resolved_request_model=gpt-5.6-sol" in out
    assert "Agent tool model:" not in out


def test_cli_without_provider_denies_scribe_high_tier(
    capsys,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role", "scribe",
            "--task-id", "TASK-652",
            "--intent", "archive bounded state",
            "--model", "opus",
            "--emit-call",
            "--dry-run",
        ]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "requested_pm_tier=planner_high" in out
    assert "selected_pm_tier=worker_low" in out
    assert "resolved_request_model=gpt-5.6-terra" in out
    assert "resolved_request_model=opus" not in out


def test_cli_rejects_raw_model_name_before_dispatch():
    with pytest.raises(SystemExit):
        sd.main(
            [
                "--role", "scribe",
                "--task-id", "TASK-652",
                "--intent", "archive bounded state",
                "--model", "vendor/raw-expensive-model",
            ]
        )


def test_cli_blocks_lookup_dispatch_without_deterministic_preflight(
    capsys, tmp_path, monkeypatch
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role", "explorer",
            "--task-id", "TASK-646",
            "--intent", "find and list routing files",
            "--emit-call",
        ]
    )
    assert rc == 2
    assert "deterministic preflight" in capsys.readouterr().err
    assert not (tmp_path / "inbox").exists()


def test_cli_emits_lookup_after_insufficient_deterministic_evidence(
    capsys, tmp_path, monkeypatch
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role", "explorer",
            "--task-id", "TASK-646",
            "--intent", "find and list routing files",
            "--provider", "native-codex",
            "--preflight-status", "attempted_insufficient",
            "--preflight-evidence", "rg found only compatibility aliases",
            "--emit-call",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0, captured.err
    output = captured.out
    assert "selected_pm_tier=worker_low" in output
    assert "resolved_request_model=gpt-5.6-terra" in output
    record = json.loads(
        next((tmp_path / "events").glob("*.jsonl"))
        .read_text(encoding="utf-8")
        .strip()
    )
    assert record["provider"] == "native-codex"
    assert record["execution_surface"] == "native_subagent_spawn"
    assert record["requested_tier"] == "worker_low"
    assert record["selected_tier"] == "worker_low"
    assert record["resolved_model"] == "gpt-5.6-terra"
    assert record["deterministic_preflight"] == "attempted_insufficient"
    assert record["model_observation_status"] == "unverified"
    assert record["token_usage_status"] == "unavailable"
    assert record["billed_cost_status"] == "unavailable"


def test_cli_completed_deterministic_lookup_emits_no_call(
    capsys, tmp_path, monkeypatch
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    rc = sd.main(
        [
            "--role", "explorer",
            "--task-id", "TASK-646",
            "--intent", "find and list routing files",
            "--preflight-status", "completed_sufficient",
            "--emit-call",
        ]
    )
    assert rc == 0
    assert "no model call emitted" in capsys.readouterr().out
    assert not (tmp_path / "inbox").exists()


def test_emit_event_records_full_routing_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path)
    decision = sd.resolve_model_decision(
        "auto",
        grade="High",
        intent="investigate why routing failed",
    )
    path = sd.emit_event(
        role_id="reviewer",
        task_id="TASK-239",
        kind="dispatch",
        extra=sd.routing_event_fields(decision),
    )
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["routing_grade"] == "High"
    assert record["policy_model"] == "sonnet"
    assert record["selected_model"] == "opus"
    assert record["routing_signals"] == ["deep_reasoning"]
    assert record["routing_reason"]


def test_emit_call_message_role_bounds_legacy_routing_frontmatter(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path)
    decision = sd.resolve_model_decision(
        "auto",
        grade="Medium",
        intent="find and list routing files",
    )
    path = sd.emit_call_message(
        role_id="reviewer",
        task_id="TASK-239",
        intent="find and list routing files",
        routing=decision,
    )
    meta, err = cm.load_frontmatter(path)
    assert err == "" and meta is not None
    assert meta["provider"] == "native-codex"
    assert meta["requested_model_tier"] == "worker_low"
    assert meta["selected_model_tier"] == "worker_low"
    assert meta["resolved_model"] == "gpt-5.6-terra"
    assert meta["role_policy_id"] == "review"
    assert "routing_grade" not in meta


def test_cli_requires_role_task_intent(capsys):
    rc = sd.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "required" in err


# ---------- TASK-143: subagent cap tests (RETRO §5 / STAGE-7 §7) ----------


def test_counter_starts_at_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    assert sd.load_subagent_counter("TASK-999") == 0


def test_increment_counter_monotonic(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    assert sd.increment_subagent_counter("TASK-999") == 1
    assert sd.increment_subagent_counter("TASK-999") == 2
    assert sd.load_subagent_counter("TASK-999") == 2


def test_reset_counter(tmp_path, monkeypatch):
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    sd.increment_subagent_counter("TASK-999")
    sd.increment_subagent_counter("TASK-999")
    sd.reset_subagent_counter("TASK-999")
    assert sd.load_subagent_counter("TASK-999") == 0


def test_cap_zero_means_unlimited(tmp_path, monkeypatch, capsys):
    """--max-subagents-per-task 0 (default) bypasses the cap entirely."""
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    # 3 dispatches with default cap=0 — all should succeed
    for _ in range(3):
        rc = sd.main([
            "--role", "reviewer",
            "--task-id", "TASK-CAPTEST",
            "--intent", "test cap zero",
            "--emit-call",
            "--dry-run",
        ])
        assert rc == 0
    # counter shouldn't have been incremented (cap=0 skips counter)
    assert sd.load_subagent_counter("TASK-CAPTEST") == 0


def test_cap_blocks_after_threshold(tmp_path, monkeypatch, capsys):
    """cap=1 allows first dispatch (dry-run no increment), but with non-dry-run increments and blocks second."""
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    monkeypatch.setattr(sd, "MESSAGES_INBOX", tmp_path / "inbox")
    monkeypatch.setattr(sd, "EVENTS_DIR", tmp_path / "events")
    # First dispatch (non-dry-run) — counter becomes 1
    rc1 = sd.main([
        "--role", "reviewer",
        "--task-id", "TASK-CAPLIM",
        "--intent", "first dispatch",
        "--emit-call",
        "--max-subagents-per-task", "1",
    ])
    assert rc1 == 0
    assert sd.load_subagent_counter("TASK-CAPLIM") == 1
    # Second dispatch — counter already at cap, should block
    rc2 = sd.main([
        "--role", "reviewer",
        "--task-id", "TASK-CAPLIM",
        "--intent", "second dispatch",
        "--emit-call",
        "--max-subagents-per-task", "1",
    ])
    assert rc2 == 2
    err = capsys.readouterr().err
    assert "subagent cap reached" in err
    assert "TASK-CAPLIM" in err


def test_reset_counter_via_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sd, "SUBAGENT_COUNTER_DIR", tmp_path / "counter")
    sd.increment_subagent_counter("TASK-CAPRESET")
    assert sd.load_subagent_counter("TASK-CAPRESET") == 1
    rc = sd.main(["--reset-counter", "--task-id", "TASK-CAPRESET"])
    assert rc == 0
    assert sd.load_subagent_counter("TASK-CAPRESET") == 0
