"""TASK-238 — agentic 측정 substrate 테스트."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("_eh", ROOT / "scripts" / "eval_harness.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


eh = _load()


def _effective_delta_record(**overrides):
    rec = {
        "grade": "Low",
        "model": "claude-haiku-4-5",
        "tokens": 100,
        "baseline_tokens": 400,
        "actual_tokens_known": True,
        "observed_model": "claude-haiku-4-5",
        "baseline_model": "claude-opus-4-8",
        "model_changed": True,
        "route_status": "effective",
        "application_status": "applied",
        "finish_reason": "stop",
        "outcome": "ok",
    }
    rec.update(overrides)
    return rec


def _golden_records():
    committed = eh.load_golden()
    if committed:
        return committed
    # The source-template test is also run before a host is initialized, where
    # the host-local golden.jsonl does not exist yet. Keep that direct test
    # deterministic without changing the installed-host lookup contract.
    rows = [
        ("Low", "stop", "ok", "ok"),
        ("Low", "length", "ok", "ok"),
        ("Medium", "stop", "completed", "ok"),
        ("Medium", "length", "needs-changes", "escalate"),
        ("High", "error", "ok", "escalate"),
        ("High", "stop", "rejected", "escalate"),
        ("High", "stop", "ok", "ok"),
        ("Critical", "cap", "ok", "escalate"),
        ("Critical", "stop", "reopen", "escalate"),
        ("Critical", "stop", "ok", "ok"),
    ]
    return [
        {
            "task_id": f"G{index}",
            "grade": grade,
            "model": "sonnet",
            "tokens": 1,
            "finish_reason": finish,
            "outcome": outcome,
            "expected": expected,
        }
        for index, (grade, finish, outcome, expected) in enumerate(rows, start=1)
    ]


# ---- objective judge: golden set 회귀 가드 ----

def test_judge_matches_golden():
    golden = _golden_records()
    assert len(golden) >= 10
    for rec in golden:
        assert eh.judge_outcome(rec) == rec["expected"], f"{rec['task_id']} mismatch"


def test_judge_ok_and_escalate():
    assert eh.judge_outcome({"finish_reason": "stop", "outcome": "ok"}) == "ok"
    assert eh.judge_outcome({"finish_reason": "error", "outcome": "ok"}) == "escalate"
    assert eh.judge_outcome({"finish_reason": "stop", "outcome": "rejected"}) == "escalate"


def test_judge_length_is_ambiguous():
    # reviewer #1: 성공한 긴 출력(length+ok)은 escalate 아님, length+나쁜 outcome 만 escalate
    assert eh.judge_outcome({"finish_reason": "length", "outcome": "ok"}) == "ok"
    assert eh.judge_outcome({"finish_reason": "length", "outcome": "needs-changes"}) == "escalate"


def test_report_opus_by_grade_baseline():
    # reviewer #2: 등급별 opus 비율 — 라우팅 전 baseline(routing 이 줄여야 할 숫자)
    recs = [{"grade": "Low", "model": "opus-4-8", "tokens": 1, "finish_reason": "stop", "outcome": "ok"},
            {"grade": "Low", "model": "haiku-4-5", "tokens": 1, "finish_reason": "stop", "outcome": "ok"},
            {"grade": "Critical", "model": "opus-4-8", "tokens": 1, "finish_reason": "stop", "outcome": "ok"}]
    rep = eh.report(recs)
    assert rep["opus_by_grade"]["Low"]["opus_share"] == 0.5
    assert rep["opus_by_grade"]["Critical"]["opus_share"] == 1.0


# ---- logger round-trip ----

def test_record_and_read(tmp_path):
    p = tmp_path / "eval_log.jsonl"
    eh.record_outcome(
        "TASK-X",
        "High",
        "sonnet-4-6",
        40000,
        "stop",
        "ok",
        path=p,
        policy_model="sonnet",
        selected_model="sonnet",
        routing_signals=["grade_policy"],
        baseline_tokens=60000,
    )
    eh.record_outcome("TASK-Y", "Low", "haiku-4-5", 3000, "stop", "ok", path=p)
    recs = eh.read_outcomes(p)
    assert len(recs) == 2 and recs[0]["task_id"] == "TASK-X" and recs[1]["model"] == "haiku-4-5"
    assert recs[0]["policy_model"] == "sonnet"
    assert recs[0]["selected_model"] == "sonnet"
    assert recs[0]["routing_signals"] == ["grade_policy"]
    assert recs[0]["baseline_tokens"] == 60000


def test_execution_receipt_persists_request_resolution_observation_and_source(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    rec = eh.record_execution_receipt(
        dispatch_id="dispatch-1",
        task_id="TASK-X",
        claim_id="CLAIM-X",
        role="scribe",
        provider="native-codex",
        execution_surface="native_subagent_spawn",
        requested_tier="worker_low",
        selected_tier="worker_low",
        resolved_model="gpt-5.6-terra",
        resolved_reasoning_effort="low",
        resolved_model_source="adapter_default:model",
        resolved_reasoning_source="adapter_default:reasoning",
        observed_provider="openai",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
        tokens_in=120,
        tokens_out=30,
        billed_cost=0.01,
        currency="usd",
        source="native_codex_reply",
        status="completed",
        route_status="effective",
        application_status="applied",
        route_changed=True,
        baseline_model="gpt-5.6-terra",
        baseline_reasoning_effort="medium",
        baseline_observation_status="observed",
        baseline_tokens=300,
        path=path,
    )

    assert rec["schema"] == eh.EXECUTION_RECEIPT_SCHEMA
    assert rec["immutable"] is True
    assert rec["requested_tier"] == "worker_low"
    assert rec["resolved_reasoning_effort"] == "low"
    assert rec["observed_reasoning_effort"] == "low"
    assert rec["tokens"] == 150
    assert rec["currency"] == "USD"
    assert rec["source"] == "native_codex_reply"
    assert eh.read_outcomes(path) == [rec]


def test_execution_receipt_rejects_duplicate_dispatch_id(tmp_path):
    path = tmp_path / "receipts.jsonl"
    kwargs = {
        "dispatch_id": "dispatch-duplicate",
        "task_id": "TASK-X",
        "source": "provider_completion",
        "status": "completed",
        "path": path,
    }
    eh.record_execution_receipt(**kwargs)

    with pytest.raises(eh.ReceiptConflictError, match="immutable receipt"):
        eh.record_execution_receipt(**kwargs)

    assert len(eh.read_outcomes(path)) == 1


def test_persistent_task_and_claim_budget_survives_restart(tmp_path):
    path = tmp_path / "receipts.jsonl"
    eh.record_execution_receipt(
        dispatch_id="dispatch-first",
        task_id="TASK-X",
        claim_id="CLAIM-X",
        tokens_in=30,
        tokens_out=10,
        source="provider_completion",
        status="completed",
        path=path,
    )

    allowed = eh.budget_preflight(
        path=path,
        task_id="TASK-X",
        claim_id="CLAIM-X",
        dispatch_id="dispatch-second",
        dispatch_ceiling=40,
        task_token_budget=100,
        claim_token_budget=90,
    )
    blocked = eh.budget_preflight(
        path=path,
        task_id="TASK-X",
        claim_id="CLAIM-X",
        dispatch_id="dispatch-third",
        dispatch_ceiling=61,
        task_token_budget=100,
        claim_token_budget=90,
    )

    assert allowed["allowed"] is True
    assert allowed["task_tokens_used"] == 40
    assert allowed["claim_tokens_used"] == 40
    assert blocked["allowed"] is False
    assert blocked["reason"] == "task_budget_insufficient"


def test_configured_budget_fails_closed_without_provider_ceiling(tmp_path):
    result = eh.budget_preflight(
        path=tmp_path / "receipts.jsonl",
        task_id="TASK-X",
        claim_id="CLAIM-X",
        dispatch_id="dispatch-no-ceiling",
        dispatch_ceiling=None,
        task_token_budget=100,
    )

    assert result["allowed"] is False
    assert result["reason"] == "dispatch_ceiling_unavailable"


def test_cli_record_writes_routing_metadata(tmp_path, capsys):
    p = tmp_path / "eval_log.jsonl"
    rc = eh.main([
        "--record",
        "--task-id", "TASK-X",
        "--grade", "Medium",
        "--model", "sonnet",
        "--tokens", "1200",
        "--policy-model", "sonnet",
        "--selected-model", "sonnet",
        "--routing-signal", "grade_policy",
        "--routing-signal", "prompt_simple_lookup",
        "--baseline-tokens", "3000",
        "--log", str(p),
        "--json",
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert '"task_id": "TASK-X"' in captured.out
    rec = eh.read_outcomes(p)[0]
    assert rec["policy_model"] == "sonnet"
    assert rec["selected_model"] == "sonnet"
    assert rec["routing_signals"] == ["grade_policy", "prompt_simple_lookup"]
    assert rec["baseline_tokens"] == 3000


# ---- report (scoreboard) ----

def test_report_aggregates_escalation():
    recs = _golden_records()
    rep = eh.report(recs)
    assert rep["total"] == len(recs)
    # High 등급에 escalate 2건(G5·G6) 존재 → escalation_rate > 0
    assert rep["by_grade"]["High"]["escalations"] >= 2
    assert 0.0 <= rep["opus_share"] <= 1.0


def test_report_opus_share():
    recs = [{"grade": "Critical", "model": "opus-4-8", "tokens": 1, "finish_reason": "stop", "outcome": "ok"},
            {"grade": "Low", "model": "haiku-4-5", "tokens": 1, "finish_reason": "stop", "outcome": "ok"}]
    assert eh.report(recs)["opus_share"] == 0.5


def test_report_includes_token_delta_only_with_effective_model_evidence():
    recs = [
        _effective_delta_record(),
        _effective_delta_record(
            grade="High",
            model="claude-sonnet-4-6",
            observed_model="claude-sonnet-4-6",
            tokens=250,
            baseline_tokens=500,
        ),
    ]
    report = eh.report(recs)
    delta = report["token_delta"]
    assert delta["actual_tokens"] == 350
    assert delta["baseline_tokens"] == 900
    assert delta["saved_tokens"] == 550
    assert delta["saved_rate"] == 0.611
    assert delta["monetary_claim"] is False
    assert report["cost_delta"]["deprecated_alias"] is True


def test_token_delta_excludes_unknown_zero_actual_tokens():
    recs = [
        _effective_delta_record(
            tokens=0,
            actual_tokens_known=False,
            finish_reason="error",
            outcome="gate-error",
        ),
        _effective_delta_record(tokens=250, baseline_tokens=500),
    ]
    delta = eh.report(recs)["token_delta"]
    assert delta["actual_tokens"] == 250
    assert delta["baseline_tokens"] == 500
    assert delta["saved_tokens"] == 250
    assert delta["saved_rate"] == 0.5
    assert delta["exclusion_reasons"]["actual_token_usage_unavailable"] == 1


def test_equivalent_route_cannot_contribute_to_token_delta():
    rec = _effective_delta_record(
        model="gpt-5.2-codex",
        observed_model="gpt-5.2-codex",
        baseline_model="gpt-5.2-codex",
        model_changed=False,
        route_status="ineffective_equivalent",
    )
    delta = eh.report([rec])["token_delta"]
    assert delta["eligible_records"] == 0
    assert delta["saved_tokens"] == 0
    assert delta["exclusion_reasons"]["route_ineffective_equivalent"] == 1


def test_receipt_savings_require_observed_comparable_baseline():
    receipt = {
        **_effective_delta_record(),
        "schema": eh.EXECUTION_RECEIPT_SCHEMA,
        "route_changed": True,
        "baseline_observation_status": "configured",
    }
    unavailable = eh.report([receipt])["token_delta"]
    receipt["baseline_observation_status"] = "observed"
    observed = eh.report([receipt])["token_delta"]

    assert unavailable["eligible_records"] == 0
    assert (
        unavailable["exclusion_reasons"]["baseline_observation_unavailable"]
        == 1
    )
    assert observed["eligible_records"] == 1


def test_monetary_delta_requires_comparable_same_currency_billed_cost():
    verified = _effective_delta_record(
        billed_cost=0.2,
        currency="USD",
        baseline_billed_cost=0.5,
        baseline_currency="usd",
    )
    mismatch = _effective_delta_record(
        billed_cost=0.2,
        currency="USD",
        baseline_billed_cost=0.5,
        baseline_currency="EUR",
    )
    delta = eh.report([verified, mismatch])["monetary_delta"]
    assert delta["verified"] is True
    assert delta["eligible_records"] == 1
    assert delta["by_currency"]["USD"]["saved_billed_cost"] == 0.3
    assert delta["exclusion_reasons"]["currency_mismatch"] == 1


def test_record_outcome_rejects_cost_without_currency(tmp_path):
    with pytest.raises(ValueError, match="currency is required"):
        eh.record_outcome(
            "TASK-X",
            "Low",
            "claude-haiku-4-5",
            100,
            billed_cost=0.2,
            path=tmp_path / "eval.jsonl",
        )


def test_report_includes_collaboration_verdict_delta():
    recs = [
        {"grade": "Medium", "model": "sonnet", "tokens": 1200, "baseline_tokens": 400,
         "baseline_verdict": "approve", "collab_verdict": "approve",
         "collab_members": ["reviewer"]},
        {"grade": "High", "model": "sonnet", "tokens": 1800, "baseline_tokens": 600,
         "baseline_verdict": "approve", "collab_verdict": "reject",
         "collab_members": ["reviewer", "skeptic"]},
    ]
    delta = eh.report(recs)["collaboration_delta"]
    assert delta["total"] == 2
    assert delta["verdict_changes"] == 1
    assert delta["verdict_change_rate"] == 0.5
    assert delta["baseline_tokens"] == 1000
    assert delta["collaboration_tokens"] == 3000
    assert delta["token_multiplier"] == 3.0


def test_collaboration_delta_excludes_unattributed_or_unpriced_rows():
    recs = [
        {"grade": "High", "model": "sonnet", "tokens": 1800, "baseline_tokens": 600,
         "baseline_verdict": "approve", "collab_verdict": "reject"},
        {"grade": "High", "model": "sonnet", "tokens": 1800,
         "baseline_verdict": "approve", "collab_verdict": "reject",
         "collab_members": ["reviewer", "skeptic"]},
        {"grade": "High", "model": "sonnet", "tokens": 1800, "baseline_tokens": 600,
         "baseline_verdict": "approve", "collab_verdict": "reject",
         "collab_members": ["reviewer", "skeptic"]},
    ]
    delta = eh.report(recs)["collaboration_delta"]
    assert delta["total"] == 1
    assert delta["baseline_tokens"] == 600
    assert delta["collaboration_tokens"] == 1800
    assert delta["token_multiplier"] == 3.0


def test_record_outcome_accepts_collaboration_eval_fields(tmp_path):
    rec = eh.record_outcome(
        "TASK-240",
        "High",
        "sonnet",
        1800,
        baseline_tokens=600,
        baseline_verdict="approve",
        collab_verdict="reject",
        collab_members=["reviewer", "skeptic"],
        path=tmp_path / "eval.jsonl",
    )
    assert rec["baseline_verdict"] == "approve"
    assert rec["collab_verdict"] == "reject"
    assert rec["collab_members"] == ["reviewer", "skeptic"]


# ---- escalation proposals (자가개선 — 배치, 사람 ratify) ----

def test_escalation_proposals_fire_over_threshold():
    # High 5건 중 3건 escalate(0.6) > 0.3 → 제안 발생
    recs = [{"grade": "High", "model": "sonnet-4-6", "tokens": 1, "finish_reason": "stop",
             "outcome": ("rejected" if i < 3 else "ok")} for i in range(5)]
    props = eh.escalation_proposals(recs, threshold=0.3)
    assert any("High" in p for p in props)
    assert any("sonnet" in p for p in props)


def test_escalation_proposals_quiet_under_threshold():
    recs = [{"grade": "Low", "model": "haiku-4-5", "tokens": 1, "finish_reason": "stop", "outcome": "ok"}
            for _ in range(5)]
    assert eh.escalation_proposals(recs, threshold=0.3) == []
