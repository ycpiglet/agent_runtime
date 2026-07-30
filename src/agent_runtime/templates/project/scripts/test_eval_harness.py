"""TASK-238 — agentic 측정 substrate 테스트."""
import importlib.util
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
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


def _write_claim_authority(
    root: Path,
    *,
    claim_id: str,
    task_id: str,
    task_token_budget: int | None,
    claim_token_budget: int | None,
) -> None:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    (claim_dir / f"{claim_id}.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": claim_id,
                "task_id": task_id,
                "status": "claimed",
                "task_token_budget": task_token_budget,
                "claim_token_budget": claim_token_budget,
            }
        ),
        encoding="utf-8",
    )


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


def _verified_delta_records(
    prefix: str,
    *,
    actual_tokens: int = 100,
    baseline_tokens: int = 400,
    actual_tokens_known: bool = True,
    actual_model: str = "claude-haiku-4-5",
    baseline_model: str = "claude-opus-4-8",
    actual_reasoning: str | None = "low",
    baseline_reasoning: str | None = "high",
    route_status: str = "effective",
    route_changed: bool = True,
    actual_billed_cost: float | None = None,
    actual_currency: str | None = None,
    baseline_billed_cost: float | None = None,
    baseline_currency: str | None = None,
) -> list[dict]:
    workload_id = f"workload-{prefix}"
    baseline_receipt_id = f"receipt-baseline-{prefix}"
    baseline = {
        "schema": eh.EXECUTION_RECEIPT_SCHEMA,
        "immutable": True,
        "receipt_id": baseline_receipt_id,
        "dispatch_id": f"baseline-{prefix}",
        "task_id": "TASK-SAVE",
        "workload_id": workload_id,
        "status": "completed",
        "provider": "native-codex",
        "resolved_reasoning_effort": baseline_reasoning,
        "resolved_reasoning_source": "adapter_default:test",
        "observed_provider": "native-codex",
        "observed_model": baseline_model,
        "observed_reasoning_effort": baseline_reasoning,
        "actual_tokens_known": True,
        "token_usage_status": "observed",
        "tokens": baseline_tokens,
        "billed_cost": baseline_billed_cost,
        "currency": baseline_currency,
        "grade": "Low",
        "model": baseline_model,
        "finish_reason": "stop",
        "outcome": "ok",
    }
    actual = {
        "schema": eh.EXECUTION_RECEIPT_SCHEMA,
        "immutable": True,
        "receipt_id": f"receipt-actual-{prefix}",
        "dispatch_id": f"actual-{prefix}",
        "task_id": "TASK-SAVE",
        "workload_id": workload_id,
        "status": "completed",
        "provider": "native-codex",
        "resolved_reasoning_effort": actual_reasoning,
        "resolved_reasoning_source": "adapter_default:test",
        "observed_provider": "native-codex",
        "observed_model": actual_model,
        "observed_reasoning_effort": actual_reasoning,
        "actual_tokens_known": actual_tokens_known,
        "token_usage_status": (
            "observed" if actual_tokens_known else "unavailable"
        ),
        "tokens": actual_tokens,
        "billed_cost": actual_billed_cost,
        "currency": actual_currency,
        "baseline_receipt_id": baseline_receipt_id,
        "baseline_reference_status": "verified",
        "baseline_model": baseline_model,
        "application_status": "applied",
        "route_status": route_status,
        "route_changed": route_changed,
        "model_changed": route_changed,
        "grade": "Low",
        "model": actual_model,
        "finish_reason": "stop",
        "outcome": "ok",
    }
    return [baseline, actual]


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
    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-X",
        task_id="TASK-X",
        task_token_budget=100,
        claim_token_budget=90,
    )
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
        root=tmp_path,
        task_id="TASK-X",
        claim_id="CLAIM-X",
        dispatch_id="dispatch-second",
        dispatch_ceiling=40,
        task_token_budget=100,
        claim_token_budget=90,
    )
    blocked = eh.budget_preflight(
        path=path,
        root=tmp_path,
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
        claim_id=None,
        dispatch_id="dispatch-no-ceiling",
        dispatch_ceiling=None,
        task_token_budget=100,
    )

    assert result["allowed"] is False
    assert result["reason"] == "dispatch_ceiling_unavailable"


def test_atomic_reservation_prevents_concurrent_budget_and_duplicate_side_effects(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-RACE",
        task_id="TASK-RACE",
        task_token_budget=100,
        claim_token_budget=None,
    )
    barrier = threading.Barrier(2)

    def reserve(dispatch_id):
        barrier.wait()
        return eh.reserve_dispatch_budget(
            path=path,
            root=tmp_path,
            task_id="TASK-RACE",
            claim_id="CLAIM-RACE",
            dispatch_id=dispatch_id,
            dispatch_ceiling=60,
            task_token_budget=100,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, ("race-1", "race-2")))

    assert sum(result["allowed"] is True for result in results) == 1
    assert sum(result["reason"] == "task_budget_insufficient" for result in results) == 1
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-RACE",
        claim_id="CLAIM-RACE",
    )
    assert usage["task"]["tokens"] == 0
    assert usage["task"]["reserved_tokens"] == 60
    assert usage["task"]["committed_tokens"] == 60

    duplicate_barrier = threading.Barrier(2)

    def duplicate():
        duplicate_barrier.wait()
        return eh.reserve_dispatch_budget(
            path=path,
            task_id="TASK-DUP",
            claim_id=None,
            dispatch_id="same-dispatch",
            dispatch_ceiling=10,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        duplicate_results = list(pool.map(lambda _: duplicate(), range(2)))

    assert sum(result["allowed"] is True for result in duplicate_results) == 1
    assert sum(
        result["reason"] == "duplicate_dispatch_id"
        for result in duplicate_results
    ) == 1


def test_batch_reservation_is_all_or_none_and_dry_run_stays_read_only(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-BATCH-BUDGET",
        task_id="TASK-BATCH-BUDGET",
        task_token_budget=15,
        claim_token_budget=None,
    )
    requests = [
        {
            "task_id": "TASK-BATCH-BUDGET",
            "claim_id": "CLAIM-BATCH-BUDGET",
            "dispatch_id": dispatch_id,
            "dispatch_ceiling": 10,
        }
        for dispatch_id in ("batch-budget-1", "batch-budget-2")
    ]

    planned = eh.plan_dispatch_budgets(
        requests[:1],
        path=path,
        root=tmp_path,
    )
    denied = eh.reserve_dispatch_budgets(
        requests,
        path=path,
        root=tmp_path,
    )

    assert planned["allowed"] is True
    assert planned["results"][0]["reservation_status"] == "planned"
    assert eh.read_outcomes(path) == []
    assert denied["allowed"] is False
    assert denied["reservations"] == []
    assert denied["results"][0]["batch_reason"] == "batch_budget_denied"
    assert denied["results"][0]["reservation_status"] == "not_reserved"
    assert denied["results"][1]["reason"] == "task_budget_insufficient"
    assert eh.read_outcomes(path) == []

    subsequent = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-BATCH-BUDGET",
        claim_id="CLAIM-BATCH-BUDGET",
        dispatch_id="batch-budget-subsequent",
        dispatch_ceiling=15,
    )
    assert subsequent["allowed"] is True


def test_claim_record_is_authoritative_budget_source(tmp_path):
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-AUTH.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-AUTH",
                "task_id": "TASK-AUTH",
                "status": "claimed",
                "task_token_budget": 0,
                "claim_token_budget": 0,
            }
        ),
        encoding="utf-8",
    )

    result = eh.reserve_dispatch_budget(
        root=tmp_path,
        path=tmp_path / "receipts.jsonl",
        task_id="TASK-AUTH",
        claim_id="CLAIM-AUTH",
        dispatch_id="dispatch-authoritative",
        dispatch_ceiling=1,
    )

    assert result["allowed"] is False
    assert result["reason"] == "task_budget_insufficient"
    assert result["task_token_budget"] == 0
    assert result["claim_token_budget"] == 0
    assert result["budget_authority"]["claim_id"] == "CLAIM-AUTH"
    assert result["budget_authority"]["source"] == "claim_record"


def test_unique_active_claim_is_authoritative_when_caller_omits_claim_id(
    tmp_path,
):
    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-AUTO-AUTH",
        task_id="TASK-AUTO-AUTH",
        task_token_budget=0,
        claim_token_budget=0,
    )

    result = eh.reserve_dispatch_budget(
        root=tmp_path,
        path=tmp_path / "receipts.jsonl",
        task_id="TASK-AUTO-AUTH",
        claim_id=None,
        dispatch_id="dispatch-auto-authority",
        dispatch_ceiling=1,
    )

    assert result["allowed"] is False
    assert result["reason"] == "task_budget_insufficient"
    assert result["budget_authority"]["claim_id"] == "CLAIM-AUTO-AUTH"
    assert result["budget_authority"]["source"] == "claim_record"


def test_auto_resolved_claim_identity_survives_reservation_and_receipt(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-AUTO-SETTLE",
        task_id="TASK-AUTO-SETTLE",
        task_token_budget=100,
        claim_token_budget=100,
    )

    preflight = eh.reserve_dispatch_budget(
        root=tmp_path,
        path=path,
        task_id="TASK-AUTO-SETTLE",
        claim_id=None,
        dispatch_id="dispatch-auto-settle",
        dispatch_ceiling=10,
    )
    receipt = eh.record_execution_receipt(
        dispatch_id="dispatch-auto-settle",
        task_id="TASK-AUTO-SETTLE",
        claim_id=None,
        source="provider_completion",
        status="completed",
        tokens_in=2,
        tokens_out=3,
        budget_preflight_result=preflight,
        path=path,
    )

    rows = eh.read_outcomes(path)
    assert preflight["allowed"] is True
    assert preflight["claim_id"] == "CLAIM-AUTO-SETTLE"
    assert rows[0]["claim_id"] == "CLAIM-AUTO-SETTLE"
    assert receipt["claim_id"] == "CLAIM-AUTO-SETTLE"
    assert receipt["budget_reservation_status"] == "settled"


def test_ambiguous_active_claim_authority_fails_closed(tmp_path):
    for claim_id in ("CLAIM-AUTO-A", "CLAIM-AUTO-B"):
        _write_claim_authority(
            tmp_path,
            claim_id=claim_id,
            task_id="TASK-AUTO-AMBIGUOUS",
            task_token_budget=100,
            claim_token_budget=100,
        )

    with pytest.raises(eh.ReceiptIntegrityError, match="multiple active claim"):
        eh.reserve_dispatch_budget(
            root=tmp_path,
            path=tmp_path / "receipts.jsonl",
            task_id="TASK-AUTO-AMBIGUOUS",
            claim_id=None,
            dispatch_id="dispatch-auto-ambiguous",
            dispatch_ceiling=1,
        )


def test_duplicate_or_mismatched_ledger_identity_fails_closed(tmp_path):
    path = tmp_path / "receipts.jsonl"
    rows = [
        {
            "schema": eh.EXECUTION_RECEIPT_SCHEMA,
            "immutable": True,
            "receipt_id": "receipt-one",
            "dispatch_id": "duplicate-dispatch",
            "task_id": "TASK-X",
        },
        {
            "schema": eh.EXECUTION_RECEIPT_SCHEMA,
            "immutable": True,
            "receipt_id": "receipt-two",
            "dispatch_id": "duplicate-dispatch",
            "task_id": "TASK-X",
        },
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(eh.ReceiptIntegrityError, match="duplicate dispatch_id"):
        eh.budget_preflight(
            path=path,
            task_id="TASK-OTHER",
            claim_id=None,
            dispatch_id="new-dispatch",
            dispatch_ceiling=1,
        )


def test_missing_or_inactive_claim_authority_fails_closed(tmp_path):
    with pytest.raises(eh.ReceiptIntegrityError, match="authority missing"):
        eh.reserve_dispatch_budget(
            root=tmp_path,
            path=tmp_path / "receipts.jsonl",
            task_id="TASK-CLAIM",
            claim_id="CLAIM-MISSING",
            dispatch_id="dispatch-missing",
            dispatch_ceiling=1,
        )

    _write_claim_authority(
        tmp_path,
        claim_id="CLAIM-INACTIVE",
        task_id="TASK-CLAIM",
        task_token_budget=10,
        claim_token_budget=10,
    )
    claim_path = (
        tmp_path
        / "agents"
        / "runtime"
        / "task_claims"
        / "CLAIM-INACTIVE.json"
    )
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    payload["status"] = "released"
    claim_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(eh.ReceiptIntegrityError, match="not active"):
        eh.reserve_dispatch_budget(
            root=tmp_path,
            path=tmp_path / "receipts.jsonl",
            task_id="TASK-CLAIM",
            claim_id="CLAIM-INACTIVE",
            dispatch_id="dispatch-inactive",
            dispatch_ceiling=1,
        )


def test_batch_terminal_receipts_append_all_or_none(tmp_path):
    path = tmp_path / "receipts.jsonl"
    eh.record_execution_receipt(
        dispatch_id="batch-existing",
        task_id="TASK-BATCH",
        source="provider_completion",
        status="completed",
        path=path,
    )

    with pytest.raises(eh.ReceiptConflictError):
        eh.record_execution_receipts(
            [
                {
                    "dispatch_id": "batch-new",
                    "task_id": "TASK-BATCH",
                    "source": "provider_completion",
                    "status": "completed",
                },
                {
                    "dispatch_id": "batch-existing",
                    "task_id": "TASK-BATCH",
                    "source": "provider_completion",
                    "status": "completed",
                },
            ],
            path=path,
        )

    assert [
        receipt["dispatch_id"] for receipt in eh.read_outcomes(path)
    ] == ["batch-existing"]


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
    recs = (
        _verified_delta_records("low")
        + _verified_delta_records(
            "high",
            actual_tokens=250,
            baseline_tokens=500,
            actual_model="claude-sonnet-4-6",
        )
    )
    report = eh.report(recs)
    delta = report["token_delta"]
    assert delta["actual_tokens"] == 350
    assert delta["baseline_tokens"] == 900
    assert delta["saved_tokens"] == 550
    assert delta["saved_rate"] == 0.611
    assert delta["monetary_claim"] is False
    assert report["cost_delta"]["deprecated_alias"] is True


def test_token_delta_excludes_unknown_zero_actual_tokens():
    recs = (
        _verified_delta_records(
            "unknown",
            actual_tokens=0,
            actual_tokens_known=False,
        )
        + _verified_delta_records(
            "known",
            actual_tokens=250,
            baseline_tokens=500,
        )
    )
    delta = eh.report(recs)["token_delta"]
    assert delta["actual_tokens"] == 250
    assert delta["baseline_tokens"] == 500
    assert delta["saved_tokens"] == 250
    assert delta["saved_rate"] == 0.5
    assert delta["exclusion_reasons"]["actual_token_usage_unavailable"] == 1


def test_equivalent_route_cannot_contribute_to_token_delta():
    recs = _verified_delta_records(
        "equivalent",
        actual_model="gpt-5.2-codex",
        baseline_model="gpt-5.2-codex",
        actual_reasoning="high",
        baseline_reasoning="high",
        route_changed=False,
        route_status="ineffective_equivalent",
    )
    delta = eh.report(recs)["token_delta"]
    assert delta["eligible_records"] == 0
    assert delta["saved_tokens"] == 0
    assert delta["exclusion_reasons"]["route_ineffective_equivalent"] == 1


def test_forged_route_flags_cannot_hide_observed_route_equivalence():
    recs = _verified_delta_records(
        "forged-equivalent",
        actual_model="gpt-5.6-sol",
        baseline_model="gpt-5.6-sol",
        actual_reasoning="high",
        baseline_reasoning="high",
        route_changed=True,
        route_status="effective",
    )

    delta = eh.report(recs)["token_delta"]
    assert delta["eligible_records"] == 0
    assert delta["saved_tokens"] == 0
    assert delta["exclusion_reasons"]["route_ineffective_equivalent"] == 1


def test_caller_claimed_baseline_metadata_cannot_create_savings():
    receipt = {
        **_effective_delta_record(),
        "schema": eh.EXECUTION_RECEIPT_SCHEMA,
        "receipt_id": "receipt-unreferenced",
        "dispatch_id": "dispatch-unreferenced",
        "route_changed": True,
        "baseline_observation_status": "configured",
    }
    unavailable = eh.report([receipt])["token_delta"]
    receipt["baseline_observation_status"] = "observed"
    observed = eh.report([receipt])["token_delta"]

    assert unavailable["eligible_records"] == 0
    assert unavailable["exclusion_reasons"]["baseline_receipt_unavailable"] == 1
    assert observed["eligible_records"] == 0
    assert observed["exclusion_reasons"]["baseline_receipt_unavailable"] == 1


def test_savings_require_referenced_baseline_receipt_and_workload_identity(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-dispatch",
        task_id="TASK-SAVE",
        workload_id="workload-same",
        provider="native-codex",
        resolved_reasoning_effort="high",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="expensive-model",
        observed_reasoning_effort="high",
        tokens_in=80,
        tokens_out=20,
        billed_cost=0.10,
        currency="USD",
        source="provider_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-dispatch",
        task_id="TASK-SAVE",
        workload_id="workload-same",
        provider="native-codex",
        observed_provider="native-codex",
        observed_model="cheap-model",
        observed_reasoning_effort="low",
        resolved_model="cheap-model",
        resolved_reasoning_effort="low",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        tokens_in=15,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        source="provider_completion",
        status="completed",
        route_status="effective",
        application_status="applied",
        route_changed=True,
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    report = eh.report(eh.read_outcomes(path))
    assert actual["baseline_reference_status"] == "verified"
    assert report["token_delta"]["eligible_records"] == 1
    assert report["token_delta"]["saved_tokens"] == 80
    assert report["monetary_delta"]["eligible_records"] == 1
    assert report["monetary_delta"]["by_currency"]["USD"][
        "saved_billed_cost"
    ] == 0.08

    forged = eh.record_execution_receipt(
        dispatch_id="forged-dispatch",
        task_id="TASK-SAVE",
        workload_id="workload-same",
        provider="native-codex",
        observed_provider="native-codex",
        observed_model="cheap-model",
        tokens_in=15,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        source="provider_completion",
        status="completed",
        route_status="effective",
        application_status="applied",
        route_changed=True,
        baseline_receipt_id="missing-receipt",
        baseline_model="caller-forged-model",
        baseline_observation_status="observed",
        baseline_tokens=1000,
        baseline_billed_cost=1.0,
        baseline_currency="USD",
        path=path,
    )
    assert forged["baseline_reference_status"] == "invalid"
    assert forged["baseline_model"] is None
    assert forged["baseline_observation_status"] == "unavailable"
    assert forged["baseline_tokens"] is None
    assert forged["baseline_billed_cost"] is None
    assert forged["baseline_currency"] is None
    forged_report = eh.report([baseline, forged])
    assert forged_report["token_delta"]["eligible_records"] == 0
    assert forged_report["monetary_delta"]["eligible_records"] == 0
    assert (
        forged_report["token_delta"]["exclusion_reasons"][
            "baseline_receipt_unavailable"
        ]
        == 1
    )


def test_finalizer_recomputes_route_equivalence_from_observed_receipts(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-equivalent",
        task_id="TASK-EQUIVALENT",
        workload_id="workload-equivalent",
        provider="native-codex",
        resolved_reasoning_effort="high",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        observed_reasoning_effort="high",
        tokens_in=80,
        tokens_out=20,
        source="native_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-equivalent",
        task_id="TASK-EQUIVALENT",
        workload_id="workload-equivalent",
        provider="native-codex",
        resolved_model="gpt-5.6-sol",
        resolved_reasoning_effort="high",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        observed_reasoning_effort="high",
        tokens_in=10,
        tokens_out=5,
        source="native_completion",
        status="completed",
        route_status="effective",
        application_status="applied",
        model_changed=True,
        route_changed=True,
        baseline_receipt_id=baseline["receipt_id"],
        baseline_model="caller-forged-expensive-model",
        baseline_reasoning_effort="max",
        baseline_observation_status="observed",
        baseline_tokens=10_000,
        path=path,
    )

    assert actual["baseline_reference_status"] == "verified"
    assert actual["baseline_model"] == "gpt-5.6-sol"
    assert actual["baseline_reasoning_effort"] == "high"
    assert actual["model_changed"] is False
    assert actual["route_changed"] is False
    assert actual["route_status"] == "ineffective_equivalent"
    assert actual["application_status"] == "applied"
    delta = eh.report(eh.read_outcomes(path))["token_delta"]
    assert delta["eligible_records"] == 0
    assert delta["exclusion_reasons"]["route_ineffective_equivalent"] == 1


def test_native_baseline_missing_observed_reasoning_is_not_comparable(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-missing-reasoning",
        task_id="TASK-INCOMPLETE-BASELINE",
        workload_id="workload-incomplete-baseline",
        provider="native-codex",
        resolved_model="gpt-5.6-sol",
        resolved_reasoning_effort="high",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        tokens_in=80,
        tokens_out=20,
        billed_cost=0.10,
        currency="USD",
        source="native_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-missing-baseline-reasoning",
        task_id="TASK-INCOMPLETE-BASELINE",
        workload_id="workload-incomplete-baseline",
        provider="native-codex",
        resolved_model="gpt-5.6-sol",
        resolved_reasoning_effort="low",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        observed_reasoning_effort="low",
        tokens_in=10,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        source="native_completion",
        status="completed",
        route_status="effective",
        application_status="applied",
        model_changed=False,
        route_changed=True,
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_route_observation_incomplete"
    )
    assert actual["baseline_reasoning_effort"] is None
    report = eh.report(eh.read_outcomes(path))
    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "baseline_reasoning_observation_unavailable"
        ]
        == 1
    )


def test_native_baseline_cannot_forge_unsupported_reasoning_source(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-forged-unsupported",
        task_id="TASK-FORGED-UNSUPPORTED",
        workload_id="workload-forged-unsupported",
        provider="native-codex",
        resolved_model="gpt-5.6-sol",
        resolved_reasoning_effort="high",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="unsupported",
        observed_provider="native-codex",
        observed_model="gpt-5.6-sol",
        tokens_in=80,
        tokens_out=20,
        billed_cost=0.10,
        currency="USD",
        source="native_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-forged-unsupported",
        task_id="TASK-FORGED-UNSUPPORTED",
        workload_id="workload-forged-unsupported",
        provider="native-codex",
        resolved_model="gpt-5.6-terra",
        resolved_reasoning_effort="low",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
        tokens_in=10,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        source="native_completion",
        status="completed",
        route_status="effective",
        application_status="applied",
        model_changed=True,
        route_changed=True,
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_route_observation_incomplete"
    )
    report = eh.report(eh.read_outcomes(path))
    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "baseline_reasoning_observation_unavailable"
        ]
        == 1
    )


def test_report_rejects_native_actual_forged_as_reasoning_unsupported():
    baseline, actual = _verified_delta_records(
        "forged-actual-unsupported",
        actual_tokens=15,
        baseline_tokens=100,
        actual_model="gpt-5.6-terra",
        baseline_model="gpt-5.6-sol",
        actual_reasoning=None,
        baseline_reasoning="high",
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    baseline.update(
        {
            "provider": "native-codex",
            "observed_provider": "native-codex",
            "resolved_reasoning_effort": "high",
            "resolved_reasoning_source": "adapter_default:test",
        }
    )
    actual.update(
        {
            "provider": "native-codex",
            "observed_provider": "native-codex",
            "resolved_reasoning_effort": "low",
            "resolved_reasoning_source": "unsupported",
        }
    )

    report = eh.report([baseline, actual])

    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "observed_reasoning_unavailable"
        ]
        == 1
    )


def test_canonical_codex_agent_unsupported_reasoning_stays_comparable(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("CODEX_AGENT_OPUS_MODEL", "gpt-codex-expensive")
    monkeypatch.setenv("CODEX_AGENT_HAIKU_MODEL", "gpt-codex-cheap")
    baseline_route = eh.model_routing.resolve_provider_route(
        "codex-agent",
        "planner_high",
    )
    actual_route = eh.model_routing.resolve_provider_route(
        "codex-agent",
        "worker_low",
    )
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-codex-unsupported",
        task_id="TASK-CODEX-UNSUPPORTED",
        workload_id="workload-codex-unsupported",
        provider=baseline_route["provider"],
        resolved_model=baseline_route["resolved_model"],
        resolved_reasoning_effort=baseline_route["reasoning_effort"],
        resolved_model_source=baseline_route["model_source"],
        resolved_reasoning_source=baseline_route["reasoning_source"],
        observed_provider="codex-agent",
        observed_model=baseline_route["resolved_model"],
        tokens_in=80,
        tokens_out=20,
        source="provider_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-codex-unsupported",
        task_id="TASK-CODEX-UNSUPPORTED",
        workload_id="workload-codex-unsupported",
        provider=actual_route["provider"],
        resolved_model=actual_route["resolved_model"],
        resolved_reasoning_effort=actual_route["reasoning_effort"],
        resolved_model_source=actual_route["model_source"],
        resolved_reasoning_source=actual_route["reasoning_source"],
        observed_provider="codex-agent",
        observed_model=actual_route["resolved_model"],
        tokens_in=10,
        tokens_out=5,
        source="provider_completion",
        status="completed",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["baseline_reference_status"] == "verified"
    assert actual["application_status"] == "applied"
    report = eh.report(eh.read_outcomes(path))
    assert report["token_delta"]["eligible_records"] == 1
    assert report["token_delta"]["saved_tokens"] == 85


def _unsupported_codex_pair(
    tmp_path,
    monkeypatch,
    *,
    baseline_observed_provider="codex-agent",
    actual_observed_provider="codex-agent",
    configured_provider="codex-agent",
):
    monkeypatch.setenv("CODEX_AGENT_OPUS_MODEL", "gpt-codex-expensive")
    monkeypatch.setenv("CODEX_AGENT_HAIKU_MODEL", "gpt-codex-cheap")
    baseline_route = eh.model_routing.resolve_provider_route(
        configured_provider,
        "planner_high",
    )
    actual_route = eh.model_routing.resolve_provider_route(
        configured_provider,
        "worker_low",
    )
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-provider-identity",
        task_id="TASK-PROVIDER-IDENTITY",
        workload_id="workload-provider-identity",
        provider=configured_provider,
        resolved_model=baseline_route["resolved_model"],
        resolved_reasoning_effort=baseline_route["reasoning_effort"],
        resolved_model_source=baseline_route["model_source"],
        resolved_reasoning_source=baseline_route["reasoning_source"],
        observed_provider=baseline_observed_provider,
        observed_model=baseline_route["resolved_model"],
        tokens_in=80,
        tokens_out=20,
        billed_cost=0.10,
        currency="USD",
        source="provider_completion",
        status="completed",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-provider-identity",
        task_id="TASK-PROVIDER-IDENTITY",
        workload_id="workload-provider-identity",
        provider=configured_provider,
        resolved_model=actual_route["resolved_model"],
        resolved_reasoning_effort=actual_route["reasoning_effort"],
        resolved_model_source=actual_route["model_source"],
        resolved_reasoning_source=actual_route["reasoning_source"],
        observed_provider=actual_observed_provider,
        observed_model=actual_route["resolved_model"],
        tokens_in=10,
        tokens_out=5,
        billed_cost=0.02,
        currency="USD",
        source="provider_completion",
        status="completed",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )
    return actual, eh.report(eh.read_outcomes(path))


@pytest.mark.parametrize(
    "observed_provider",
    [
        None,
        "unknown-provider",
        "claude-agent",
        "native-codex",
        "codex-session",
        "codex-native",
    ],
    ids=(
        "missing",
        "unknown",
        "different-unsupported",
        "native",
        "native-session-alias",
        "native-name-alias",
    ),
)
def test_unsupported_actual_requires_matching_observed_provider(
    tmp_path,
    monkeypatch,
    observed_provider,
):
    actual, report = _unsupported_codex_pair(
        tmp_path,
        monkeypatch,
        actual_observed_provider=observed_provider,
    )

    assert actual["application_status"] == "unverified"
    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "observed_reasoning_unavailable"
        ]
        == 1
    )


@pytest.mark.parametrize(
    "observed_provider",
    [
        None,
        "unknown-provider",
        "claude-agent",
        "native-codex",
        "codex-session",
        "codex-native",
    ],
    ids=(
        "missing",
        "unknown",
        "different-unsupported",
        "native",
        "native-session-alias",
        "native-name-alias",
    ),
)
def test_unsupported_baseline_requires_matching_observed_provider(
    tmp_path,
    monkeypatch,
    observed_provider,
):
    actual, report = _unsupported_codex_pair(
        tmp_path,
        monkeypatch,
        baseline_observed_provider=observed_provider,
    )

    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_route_observation_incomplete"
    )
    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "baseline_reasoning_observation_unavailable"
        ]
        == 1
    )


def test_registered_codex_aliases_share_one_observed_provider_identity(
    tmp_path,
    monkeypatch,
):
    actual, report = _unsupported_codex_pair(
        tmp_path,
        monkeypatch,
        configured_provider="codex",
        baseline_observed_provider="codex-agent",
        actual_observed_provider="codex-agent",
    )

    assert actual["baseline_reference_status"] == "verified"
    assert actual["application_status"] == "applied"
    assert report["token_delta"]["eligible_records"] == 1
    assert report["token_delta"]["saved_tokens"] == 85
    assert report["monetary_delta"]["eligible_records"] == 1


@pytest.mark.parametrize(
    "observed_provider",
    [None, "unknown-provider", "claude-agent"],
    ids=("missing", "unknown", "mismatched"),
)
def test_provider_identity_is_required_even_when_reasoning_is_observed(
    observed_provider,
):
    baseline, actual = _verified_delta_records(
        f"provider-first-{observed_provider}",
        actual_tokens=15,
        baseline_tokens=100,
        actual_model="gpt-5.6-terra",
        baseline_model="gpt-5.6-sol",
        actual_reasoning="low",
        baseline_reasoning="high",
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    baseline.update(
        {
            "provider": "native-codex",
            "observed_provider": "native-codex",
            "resolved_reasoning_effort": "high",
            "resolved_reasoning_source": "adapter_default:test",
        }
    )
    actual.update(
        {
            "provider": "native-codex",
            "observed_provider": observed_provider,
            "resolved_reasoning_effort": "low",
            "resolved_reasoning_source": "adapter_default:test",
        }
    )

    report = eh.report([baseline, actual])

    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "observed_reasoning_unavailable"
        ]
        == 1
    )


def test_report_rejects_forged_verified_native_baseline_without_reasoning():
    baseline, actual = _verified_delta_records(
        "missing-baseline-reasoning",
        actual_model="gpt-5.6-sol",
        baseline_model="gpt-5.6-sol",
        actual_reasoning="low",
        baseline_reasoning=None,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    baseline["provider"] = "native-codex"
    baseline["observed_provider"] = "native-codex"
    baseline["resolved_reasoning_source"] = "adapter_default:test"
    actual["provider"] = "native-codex"
    actual["observed_provider"] = "native-codex"
    actual["resolved_reasoning_source"] = "adapter_default:test"

    report = eh.report([baseline, actual])

    assert report["token_delta"]["eligible_records"] == 0
    assert report["token_delta"]["saved_tokens"] == 0
    assert report["monetary_delta"]["eligible_records"] == 0
    assert (
        report["token_delta"]["exclusion_reasons"][
            "baseline_reasoning_observation_unavailable"
        ]
        == 1
    )


def test_monetary_delta_requires_comparable_same_currency_billed_cost():
    recs = (
        _verified_delta_records(
            "money-verified",
            actual_billed_cost=0.2,
            actual_currency="USD",
            baseline_billed_cost=0.5,
            baseline_currency="USD",
        )
        + _verified_delta_records(
            "money-mismatch",
            actual_billed_cost=0.2,
            actual_currency="USD",
            baseline_billed_cost=0.5,
            baseline_currency="EUR",
        )
    )
    delta = eh.report(recs)["monetary_delta"]
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
