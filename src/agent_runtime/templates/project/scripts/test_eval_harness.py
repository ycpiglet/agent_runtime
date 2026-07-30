"""TASK-238 — agentic 측정 substrate 테스트."""
import importlib.util
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import MappingProxyType

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


_FRESH_BUDGET_PROCESS = r"""
import importlib.util
import json
import sys
from pathlib import Path

module_path = Path(sys.argv[1])
ledger_path = Path(sys.argv[2])
authority_root = Path(sys.argv[3])
payload = json.loads(sys.argv[4])
spec = importlib.util.spec_from_file_location("_fresh_eval_harness", module_path)
eh = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = eh
spec.loader.exec_module(eh)

common = {
    "path": ledger_path,
    "root": authority_root,
    "task_id": payload["task_id"],
    "claim_id": payload["claim_id"],
}
if payload["action"] in {"settle", "settle_no_call"}:
    preflight = eh.reserve_dispatch_budget(
        **common,
        dispatch_id=payload["dispatch_id"],
        dispatch_ceiling=payload["dispatch_ceiling"],
        source=payload.get("reservation_source", "execution_preflight"),
    )
    call_start = None
    if payload.get("call_start"):
        call_start = eh.record_provider_call_start(
            dispatch_id=payload["dispatch_id"],
            task_id=payload["task_id"],
            source=payload["call_start"]["source"],
            provider=payload["call_start"]["provider"],
            execution_surface=payload["call_start"]["execution_surface"],
            path=ledger_path,
            root=authority_root,
        )
    record_receipt = (
        eh.record_pre_provider_skip_receipt
        if payload["action"] == "settle_no_call"
        else eh.record_execution_receipt
    )
    receipt = record_receipt(
        dispatch_id=payload["dispatch_id"],
        task_id=payload["task_id"],
        claim_id=payload["claim_id"],
        budget_preflight_result=preflight,
        path=ledger_path,
        **payload["receipt"],
    )
    result = {
        "preflight": preflight,
        "call_start": call_start,
        "receipt": receipt,
    }
elif payload["action"] == "inspect":
    usage = eh.cumulative_usage(
        path=ledger_path,
        task_id=payload["task_id"],
        claim_id=payload["claim_id"],
    )
    preflight = eh.budget_preflight(
        **common,
        dispatch_id=payload["dispatch_id"],
        dispatch_ceiling=payload["dispatch_ceiling"],
    )
    result = {"usage": usage, "preflight": preflight}
else:
    raise AssertionError(f"unknown action: {payload['action']}")
print(json.dumps(result, sort_keys=True))
"""


def _run_fresh_budget_process(
    ledger_path: Path,
    authority_root: Path,
    payload: dict,
) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _FRESH_BUDGET_PROCESS,
            str(ROOT / "scripts" / "eval_harness.py"),
            str(ledger_path),
            str(authority_root),
            json.dumps(payload),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


_FRESH_ECONOMIC_REPORT_PROCESS = r"""
import importlib.util
import json
import sys
from pathlib import Path

module_path = Path(sys.argv[1])
ledger_path = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("_fresh_economic_harness", module_path)
eh = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = eh
spec.loader.exec_module(eh)
report = eh.report(eh.read_outcomes(ledger_path))
print(json.dumps({
    "token_eligible": report["token_delta"]["eligible_records"],
    "money_eligible": report["monetary_delta"]["eligible_records"],
    "token_reasons": report["token_delta"]["exclusion_reasons"],
    "money_reasons": report["monetary_delta"]["exclusion_reasons"],
}, sort_keys=True))
"""


def _run_fresh_economic_report(
    ledger_path: Path,
    *,
    check: bool = True,
) -> dict | subprocess.CompletedProcess:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _FRESH_ECONOMIC_REPORT_PROCESS,
            str(ROOT / "scripts" / "eval_harness.py"),
            str(ledger_path),
        ],
        check=check,
        capture_output=True,
        text=True,
    )
    if not check:
        return completed
    return json.loads(completed.stdout)


def _record_reserved_economic_pair(
    tmp_path: Path,
    *,
    prefix: str,
    mark_baseline: bool,
    mark_actual: bool,
    actual_status: str = "completed",
) -> tuple[Path, dict, dict]:
    path = tmp_path / f"{prefix}-receipts.jsonl"
    task_id = f"TASK-ECONOMIC-{prefix.upper()}"
    workload_id = f"workload-economic-{prefix}"

    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id=task_id,
        claim_id=None,
        dispatch_id=f"{prefix}-baseline",
        dispatch_ceiling=200,
        task_token_budget=1_000,
        source="auto_dispatch",
    )
    if mark_baseline:
        eh.record_provider_call_start(
            dispatch_id=f"{prefix}-baseline",
            task_id=task_id,
            source="auto_dispatch_provider_run",
            provider="native-codex",
            execution_surface="provider_worker",
            path=path,
            root=tmp_path,
        )
    baseline = eh.record_execution_receipt(
        dispatch_id=f"{prefix}-baseline",
        task_id=task_id,
        workload_id=workload_id,
        provider="native-codex",
        execution_surface="provider_worker",
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
        source="provider_completion",
        status="completed",
        finish_reason="stop",
        path=path,
    )

    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id=task_id,
        claim_id=None,
        dispatch_id=f"{prefix}-actual",
        dispatch_ceiling=200,
        task_token_budget=1_000,
        source="auto_dispatch",
    )
    if mark_actual:
        eh.record_provider_call_start(
            dispatch_id=f"{prefix}-actual",
            task_id=task_id,
            source="auto_dispatch_provider_run",
            provider="native-codex",
            execution_surface="provider_worker",
            path=path,
            root=tmp_path,
        )
    actual_completed = actual_status == "completed"
    actual = eh.record_execution_receipt(
        dispatch_id=f"{prefix}-actual",
        task_id=task_id,
        workload_id=workload_id,
        provider="native-codex",
        execution_surface="provider_worker",
        resolved_model="gpt-5.6-terra",
        resolved_reasoning_effort="low",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="adapter_default:test",
        observed_provider="native-codex",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
        tokens_in=10 if actual_completed else 0,
        tokens_out=5 if actual_completed else 0,
        billed_cost=0.02 if actual_completed else None,
        currency="USD" if actual_completed else None,
        source="provider_completion",
        status=actual_status,
        finish_reason="stop" if actual_completed else actual_status,
        error=(
            None
            if actual_completed
            else "synthetic provider call did not complete"
        ),
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )
    return path, baseline, actual


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
        "tokens_in": baseline_tokens,
        "tokens_out": 0,
        "tokens": baseline_tokens,
        "billed_cost_status": (
            "observed"
            if baseline_billed_cost is not None
            else "unavailable"
        ),
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
        "tokens_in": actual_tokens if actual_tokens_known else None,
        "tokens_out": 0 if actual_tokens_known else None,
        "tokens": actual_tokens,
        "billed_cost_status": (
            "observed"
            if actual_billed_cost is not None
            else "unavailable"
        ),
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


def _validated_execution_rows(records: list[dict]):
    """Attest synthetic execution rows as one complete strict ledger."""
    return eh.ValidatedOutcomeRecords(records, records)


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


@pytest.mark.parametrize(
    (
        "receipt_values",
        "expected_tokens",
        "expected_conservative",
        "expected_committed",
        "next_ceiling",
        "next_allowed",
        "settlement_basis",
    ),
    [
        (
            {
                "source": "provider_completion",
                "status": "completed",
                "token_usage_status": "unavailable",
            },
            0,
            10,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
        (
            {
                "source": "provider_error",
                "status": "error",
                "finish_reason": "error",
                "error": "synthetic provider failure",
                "token_usage_status": "unavailable",
            },
            0,
            10,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
        (
            {
                "source": "native_codex_reply",
                "status": "skipped",
                "finish_reason": "skipped",
                "token_usage_status": "unavailable",
            },
            0,
            10,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
        (
            {
                "source": "provider_completion",
                "status": "completed",
                "tokens_in": 4,
                "token_usage_status": "partial",
            },
            4,
            6,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
        (
            {
                "source": "provider_completion",
                "status": "completed",
                "tokens_in": 4,
                "tokens_out": 0,
            },
            4,
            6,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
        (
            {
                "source": "session_budget_preflight",
                "status": "skipped",
                "finish_reason": "skipped",
                "error": "session budget blocked before provider call",
                "token_usage_status": "unavailable",
            },
            0,
            10,
            10,
            1,
            False,
            "conservative_ceiling",
        ),
    ],
    ids=(
        "completed-unknown",
        "error-unknown",
        "post-dispatch-skip-unknown",
        "partial-usage",
        "observed-usage-without-call-start",
        "generic-pre-provider-skip",
    ),
)
def test_terminal_budget_settlement_survives_fresh_process_restart(
    tmp_path,
    receipt_values,
    expected_tokens,
    expected_conservative,
    expected_committed,
    next_ceiling,
    next_allowed,
    settlement_basis,
):
    path = tmp_path / "receipts.jsonl"
    task_id = "TASK-FRESH-BUDGET"
    claim_id = "CLAIM-FRESH-BUDGET"
    _write_claim_authority(
        tmp_path,
        claim_id=claim_id,
        task_id=task_id,
        task_token_budget=10,
        claim_token_budget=10,
    )

    first = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "settle",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-first",
            "dispatch_ceiling": 10,
            "receipt": receipt_values,
        },
    )
    second = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "inspect",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-second",
            "dispatch_ceiling": next_ceiling,
        },
    )

    assert first["preflight"]["allowed"] is True
    assert first["receipt"]["budget_reservation_status"] == "settled"
    assert first["receipt"]["budget_settlement_basis"] == settlement_basis
    for scope in ("task", "claim"):
        usage = second["usage"][scope]
        assert usage["tokens"] == expected_tokens
        assert usage["reserved_tokens"] == 0
        assert (
            usage["conservative_unobserved_tokens"]
            == expected_conservative
        )
        assert usage["committed_tokens"] == expected_committed
    assert second["preflight"]["allowed"] is next_allowed
    if next_allowed:
        assert second["preflight"]["reason"] == "within_budget"
    else:
        assert second["preflight"]["reason"] == "task_budget_insufficient"


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
    report = eh.report(_validated_execution_rows(recs))
    delta = report["token_delta"]
    assert delta["actual_tokens"] == 350
    assert delta["baseline_tokens"] == 900
    assert delta["saved_tokens"] == 550
    assert delta["saved_rate"] == 0.611
    assert delta["monetary_claim"] is False
    assert report["cost_delta"]["deprecated_alias"] is True


@pytest.mark.parametrize(
    "actual_updates",
    [
        {
            "status": "error",
            "error": "synthetic provider failure",
            "finish_reason": "error",
            "outcome": "gate-error",
        },
        {"status": "skipped", "finish_reason": "skipped"},
        {"status": "pending"},
        {
            "status": "completed",
            "error": "synthetic provider failure",
        },
        {"status": "completed", "outcome": "rejected"},
        {"status": "completed", "finish_reason": "max_tokens"},
        {"status": "completed", "finish_reason": "incomplete"},
        {"status": "completed", "finish_reason": "in_progress"},
        {"status": "completed", "finish_reason": "queued"},
        {"status": "completed", "finish_reason": "requires_action"},
        {"status": "completed", "finish_reason": "unknown_terminal"},
    ],
    ids=(
        "error",
        "skipped",
        "nonterminal",
        "completed-with-error",
        "failed-outcome",
        "failed-finish-reason",
        "incomplete-finish",
        "in-progress-finish",
        "queued-finish",
        "requires-action-finish",
        "unknown-finish",
    ),
)
def test_report_recomputes_actual_execution_success_before_economic_eligibility(
    actual_updates,
):
    baseline, actual = _verified_delta_records(
        "actual-terminal-integrity",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    actual.update(actual_updates)
    actual.update(
        {
            "application_status": "applied",
            "route_status": "effective",
            "route_changed": True,
        }
    )

    result = eh.report(
        _validated_execution_rows([baseline, actual])
    )

    assert result["token_delta"]["eligible_records"] == 0
    assert result["token_delta"]["saved_tokens"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0
    assert (
        result["token_delta"]["exclusion_reasons"][
            "actual_execution_not_successful"
        ]
        == 1
    )


@pytest.mark.parametrize(
    "baseline_updates",
    [
        {
            "status": "error",
            "error": "synthetic baseline failure",
            "finish_reason": "error",
            "outcome": "gate-error",
        },
        {"status": "skipped", "finish_reason": "skipped"},
        {"status": "completed", "error": "synthetic baseline failure"},
        {"status": "completed", "outcome": "rejected"},
        {"status": "completed", "finish_reason": "incomplete"},
        {"status": "completed", "finish_reason": "in_progress"},
        {"status": "completed", "finish_reason": "queued"},
        {"status": "completed", "finish_reason": "requires_action"},
        {"status": "completed", "finish_reason": "unknown_terminal"},
    ],
    ids=(
        "error",
        "skipped",
        "completed-with-error",
        "failed-outcome",
        "incomplete-finish",
        "in-progress-finish",
        "queued-finish",
        "requires-action-finish",
        "unknown-finish",
    ),
)
def test_report_requires_successful_baseline_execution(baseline_updates):
    baseline, actual = _verified_delta_records(
        "baseline-terminal-integrity",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    baseline.update(baseline_updates)

    result = eh.report(
        _validated_execution_rows([baseline, actual])
    )

    assert result["token_delta"]["eligible_records"] == 0
    assert result["token_delta"]["saved_tokens"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0
    assert (
        result["token_delta"]["exclusion_reasons"][
            "baseline_execution_not_successful"
        ]
        == 1
    )


def test_report_rejects_incomplete_actual_token_observation():
    baseline, actual = _verified_delta_records(
        "incomplete-actual-token-observation",
        actual_tokens=15,
        baseline_tokens=100,
    )
    actual.update(
        {
            "actual_tokens_known": True,
            "token_usage_status": "observed",
            "tokens_in": None,
            "tokens_out": None,
        }
    )

    result = eh.report(
        _validated_execution_rows([baseline, actual])
    )["token_delta"]

    assert result["eligible_records"] == 0
    assert result["saved_tokens"] == 0
    assert result["exclusion_reasons"]["actual_token_usage_unavailable"] == 1


def test_report_rejects_incomplete_baseline_token_observation():
    baseline, actual = _verified_delta_records(
        "incomplete-baseline-token-observation",
        actual_tokens=15,
        baseline_tokens=100,
    )
    baseline.update(
        {
            "actual_tokens_known": True,
            "token_usage_status": "observed",
            "tokens_in": 99,
            "tokens_out": 0,
        }
    )

    result = eh.report(
        _validated_execution_rows([baseline, actual])
    )["token_delta"]

    assert result["eligible_records"] == 0
    assert result["saved_tokens"] == 0
    assert result["exclusion_reasons"]["baseline_observation_unavailable"] == 1


@pytest.mark.parametrize(
    ("actual_status", "baseline_status", "expected_reason"),
    [
        ("unavailable", "observed", "actual_billed_cost_unavailable"),
        ("observed", "unavailable", "baseline_billed_cost_unavailable"),
    ],
    ids=("actual-unavailable", "baseline-unavailable"),
)
def test_report_requires_observed_billed_cost_status(
    actual_status,
    baseline_status,
    expected_reason,
):
    baseline, actual = _verified_delta_records(
        f"billed-cost-{actual_status}-{baseline_status}",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    actual["billed_cost_status"] = actual_status
    baseline["billed_cost_status"] = baseline_status

    result = eh.report(
        _validated_execution_rows([baseline, actual])
    )["monetary_delta"]

    assert result["eligible_records"] == 0
    assert result["verified"] is False
    assert result["exclusion_reasons"][expected_reason] == 1


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
    delta = eh.report(_validated_execution_rows(recs))["token_delta"]
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
    delta = eh.report(_validated_execution_rows(recs))["token_delta"]
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

    delta = eh.report(_validated_execution_rows(recs))["token_delta"]
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
        finish_reason="stop",
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
        finish_reason="stop",
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
    forged_report = eh.report(eh.read_outcomes(path))
    # The earlier valid comparison remains eligible; the forged row must not
    # create a second comparison.
    assert forged_report["token_delta"]["eligible_records"] == 1
    assert forged_report["token_delta"]["saved_tokens"] == 80
    assert forged_report["monetary_delta"]["eligible_records"] == 1
    assert (
        forged_report["token_delta"]["exclusion_reasons"][
            "baseline_receipt_unavailable"
        ]
        == 1
    )


def test_finalizer_rejects_unsuccessful_baseline_execution(tmp_path):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-failed",
        task_id="TASK-FAILED-BASELINE",
        workload_id="workload-failed-baseline",
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
        source="provider_error",
        status="error",
        finish_reason="error",
        error="synthetic baseline failure",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-after-failed-baseline",
        task_id="TASK-FAILED-BASELINE",
        workload_id="workload-failed-baseline",
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
        source="provider_completion",
        status="completed",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_execution_not_successful"
    )
    result = eh.report(eh.read_outcomes(path))
    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


@pytest.mark.parametrize(
    "finish_reason",
    (
        "incomplete",
        "in_progress",
        "queued",
        "requires_action",
        "unknown_terminal",
    ),
)
def test_finalizer_rejects_nonterminal_or_unknown_baseline_finish(
    tmp_path,
    finish_reason,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id=f"baseline-{finish_reason}",
        task_id="TASK-NONTERMINAL-BASELINE",
        workload_id=f"workload-{finish_reason}",
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
        source="native_codex_reply",
        status="completed",
        finish_reason=finish_reason,
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id=f"actual-{finish_reason}",
        task_id="TASK-NONTERMINAL-BASELINE",
        workload_id=f"workload-{finish_reason}",
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
        source="native_codex_reply",
        status="completed",
        finish_reason="stop",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_execution_not_successful"
    )


def test_recording_preserves_explicit_empty_actual_finish_and_fails_closed(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-explicit-empty-actual",
        task_id="TASK-EMPTY-ACTUAL",
        workload_id="workload-explicit-empty-actual",
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
    actual = eh.record_execution_receipt(
        dispatch_id="actual-explicit-empty",
        task_id="TASK-EMPTY-ACTUAL",
        workload_id="workload-explicit-empty-actual",
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
        source="native_codex_reply",
        status="completed",
        finish_reason="",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert actual["finish_reason"] == ""
    assert actual["application_status"] == "unverified"
    assert actual["route_status"] == "unverified"
    result = eh.report(eh.read_outcomes(path))
    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


def test_recording_does_not_promote_omitted_finish_to_success(tmp_path):
    path = tmp_path / "receipts.jsonl"

    receipt = eh.record_execution_receipt(
        dispatch_id="actual-omitted-finish",
        task_id="TASK-OMITTED-FINISH",
        provider="native-codex",
        observed_provider="native-codex",
        observed_model="gpt-5.6-terra",
        tokens_in=10,
        tokens_out=5,
        source="native_codex_reply",
        status="completed",
        path=path,
    )

    assert receipt["finish_reason"] is None
    assert receipt["application_status"] == "unverified"
    assert receipt["route_status"] == "unverified"
    result = eh.report(eh.read_outcomes(path))
    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


def test_recording_preserves_explicit_empty_baseline_finish_and_rejects_it(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    baseline = eh.record_execution_receipt(
        dispatch_id="baseline-explicit-empty",
        task_id="TASK-EMPTY-BASELINE",
        workload_id="workload-explicit-empty-baseline",
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
        source="native_codex_reply",
        status="completed",
        finish_reason="",
        path=path,
    )
    actual = eh.record_execution_receipt(
        dispatch_id="actual-after-explicit-empty-baseline",
        task_id="TASK-EMPTY-BASELINE",
        workload_id="workload-explicit-empty-baseline",
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
        source="native_codex_reply",
        status="completed",
        finish_reason="stop",
        baseline_receipt_id=baseline["receipt_id"],
        path=path,
    )

    assert baseline["finish_reason"] == ""
    assert actual["baseline_reference_status"] == "invalid"
    assert actual["baseline_reference_reason"] == (
        "baseline_execution_not_successful"
    )


@pytest.mark.parametrize(
    ("reservation_source", "receipt_source"),
    (
        ("auto_dispatch", "routing_policy"),
        ("auto_dispatch", "budget_preflight"),
        ("auto_dispatch", "deterministic_preflight_blocked"),
        ("auto_dispatch", "deterministic_preflight_complete"),
        ("agent_worker", "session_budget_preflight"),
        ("agent_worker", "claim_preflight"),
        ("auto_dispatch", "session_budget_preflight"),
        ("auto_dispatch", "claim_preflight"),
    ),
)
def test_generic_skip_receipt_cannot_release_reserved_budget_across_restart(
    tmp_path,
    reservation_source,
    receipt_source,
):
    path = tmp_path / "receipts.jsonl"
    task_id = "TASK-GENERIC-SKIP"
    claim_id = "CLAIM-GENERIC-SKIP"
    _write_claim_authority(
        tmp_path,
        claim_id=claim_id,
        task_id=task_id,
        task_token_budget=10,
        claim_token_budget=10,
    )

    first = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "settle",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-first",
            "dispatch_ceiling": 10,
            "reservation_source": reservation_source,
            "receipt": {
                "source": receipt_source,
                "status": "skipped",
                "finish_reason": "skipped",
                "error": "synthetic no-call claim",
                "token_usage_status": "unavailable",
            },
        },
    )
    second = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "inspect",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-second",
            "dispatch_ceiling": 1,
        },
    )

    assert first["preflight"]["allowed"] is True
    assert (
        first["receipt"]["budget_settlement_basis"]
        == "conservative_ceiling"
    )
    for scope in ("task", "claim"):
        usage = second["usage"][scope]
        assert usage["pre_provider_releases"] == 0
        assert usage["conservative_unobserved_tokens"] == 10
        assert usage["committed_tokens"] == 10
    assert second["preflight"]["allowed"] is False
    assert second["preflight"]["reason"] == "task_budget_insufficient"


@pytest.mark.parametrize(
    "receipt_source",
    ("session_budget_preflight", "claim_preflight"),
)
def test_dedicated_no_call_settlement_releases_exact_reservation_after_restart(
    tmp_path,
    receipt_source,
):
    path = tmp_path / "receipts.jsonl"
    task_id = "TASK-DEDICATED-NO-CALL"
    claim_id = "CLAIM-DEDICATED-NO-CALL"
    _write_claim_authority(
        tmp_path,
        claim_id=claim_id,
        task_id=task_id,
        task_token_budget=10,
        claim_token_budget=10,
    )

    first = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "settle_no_call",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-first",
            "dispatch_ceiling": 10,
            "reservation_source": "auto_dispatch",
            "receipt": {
                "source": receipt_source,
                "status": "skipped",
                "finish_reason": "skipped",
                "error": "synthetic post-reservation no-call",
                "token_usage_status": "unavailable",
            },
        },
    )
    second = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "inspect",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-second",
            "dispatch_ceiling": 10,
        },
    )

    assert first["preflight"]["allowed"] is True
    receipt = first["receipt"]
    assert receipt["budget_settlement_basis"] == "pre_provider_skip"
    assert receipt["budget_no_provider_settlement_id"].startswith(
        "no-provider-settlement-"
    )
    for scope in ("task", "claim"):
        usage = second["usage"][scope]
        assert usage["pre_provider_releases"] == 1
        assert usage["conservative_unobserved_tokens"] == 0
        assert usage["committed_tokens"] == 0
    assert second["preflight"]["allowed"] is True
    assert second["preflight"]["reason"] == "within_budget"

    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        eh.BUDGET_RESERVATION_SCHEMA,
        eh.NO_PROVIDER_SETTLEMENT_SCHEMA,
        eh.EXECUTION_RECEIPT_SCHEMA,
    ]
    assert eh.read_outcomes(path) == [raw[-1]]


def test_dedicated_no_call_settlement_rejects_invalid_transition_atomically(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-BAD-TRANSITION",
        claim_id=None,
        dispatch_id="dispatch-bad-transition",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="agent_worker",
    )
    assert preflight["allowed"] is True

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="invalid no-provider settlement transition",
    ):
        eh.record_pre_provider_skip_receipt(
            dispatch_id="dispatch-bad-transition",
            task_id="TASK-BAD-TRANSITION",
            source="session_budget_preflight",
            status="skipped",
            finish_reason="skipped",
            path=path,
        )

    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        eh.BUDGET_RESERVATION_SCHEMA
    ]
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-BAD-TRANSITION",
    )
    assert usage["task"]["reserved_tokens"] == 10
    assert usage["task"]["committed_tokens"] == 10


def test_dedicated_no_call_settlement_rejects_provider_observation_atomically(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-NO-CALL-OBSERVED",
        claim_id=None,
        dispatch_id="dispatch-no-call-observed",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    assert preflight["allowed"] is True

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="lacks a valid no-call receipt",
    ):
        eh.record_pre_provider_skip_receipt(
            dispatch_id="dispatch-no-call-observed",
            task_id="TASK-NO-CALL-OBSERVED",
            source="session_budget_preflight",
            status="skipped",
            finish_reason="skipped",
            observed_provider="native-codex",
            path=path,
        )

    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        eh.BUDGET_RESERVATION_SCHEMA
    ]
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-NO-CALL-OBSERVED",
    )
    assert usage["task"]["reserved_tokens"] == 10
    assert usage["task"]["committed_tokens"] == 10


def test_no_call_settlement_detects_reservation_provenance_tampering(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-TAMPERED-SETTLEMENT",
        claim_id=None,
        dispatch_id="dispatch-tampered-settlement",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    assert preflight["allowed"] is True
    eh.record_pre_provider_skip_receipt(
        dispatch_id="dispatch-tampered-settlement",
        task_id="TASK-TAMPERED-SETTLEMENT",
        source="session_budget_preflight",
        status="skipped",
        finish_reason="skipped",
        path=path,
    )
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    raw[0]["reserved_tokens"] = 9
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="reservation fingerprint mismatch",
    ):
        eh.cumulative_usage(
            path=path,
            task_id="TASK-TAMPERED-SETTLEMENT",
        )


def test_forged_stored_settlement_basis_is_a_ledger_integrity_failure(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-FORGED-SETTLEMENT-BASIS",
        claim_id=None,
        dispatch_id="dispatch-forged-basis",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    assert preflight["allowed"] is True
    eh.record_execution_receipt(
        dispatch_id="dispatch-forged-basis",
        task_id="TASK-FORGED-SETTLEMENT-BASIS",
        source="session_budget_preflight",
        status="skipped",
        finish_reason="skipped",
        token_usage_status="unavailable",
        budget_preflight_result=preflight,
        path=path,
    )
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    raw[-1]["budget_settlement_basis"] = "pre_provider_skip"
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="derived budget_settlement_basis mismatch",
    ):
        eh.cumulative_usage(
            path=path,
            task_id="TASK-FORGED-SETTLEMENT-BASIS",
        )


@pytest.mark.parametrize(
    ("status", "finish_reason", "error"),
    (
        ("completed", "stop", None),
        ("error", "error", "synthetic provider error"),
        ("skipped", "skipped", "synthetic spawn did not occur"),
    ),
)
def test_observed_usage_without_provider_call_start_keeps_full_commitment(
    tmp_path,
    status,
    finish_reason,
    error,
):
    path = tmp_path / "receipts.jsonl"
    task_id = f"TASK-NO-CALL-START-{status}"
    claim_id = f"CLAIM-NO-CALL-START-{status}"
    _write_claim_authority(
        tmp_path,
        claim_id=claim_id,
        task_id=task_id,
        task_token_budget=10,
        claim_token_budget=10,
    )

    first = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "settle",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-first",
            "dispatch_ceiling": 10,
            "reservation_source": "auto_dispatch",
            "receipt": {
                "provider": "dummy",
                "execution_surface": "provider_worker",
                "source": "provider_completion",
                "status": status,
                "finish_reason": finish_reason,
                "error": error,
                "tokens_in": 0,
                "tokens_out": 0,
            },
        },
    )
    second = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "inspect",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-second",
            "dispatch_ceiling": 1,
        },
    )

    assert (
        first["receipt"]["budget_settlement_basis"]
        == "conservative_ceiling"
    )
    for scope in ("task", "claim"):
        assert second["usage"][scope]["committed_tokens"] == 10
        assert (
            second["usage"][scope]["conservative_unobserved_tokens"]
            == 10
        )
    assert second["preflight"]["allowed"] is False


def test_matching_provider_call_start_allows_observed_usage_after_restart(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    task_id = "TASK-VALID-CALL-START"
    claim_id = "CLAIM-VALID-CALL-START"
    _write_claim_authority(
        tmp_path,
        claim_id=claim_id,
        task_id=task_id,
        task_token_budget=10,
        claim_token_budget=10,
    )

    first = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "settle",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-first",
            "dispatch_ceiling": 10,
            "reservation_source": "auto_dispatch",
            "call_start": {
                "source": "auto_dispatch_provider_run",
                "provider": "dummy",
                "execution_surface": "provider_worker",
            },
            "receipt": {
                "provider": "dummy",
                "execution_surface": "provider_worker",
                "source": "provider_completion",
                "status": "completed",
                "finish_reason": "stop",
                "tokens_in": 4,
                "tokens_out": 0,
            },
        },
    )
    second = _run_fresh_budget_process(
        path,
        tmp_path,
        {
            "action": "inspect",
            "task_id": task_id,
            "claim_id": claim_id,
            "dispatch_id": "dispatch-second",
            "dispatch_ceiling": 6,
        },
    )

    assert first["call_start"]["schema"] == eh.PROVIDER_CALL_START_SCHEMA
    assert first["receipt"]["budget_settlement_basis"] == "observed_usage"
    for scope in ("task", "claim"):
        assert second["usage"][scope]["tokens"] == 4
        assert second["usage"][scope]["committed_tokens"] == 4
    assert second["preflight"]["allowed"] is True


def test_provider_call_start_without_receipt_stays_reserved_after_restart(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-CALL-START-CRASH",
        claim_id=None,
        dispatch_id="dispatch-call-start-crash",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="agent_worker",
    )
    assert preflight["allowed"] is True
    marker = eh.record_provider_call_start(
        dispatch_id="dispatch-call-start-crash",
        task_id="TASK-CALL-START-CRASH",
        source="agent_worker_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
    )

    assert marker["schema"] == eh.PROVIDER_CALL_START_SCHEMA
    assert eh.read_outcomes(path) == []
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-CALL-START-CRASH",
    )
    assert usage["task"]["pending_reservations"] == 1
    assert usage["task"]["reserved_tokens"] == 10
    assert usage["task"]["committed_tokens"] == 10


def test_provider_call_start_plus_skipped_zero_receipt_stays_conservative(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    preflight = eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKED-SKIP",
        claim_id=None,
        dispatch_id="dispatch-marked-skip",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    assert preflight["allowed"] is True
    eh.record_provider_call_start(
        dispatch_id="dispatch-marked-skip",
        task_id="TASK-MARKED-SKIP",
        source="auto_dispatch_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )
    receipt = eh.record_execution_receipt(
        dispatch_id="dispatch-marked-skip",
        task_id="TASK-MARKED-SKIP",
        provider="dummy",
        execution_surface="provider_worker",
        source="provider_completion",
        status="skipped",
        finish_reason="skipped",
        error="synthetic provider call did not complete",
        tokens_in=0,
        tokens_out=0,
        path=path,
    )

    assert receipt["budget_settlement_basis"] == "conservative_ceiling"
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-MARKED-SKIP",
    )
    assert usage["task"]["committed_tokens"] == 10
    assert usage["task"]["conservative_unobserved_tokens"] == 10


def test_provider_error_with_matching_call_start_can_settle_observed_usage(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKED-ERROR",
        claim_id=None,
        dispatch_id="dispatch-marked-error",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    eh.record_provider_call_start(
        dispatch_id="dispatch-marked-error",
        task_id="TASK-MARKED-ERROR",
        source="auto_dispatch_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )
    receipt = eh.record_execution_receipt(
        dispatch_id="dispatch-marked-error",
        task_id="TASK-MARKED-ERROR",
        provider="dummy",
        execution_surface="provider_worker",
        source="provider_error",
        status="error",
        finish_reason="error",
        error="synthetic provider error with usage",
        tokens_in=2,
        tokens_out=1,
        path=path,
    )

    assert receipt["budget_settlement_basis"] == "observed_usage"
    usage = eh.cumulative_usage(
        path=path,
        task_id="TASK-MARKED-ERROR",
    )
    assert usage["task"]["tokens"] == 3
    assert usage["task"]["committed_tokens"] == 3


def test_provider_call_start_rejects_mismatched_result_atomically(tmp_path):
    path = tmp_path / "receipts.jsonl"
    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKER-MISMATCH",
        claim_id=None,
        dispatch_id="dispatch-marker-mismatch",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    eh.record_provider_call_start(
        dispatch_id="dispatch-marker-mismatch",
        task_id="TASK-MARKER-MISMATCH",
        source="auto_dispatch_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="receipt provider mismatch",
    ):
        eh.record_execution_receipt(
            dispatch_id="dispatch-marker-mismatch",
            task_id="TASK-MARKER-MISMATCH",
            provider="other-provider",
            execution_surface="provider_worker",
            source="provider_completion",
            status="completed",
            finish_reason="stop",
            tokens_in=2,
            tokens_out=1,
            path=path,
        )

    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        eh.BUDGET_RESERVATION_SCHEMA,
        eh.PROVIDER_CALL_START_SCHEMA,
    ]


def test_provider_call_start_and_no_call_settlement_are_mutually_exclusive(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKER-NO-CALL-CONFLICT",
        claim_id=None,
        dispatch_id="dispatch-marker-no-call-conflict",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    eh.record_provider_call_start(
        dispatch_id="dispatch-marker-no-call-conflict",
        task_id="TASK-MARKER-NO-CALL-CONFLICT",
        source="auto_dispatch_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )

    with pytest.raises(
        eh.ReceiptConflictError,
        match="conflicts with provider call-start",
    ):
        eh.record_pre_provider_skip_receipt(
            dispatch_id="dispatch-marker-no-call-conflict",
            task_id="TASK-MARKER-NO-CALL-CONFLICT",
            source="session_budget_preflight",
            status="skipped",
            finish_reason="skipped",
            path=path,
        )

    assert eh.read_outcomes(path) == []
    assert eh.cumulative_usage(
        path=path,
        task_id="TASK-MARKER-NO-CALL-CONFLICT",
    )["task"]["committed_tokens"] == 10


def test_provider_call_start_detects_tampering_and_conflicting_replay(
    tmp_path,
):
    path = tmp_path / "receipts.jsonl"
    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKER-TAMPER",
        claim_id=None,
        dispatch_id="dispatch-marker-tamper",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="agent_worker",
    )
    marker = eh.record_provider_call_start(
        dispatch_id="dispatch-marker-tamper",
        task_id="TASK-MARKER-TAMPER",
        source="agent_worker_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )
    same = eh.record_provider_call_start(
        dispatch_id="dispatch-marker-tamper",
        task_id="TASK-MARKER-TAMPER",
        source="agent_worker_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )
    assert same["call_start_id"] == marker["call_start_id"]
    with pytest.raises(
        eh.ReceiptConflictError,
        match="immutable provider call-start",
    ):
        eh.record_provider_call_start(
            dispatch_id="dispatch-marker-tamper",
            task_id="TASK-MARKER-TAMPER",
            source="agent_worker_provider_run",
            provider="other-provider",
            execution_surface="provider_worker",
            path=path,
            root=tmp_path,
        )

    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    raw[-1]["reservation_fingerprint"] = "tampered"
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="reservation fingerprint mismatch",
    ):
        eh.cumulative_usage(
            path=path,
            task_id="TASK-MARKER-TAMPER",
        )


@pytest.mark.parametrize(
    ("field", "tampered"),
    (
        ("schema", "agent-runtime-provider-call-start/tampered"),
        ("immutable", False),
        ("call_start_id", "provider-call-start-tampered"),
        ("dispatch_id", "dispatch-tampered"),
        ("task_id", "TASK-TAMPERED"),
        ("claim_id", "CLAIM-TAMPERED"),
        ("reservation_id", "reservation-tampered"),
        ("reservation_source", "agent_worker"),
        ("source", "agent_worker_provider_run"),
        ("status", "pending"),
        ("provider", "other-provider"),
        ("execution_surface", "other-surface"),
        ("reservation_fingerprint", "tampered"),
        ("budget_authority_fingerprint", "tampered"),
    ),
)
def test_provider_call_start_rejects_single_field_tampering(
    tmp_path,
    field,
    tampered,
):
    path = tmp_path / "receipts.jsonl"
    eh.reserve_dispatch_budget(
        path=path,
        root=tmp_path,
        task_id="TASK-MARKER-FIELD-TAMPER",
        claim_id=None,
        dispatch_id="dispatch-marker-field-tamper",
        dispatch_ceiling=10,
        task_token_budget=10,
        source="auto_dispatch",
    )
    eh.record_provider_call_start(
        dispatch_id="dispatch-marker-field-tamper",
        task_id="TASK-MARKER-FIELD-TAMPER",
        source="auto_dispatch_provider_run",
        provider="dummy",
        execution_surface="provider_worker",
        path=path,
        root=tmp_path,
    )
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    raw[-1][field] = tampered
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(eh.ReceiptIntegrityError):
        eh.cumulative_usage(
            path=path,
            task_id="TASK-MARKER-FIELD-TAMPER",
        )


@pytest.mark.parametrize(
    ("mark_baseline", "mark_actual", "expected_reason"),
    (
        (False, False, "baseline_provider_call_provenance_unverified"),
        (False, True, "baseline_provider_call_provenance_unverified"),
        (True, False, "actual_provider_call_provenance_unverified"),
    ),
    ids=("both-missing", "baseline-missing", "actual-missing"),
)
def test_reserved_economic_pair_requires_both_call_markers_after_restart(
    tmp_path,
    mark_baseline,
    mark_actual,
    expected_reason,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix=f"missing-{mark_baseline}-{mark_actual}",
        mark_baseline=mark_baseline,
        mark_actual=mark_actual,
    )

    result = _run_fresh_economic_report(path)

    assert result["token_eligible"] == 0
    assert result["money_eligible"] == 0
    assert result["token_reasons"][expected_reason] == 1
    assert result["money_reasons"][expected_reason] == 1


def test_reserved_economic_pair_with_both_markers_survives_restart(tmp_path):
    path, baseline, actual = _record_reserved_economic_pair(
        tmp_path,
        prefix="both-marked",
        mark_baseline=True,
        mark_actual=True,
    )

    result = _run_fresh_economic_report(path)

    assert baseline["budget_settlement_basis"] == "observed_usage"
    assert actual["budget_settlement_basis"] == "observed_usage"
    assert result["token_eligible"] == 1
    assert result["money_eligible"] == 1


def test_reserved_skipped_result_with_marker_is_ineligible_after_restart(
    tmp_path,
):
    path, _, actual = _record_reserved_economic_pair(
        tmp_path,
        prefix="marked-skipped-economic",
        mark_baseline=True,
        mark_actual=True,
        actual_status="skipped",
    )

    result = _run_fresh_economic_report(path)

    assert actual["budget_settlement_basis"] == "conservative_ceiling"
    assert result["token_eligible"] == 0
    assert result["money_eligible"] == 0
    assert result["token_reasons"]["actual_execution_not_successful"] == 1


def test_reserved_rows_copied_without_validated_ledger_context_fail_closed(
    tmp_path,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix="copied-context",
        mark_baseline=True,
        mark_actual=True,
    )
    validated_rows = eh.read_outcomes(path)

    validated = eh.report(validated_rows)
    copied = eh.report(list(validated_rows))

    assert validated["token_delta"]["eligible_records"] == 1
    assert validated["monetary_delta"]["eligible_records"] == 1
    assert copied["token_delta"]["eligible_records"] == 0
    assert copied["monetary_delta"]["eligible_records"] == 0
    assert (
        copied["token_delta"]["exclusion_reasons"][
            "baseline_provider_call_provenance_unverified"
        ]
        == 1
    )


def test_unreserved_legacy_pair_remains_economically_compatible(tmp_path):
    baseline, actual = _verified_delta_records(
        "unreserved-compatibility",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    path = tmp_path / "unreserved-legacy.jsonl"
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True) + "\n"
            for row in (baseline, actual)
        ),
        encoding="utf-8",
    )

    result = eh.report(eh.read_outcomes(path))

    assert result["token_delta"]["eligible_records"] == 1
    assert result["monetary_delta"]["eligible_records"] == 1


def test_plain_execution_receipts_cannot_self_declare_legacy_compatibility():
    baseline, actual = _verified_delta_records(
        "plain-list-unreserved",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )

    result = eh.report([baseline, actual])

    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0
    assert (
        result["token_delta"]["exclusion_reasons"][
            "baseline_provider_call_provenance_unverified"
        ]
        == 1
    )


def test_reserved_rows_cannot_strip_derived_fields_to_claim_legacy_status(
    tmp_path,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix="copy-strip-derived",
        mark_baseline=True,
        mark_actual=True,
    )
    copied = [dict(row) for row in eh.read_outcomes(path)]
    for row in copied:
        for field in (
            "budget_reservation_id",
            "budget_no_provider_settlement_id",
            "budget_provider_call_start_id",
            "budget_reservation_status",
            "budget_settlement_basis",
        ):
            row.pop(field, None)

    result = eh.report(copied)

    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0
    assert (
        result["token_delta"]["exclusion_reasons"][
            "baseline_provider_call_provenance_unverified"
        ]
        == 1
    )


@pytest.mark.parametrize(
    ("target", "updates"),
    (
        ("actual", {"tokens_in": 1, "tokens_out": 0, "tokens": 1}),
        ("actual", {"billed_cost": 0.0}),
        ("actual", {"currency": "EUR"}),
        ("actual", {"provider": "mutated-provider"}),
        ("actual", {"execution_surface": "mutated-surface"}),
        ("actual", {"observed_provider": "mutated-provider"}),
        ("actual", {"observed_model": "gpt-5.6-luna"}),
        ("actual", {"observed_reasoning_effort": "medium"}),
        ("actual", {"resolved_model": "gpt-5.6-luna"}),
        ("actual", {"resolved_reasoning_effort": "medium"}),
        ("actual", {"resolved_model_source": "mutated-source"}),
        ("actual", {"resolved_reasoning_source": "mutated-source"}),
        ("actual", {"actual_tokens_known": False}),
        ("actual", {"token_usage_status": "unavailable"}),
        ("actual", {"billed_cost_status": "unavailable"}),
        ("actual", {"status": "error"}),
        ("actual", {"error": "mutated-error"}),
        ("actual", {"finish_reason": "success"}),
        ("actual", {"outcome": "completed"}),
        ("actual", {"task_id": "TASK-MUTATED"}),
        ("actual", {"claim_id": "CLAIM-MUTATED"}),
        ("actual", {"workload_id": "mutated-workload"}),
        ("actual", {"baseline_receipt_id": "mutated-baseline-id"}),
        ("actual", {"baseline_model": "mutated-baseline-model"}),
        ("actual", {"baseline_reasoning_effort": "max"}),
        ("actual", {"route_changed": False}),
        ("actual", {"model_changed": False}),
        ("actual", {"application_status": "not_applied"}),
        ("actual", {"route_status": "not_applied"}),
        ("actual", {"source": "provider_error"}),
        ("actual", {"budget_reservation_id": "reservation-mutated"}),
        (
            "actual",
            {"budget_provider_call_start_id": "provider-call-start-mutated"},
        ),
        ("actual", {"budget_reservation_status": "pending"}),
        ("actual", {"budget_settlement_basis": "conservative_ceiling"}),
        ("actual", {"dispatch_id": "mutated-actual-dispatch"}),
        ("actual", {"receipt_id": "mutated-actual-receipt"}),
        ("actual", {"immutable": False}),
        ("baseline", {"tokens_in": 1, "tokens_out": 0, "tokens": 1}),
        ("baseline", {"billed_cost": 0.0}),
        ("baseline", {"currency": "EUR"}),
        ("baseline", {"provider": "mutated-provider"}),
        ("baseline", {"execution_surface": "mutated-surface"}),
        ("baseline", {"observed_provider": "mutated-provider"}),
        ("baseline", {"observed_model": "gpt-5.6-max"}),
        ("baseline", {"observed_reasoning_effort": "max"}),
        ("baseline", {"resolved_model": "gpt-5.6-max"}),
        ("baseline", {"resolved_reasoning_effort": "max"}),
        ("baseline", {"resolved_model_source": "mutated-source"}),
        ("baseline", {"resolved_reasoning_source": "mutated-source"}),
        ("baseline", {"actual_tokens_known": False}),
        ("baseline", {"token_usage_status": "unavailable"}),
        ("baseline", {"billed_cost_status": "unavailable"}),
        ("baseline", {"status": "error"}),
        ("baseline", {"error": "mutated-error"}),
        ("baseline", {"finish_reason": "success"}),
        ("baseline", {"outcome": "completed"}),
        ("baseline", {"task_id": "TASK-MUTATED"}),
        ("baseline", {"claim_id": "CLAIM-MUTATED"}),
        ("baseline", {"workload_id": "mutated-workload"}),
        ("baseline", {"source": "provider_error"}),
        ("baseline", {"budget_reservation_id": "reservation-mutated"}),
        (
            "baseline",
            {"budget_provider_call_start_id": "provider-call-start-mutated"},
        ),
        ("baseline", {"budget_reservation_status": "pending"}),
        ("baseline", {"budget_settlement_basis": "conservative_ceiling"}),
        ("baseline", {"dispatch_id": "mutated-baseline-dispatch"}),
        ("baseline", {"receipt_id": "mutated-baseline-receipt"}),
        ("baseline", {"immutable": False}),
    ),
)
def test_post_read_receipt_mutation_invalidates_economic_attestation(
    tmp_path,
    target,
    updates,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix=f"mutate-{target}-{len(updates)}",
        mark_baseline=True,
        mark_actual=True,
    )
    rows = eh.read_outcomes(path)
    baseline, actual = rows
    (baseline if target == "baseline" else actual).update(updates)

    result = eh.report(rows)

    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


def test_validated_outcome_constructor_requires_exact_ledger_membership():
    baseline, actual = _verified_delta_records(
        "constructor-membership",
        actual_tokens=15,
        baseline_tokens=100,
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="outcome rows do not match validated ledger",
    ):
        eh.ValidatedOutcomeRecords([baseline], [baseline, actual])


def test_validated_outcome_constructor_validates_complete_ledger():
    baseline, actual = _verified_delta_records(
        "constructor-ledger-integrity",
        actual_tokens=15,
        baseline_tokens=100,
    )
    actual["dispatch_id"] = baseline["dispatch_id"]

    with pytest.raises(eh.ReceiptIntegrityError, match="duplicate dispatch_id"):
        eh.ValidatedOutcomeRecords([baseline, actual], [baseline, actual])


def test_direct_validated_collection_binds_complete_receipt_value():
    baseline, actual = _verified_delta_records(
        "constructor-receipt-binding",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )
    before = eh.report(rows)
    actual.update({"tokens_in": 1, "tokens_out": 0, "tokens": 1})
    after = eh.report(rows)

    assert before["token_delta"]["eligible_records"] == 1
    assert before["monetary_delta"]["eligible_records"] == 1
    assert after["token_delta"]["eligible_records"] == 0
    assert after["monetary_delta"]["eligible_records"] == 0


def test_validated_collection_snapshots_hidden_provenance_records(tmp_path):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix="hidden-provenance-snapshot",
        mark_baseline=True,
        mark_actual=True,
    )
    ledger = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    outcomes = [
        row
        for row in ledger
        if row.get("schema")
        not in {
            eh.BUDGET_RESERVATION_SCHEMA,
            eh.NO_PROVIDER_SETTLEMENT_SCHEMA,
            eh.PROVIDER_CALL_START_SCHEMA,
        }
    ]
    rows = eh.ValidatedOutcomeRecords(outcomes, ledger)
    before = eh.report(rows)
    for row in ledger:
        if row.get("schema") == eh.BUDGET_RESERVATION_SCHEMA:
            row["reserved_tokens"] = 1
        elif row.get("schema") == eh.PROVIDER_CALL_START_SCHEMA:
            row["provider"] = "mutated-provider"
    after = eh.report(rows)

    assert before["token_delta"]["eligible_records"] == 1
    assert before["monetary_delta"]["eligible_records"] == 1
    assert after["token_delta"]["eligible_records"] == 1
    assert after["monetary_delta"]["eligible_records"] == 1


def _mutate_validated_collection(rows, operation, *, direct):
    baseline, actual = rows
    target = list if direct else type(rows)
    if operation == "init":
        target.__init__(rows, [baseline, actual, actual])
    elif operation == "append":
        target.append(rows, actual)
    elif operation == "extend":
        target.extend(rows, [actual, actual])
    elif operation == "insert":
        target.insert(rows, 0, actual)
    elif operation == "iadd":
        target.__iadd__(rows, [actual])
    elif operation == "imul":
        target.__imul__(rows, 2)
    elif operation == "setitem":
        target.__setitem__(rows, 1, baseline)
    elif operation == "setslice":
        target.__setitem__(rows, slice(1, 2), [actual, actual])
    elif operation == "delitem":
        target.__delitem__(rows, 0)
    elif operation == "delslice":
        target.__delitem__(rows, slice(0, 1))
    elif operation == "pop":
        target.pop(rows, 0)
    elif operation == "remove":
        target.remove(rows, baseline)
    elif operation == "clear":
        target.clear(rows)
    elif operation == "reverse":
        target.reverse(rows)
    elif operation == "sort":
        target.sort(
            rows,
            key=lambda row: str(row.get("receipt_id") or ""),
        )
    else:  # pragma: no cover - protects the test matrix itself
        raise AssertionError(f"unknown collection mutation: {operation}")


_VALIDATED_COLLECTION_MUTATIONS = (
    "append",
    "extend",
    "insert",
    "iadd",
    "imul",
    "setitem",
    "setslice",
    "delitem",
    "delslice",
    "pop",
    "remove",
    "clear",
    "reverse",
    "sort",
)
_DIRECT_VALIDATED_COLLECTION_MUTATIONS = (
    "init",
    *_VALIDATED_COLLECTION_MUTATIONS,
)


@pytest.mark.parametrize("operation", _VALIDATED_COLLECTION_MUTATIONS)
def test_validated_collection_rejects_structural_mutation(operation):
    baseline, actual = _verified_delta_records(
        f"sealed-ordinary-{operation}",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="validated outcome collection is immutable",
    ):
        _mutate_validated_collection(rows, operation, direct=False)


@pytest.mark.parametrize(
    "operation",
    _DIRECT_VALIDATED_COLLECTION_MUTATIONS,
)
def test_direct_list_mutation_invalidates_collection_attestation(operation):
    baseline, actual = _verified_delta_records(
        f"sealed-direct-{operation}",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )
    _mutate_validated_collection(rows, operation, direct=True)

    result = eh.report(rows)

    assert result["token_delta"]["eligible_records"] == 0
    assert result["token_delta"]["saved_tokens"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["verified"] is False


def test_validated_collection_cannot_be_reinitialized():
    baseline, actual = _verified_delta_records(
        "sealed-reinitialization",
        actual_tokens=15,
        baseline_tokens=100,
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )

    with pytest.raises(
        eh.ReceiptIntegrityError,
        match="validated outcome attestation is sealed",
    ):
        rows.__init__(
            [baseline, actual],
            [baseline, actual],
        )


@pytest.mark.parametrize(
    "operation",
    ("assign", "object_assign", "delete", "object_delete"),
)
def test_validated_collection_provenance_authority_cannot_be_replaced(
    operation,
):
    baseline, actual = _verified_delta_records(
        f"sealed-provenance-{operation}",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )
    original = getattr(rows, "_economic_provenance", {})
    actual.update(
        {
            "tokens_in": 1,
            "tokens_out": 0,
            "tokens": 1,
            "billed_cost": 0.0,
        }
    )
    if original:
        original_entry = original[id(actual)]
        forged_entry = (
            eh._record_attestation_digest(actual),
            *original_entry[1:],
        )
        forged = MappingProxyType(
            {
                id(baseline): original[id(baseline)],
                id(actual): forged_entry,
            }
        )
    else:
        forged = MappingProxyType({})

    with pytest.raises(
        (AttributeError, eh.ReceiptIntegrityError),
        match="validated outcome attestation is sealed|"
        "has no attribute|read-only",
    ):
        if operation == "assign":
            rows._economic_provenance = forged
        elif operation == "object_assign":
            object.__setattr__(rows, "_economic_provenance", forged)
        elif operation == "delete":
            del rows._economic_provenance
        else:
            object.__delattr__(rows, "_economic_provenance")

    result = eh.report(rows)
    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


@pytest.mark.parametrize(
    "attribute",
    (
        "_economic_provenance",
        "_ValidatedOutcomeRecords__attestation",
        "_ValidatedOutcomeRecords__sealed",
    ),
)
def test_validated_collection_has_no_replaceable_attestation_slot(attribute):
    baseline, actual = _verified_delta_records(
        f"sealed-instance-slot-{attribute}",
        actual_tokens=15,
        baseline_tokens=100,
    )
    rows = eh.ValidatedOutcomeRecords(
        [baseline, actual],
        [baseline, actual],
    )

    with pytest.raises(
        (AttributeError, eh.ReceiptIntegrityError),
        match="validated outcome attestation is sealed|"
        "has no attribute|read-only",
    ):
        object.__setattr__(rows, attribute, ())


def test_validated_collection_subclass_cannot_override_report_authority():
    forged = MappingProxyType({})

    class ForgedValidatedRows(eh.ValidatedOutcomeRecords):
        def _validated_report_inputs(self):
            return self, forged

    baseline, actual = _verified_delta_records(
        "sealed-subclass-authority",
        actual_tokens=15,
        baseline_tokens=100,
        actual_billed_cost=0.02,
        actual_currency="USD",
        baseline_billed_cost=0.10,
        baseline_currency="USD",
    )
    rows = ForgedValidatedRows(
        [baseline, actual],
        [baseline, actual],
    )
    _, original = eh.ValidatedOutcomeRecords._validated_report_inputs(rows)
    actual.update(
        {
            "tokens_in": 1,
            "tokens_out": 0,
            "tokens": 1,
            "billed_cost": 0.0,
        }
    )
    forged = MappingProxyType(
        {
            id(baseline): original[id(baseline)],
            id(actual): (
                eh._record_attestation_digest(actual),
                *original[id(actual)][1:],
            ),
        }
    )

    result = eh.report(rows)

    assert result["token_delta"]["eligible_records"] == 0
    assert result["monetary_delta"]["eligible_records"] == 0


@pytest.mark.parametrize(
    ("field", "tampered"),
    (
        ("budget_reservation_id", "reservation-forged"),
        ("budget_reservation_status", "not_required_or_unreserved"),
        ("budget_settlement_basis", "conservative_ceiling"),
        ("budget_provider_call_start_id", "provider-call-start-forged"),
    ),
)
def test_fresh_process_rejects_forged_reserved_receipt_derivation(
    tmp_path,
    field,
    tampered,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix=f"forged-{field}",
        mark_baseline=True,
        mark_actual=True,
    )
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    actual = next(
        row
        for row in raw
        if row.get("schema") == eh.EXECUTION_RECEIPT_SCHEMA
        and str(row.get("dispatch_id") or "").endswith("-actual")
    )
    actual[field] = tampered
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )

    completed = _run_fresh_economic_report(path, check=False)

    assert completed.returncode != 0
    assert "ReceiptIntegrityError" in completed.stderr


@pytest.mark.parametrize(
    ("mutation", "field", "tampered"),
    (
        ("orphan", None, None),
        ("field", "reservation_id", "reservation-mismatched"),
        ("field", "budget_authority_fingerprint", "authority-mismatched"),
        ("field", "provider", "wrong-provider"),
        ("field", "execution_surface", "wrong-surface"),
        ("field", "source", "agent_worker_provider_run"),
    ),
    ids=(
        "orphan-marker",
        "reservation-mismatch",
        "authority-mismatch",
        "wrong-provider",
        "wrong-surface",
        "wrong-transition",
    ),
)
def test_fresh_process_rejects_invalid_economic_call_marker(
    tmp_path,
    mutation,
    field,
    tampered,
):
    path, _, _ = _record_reserved_economic_pair(
        tmp_path,
        prefix=f"invalid-marker-{field or mutation}",
        mark_baseline=True,
        mark_actual=True,
    )
    raw = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    actual_dispatch = next(
        row["dispatch_id"]
        for row in raw
        if row.get("schema") == eh.EXECUTION_RECEIPT_SCHEMA
        and str(row.get("dispatch_id") or "").endswith("-actual")
    )
    if mutation == "orphan":
        raw = [
            row
            for row in raw
            if not (
                row.get("schema") == eh.BUDGET_RESERVATION_SCHEMA
                and row.get("dispatch_id") == actual_dispatch
            )
        ]
    else:
        marker = next(
            row
            for row in raw
            if row.get("schema") == eh.PROVIDER_CALL_START_SCHEMA
            and row.get("dispatch_id") == actual_dispatch
        )
        marker[field] = tampered
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in raw) + "\n",
        encoding="utf-8",
    )

    completed = _run_fresh_economic_report(path, check=False)

    assert completed.returncode != 0
    assert "ReceiptIntegrityError" in completed.stderr


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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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

    report = eh.report(
        _validated_execution_rows([baseline, actual])
    )

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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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
        finish_reason="stop",
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

    report = eh.report(
        _validated_execution_rows([baseline, actual])
    )

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

    report = eh.report(
        _validated_execution_rows([baseline, actual])
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
    delta = eh.report(_validated_execution_rows(recs))["monetary_delta"]
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
