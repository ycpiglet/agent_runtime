"""Provider-worker routing truth tests for TASK-AR-646."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_worker as worker  # noqa: E402
import eval_harness  # noqa: E402
import model_routing  # noqa: E402


class _Provider:
    name = "fake-provider"

    def __init__(self, model: str = "request-default"):
        self.model = model


def _low_decision():
    return model_routing.resolve_model(
        "auto",
        grade="Low",
        prompt="bounded implementation",
    )


def test_worker_role_policy_is_mandatory_and_denies_untriggered_high_tier():
    cfg = worker.WorkerConfig(
        role="scribe",
        provider_name="dummy",
    )
    implicit = worker._message_routing_decision(cfg, {}, "archive bounded state")
    assert implicit["role_policy_id"] == "scribe"
    assert implicit["selected_tier"] == "worker_low"

    explicit_high = worker._message_routing_decision(
        cfg,
        {"routing_model": "opus"},
        "archive bounded state",
    )
    assert explicit_high["selected_tier"] == "worker_low"
    assert explicit_high["routing_status"] == "high_tier_denied"
    assert explicit_high["high_tier_authorized"] is True
    assert explicit_high["denied_requested_tier"] == "planner_high"


def test_request_configuration_is_not_completion_observation():
    provider = _Provider()
    decision = _low_decision()
    planned = worker._apply_routing_to_provider(
        provider,
        "codex-agent",
        decision,
        baseline_model="gpt-5.2-codex",
    )
    assert provider.model == "gpt-5.2-codex"
    assert planned["route_status"] == "ineffective_equivalent"

    observation = worker._completion_observation(
        SimpleNamespace(tokens_in=0, tokens_out=0),
        latency_ms=3.5,
    )
    completed = worker._route_with_observation(
        "codex-agent",
        decision,
        baseline_model="gpt-5.2-codex",
        observation=observation,
    )
    fields = worker._provider_routing_event_fields(
        decision,
        completed,
        observation,
        dispatch_id="MSG-1",
    )

    assert fields["dispatch_id"] == "MSG-1"
    assert fields["resolved_model"] == "gpt-5.2-codex"
    assert fields["observed_model"] is None
    assert fields["model_observation_status"] == "unverified"
    assert fields["token_usage_status"] == "unavailable"
    assert fields["tokens_in"] is None
    assert fields["tokens_out"] is None
    assert fields["latency_status"] == "observed"
    assert fields["billed_cost_status"] == "unavailable"
    assert fields["model_changed"] is False


def test_effective_observed_route_records_token_and_monetary_evidence(tmp_path):
    provider = _Provider()
    decision = _low_decision()
    worker._apply_routing_to_provider(
        provider,
        "claude-agent",
        decision,
        baseline_model="claude-opus-4-8",
    )
    result = SimpleNamespace(
        provider="claude-agent",
        model="claude-haiku-4-5",
        reasoning_effort=None,
        tokens_in=12,
        tokens_out=4,
        billed_cost=0.02,
        currency="usd",
    )
    observation = worker._completion_observation(result, latency_ms=7.25)
    completed = worker._route_with_observation(
        "claude-agent",
        decision,
        baseline_model="claude-opus-4-8",
        observation=observation,
    )
    assert completed["application_status"] == "applied"
    assert completed["route_status"] == "effective"
    assert completed["model_changed"] is True

    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="claude-agent",
        eval_log_path=tmp_path / "eval.jsonl",
    )
    baseline = eval_harness.record_execution_receipt(
        dispatch_id="MSG-2-baseline",
        task_id="TASK-646",
        workload_id="WORKLOAD-2",
        provider="claude-agent",
        resolved_model="claude-opus-4-8",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="unsupported",
        observed_provider="claude-agent",
        observed_model="claude-opus-4-8",
        tokens_in=30,
        tokens_out=10,
        billed_cost=0.08,
        currency="USD",
        source="provider_completion",
        status="completed",
        finish_reason="stop",
        path=cfg.eval_log_path,
    )
    meta = {
        "id": "MSG-2",
        "task_id": "TASK-646",
        "eval_baseline_model": "claude-opus-4-8",
        "eval_baseline_receipt_id": baseline["receipt_id"],
        "eval_workload_id": "WORKLOAD-2",
    }
    recorded, reason = worker._record_execution_receipt(
        cfg,
        meta,
        decision,
        completed,
        observation,
        dispatch_id="MSG-2",
        status="completed",
        source="provider_completion",
        finish_reason="stop",
        error=None,
    )
    assert recorded is True
    assert reason is None

    records = eval_harness.read_outcomes(cfg.eval_log_path)
    rec = records[-1]
    assert rec["observed_model"] == "claude-haiku-4-5"
    assert rec["baseline_model"] == "claude-opus-4-8"
    assert rec["baseline_reference_status"] == "verified"
    report = eval_harness.report(records)
    assert report["token_delta"]["saved_tokens"] == 24
    assert report["monetary_delta"]["by_currency"]["USD"][
        "saved_billed_cost"
    ] == 0.06


def test_wrong_observed_model_records_receipt_but_not_savings_evidence(tmp_path):
    decision = _low_decision()
    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="claude-agent",
        eval_log_path=tmp_path / "eval.jsonl",
    )
    meta = {
        "id": "MSG-3",
        "eval_baseline_tokens": "40",
        "eval_baseline_model": "claude-opus-4-8",
        "eval_baseline_observation_status": "observed",
    }
    observation = worker._completion_observation(
        SimpleNamespace(
            model="claude-sonnet-4-6",
            tokens_in=12,
            tokens_out=4,
        ),
        latency_ms=1,
    )
    route = worker._route_with_observation(
        "claude-agent",
        decision,
        baseline_model="claude-opus-4-8",
        observation=observation,
    )
    recorded, reason = worker._record_execution_receipt(
        cfg,
        meta,
        decision,
        route,
        observation,
        dispatch_id="MSG-3",
        status="completed",
        source="provider_completion",
        finish_reason="stop",
        error=None,
    )
    assert recorded is True
    assert reason == "routing_not_applied"
    records = eval_harness.read_outcomes(cfg.eval_log_path)
    assert len(records) == 1
    assert records[0]["application_status"] == "not_applied"
    assert eval_harness.report(records)["token_delta"]["eligible_records"] == 0


def test_worker_receipt_preserves_explicit_empty_provider_finish(tmp_path):
    decision = _low_decision()
    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="claude-agent",
        eval_log_path=tmp_path / "eval.jsonl",
    )
    observation = worker._completion_observation(
        SimpleNamespace(
            provider="claude-agent",
            model="claude-haiku-4-5",
            reasoning_effort=None,
            tokens_in=2,
            tokens_out=1,
        ),
        latency_ms=1,
    )
    route = worker._route_with_observation(
        "claude-agent",
        decision,
        baseline_model=None,
        observation=observation,
    )

    recorded, _ = worker._record_execution_receipt(
        cfg,
        {"id": "MSG-EMPTY", "task_id": "TASK-EMPTY-WORKER"},
        decision,
        route,
        observation,
        dispatch_id="MSG-EMPTY",
        status="completed",
        source="provider_completion",
        finish_reason="",
        error=None,
    )

    assert recorded is True
    receipt = eval_harness.read_outcomes(cfg.eval_log_path)[0]
    assert receipt["finish_reason"] == ""
    assert receipt["application_status"] == "unverified"
    assert receipt["route_status"] == "unverified"


def test_worker_budget_preflight_skips_provider_and_closes_claim(
    tmp_path,
    monkeypatch,
):
    import message_queue

    repo_root = tmp_path / "repo"
    inbox = repo_root / "agents" / "messages" / "inbox"
    events = repo_root / "agents" / "runtime" / "events"
    claims = repo_root / "agents" / "runtime" / "claims"
    inbox.mkdir(parents=True)
    message = inbox / "MSG-20260730-000000-budget.md"
    message.write_text(
        "---\n"
        "id: MSG-20260730-000000-budget\n"
        "from: backend\n"
        "to: qa\n"
        "task_id: TASK-BUDGET\n"
        "task_token_budget: 0\n"
        "type: question\n"
        "status: open\n"
        "ts: 2026-07-30T00:00:00+09:00\n"
        "---\n"
        "must not reach provider\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker, "REPO_ROOT", repo_root)
    monkeypatch.setattr(worker, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(worker, "EVENTS_DIR", events)
    monkeypatch.setattr(message_queue, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(message_queue, "CLAIMS_DIR", claims)

    class _NeverCalledProvider:
        name = "never-called"
        tokens_per_call = 10

        def __init__(self):
            self.calls = []

        def run(self, role, instruction, context):
            self.calls.append((role, instruction, context))
            raise AssertionError("provider must not be called")

    provider = _NeverCalledProvider()
    receipt_log = tmp_path / "receipts.jsonl"
    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="dummy",
        eval_log_path=receipt_log,
        verbose=False,
    )

    assert worker.process_one(cfg, provider) is True
    assert provider.calls == []
    updated_meta, _ = worker.parse_frontmatter(
        message.read_text(encoding="utf-8")
    )
    assert updated_meta["status"] == "answered"
    records = eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["status"] == "skipped"
    assert records[0]["source"] == "budget_preflight"
    assert records[0]["budget_preflight"]["reason"] == "task_budget_insufficient"


def test_worker_records_provider_call_start_immediately_before_run(
    tmp_path,
    monkeypatch,
):
    import json
    import message_queue

    repo_root = tmp_path / "repo"
    inbox = repo_root / "agents" / "messages" / "inbox"
    events = repo_root / "agents" / "runtime" / "events"
    claims = repo_root / "agents" / "runtime" / "claims"
    inbox.mkdir(parents=True)
    message = inbox / "MSG-20260730-000000-provider.md"
    message.write_text(
        "---\n"
        "id: MSG-20260730-000000-provider\n"
        "from: backend\n"
        "to: qa\n"
        "task_id: TASK-WORKER-PROVIDER\n"
        "task_token_budget: 10\n"
        "type: question\n"
        "status: open\n"
        "ts: 2026-07-30T00:00:00+09:00\n"
        "---\n"
        "run the fake provider\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker, "REPO_ROOT", repo_root)
    monkeypatch.setattr(worker, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(worker, "EVENTS_DIR", events)
    monkeypatch.setattr(message_queue, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(message_queue, "CLAIMS_DIR", claims)

    class _CalledProvider:
        name = "dummy"
        tokens_per_call = 10
        model = "dummy"

        def __init__(self):
            self.calls = []

        def run(self, role, instruction, context):
            self.calls.append((role, instruction, context))
            return SimpleNamespace(
                text="done",
                tokens_in=2,
                tokens_out=1,
                finish_reason="stop",
                error=None,
                changed_files=[],
                provider="dummy",
                model=self.model,
                reasoning_effort=None,
                billed_cost=None,
                currency=None,
            )

    provider = _CalledProvider()
    receipt_log = tmp_path / "receipts.jsonl"
    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="dummy",
        eval_log_path=receipt_log,
        verbose=False,
    )

    assert worker.process_one(cfg, provider) is True
    assert len(provider.calls) == 1
    raw = [
        json.loads(line)
        for line in receipt_log.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["schema"] for row in raw] == [
        eval_harness.BUDGET_RESERVATION_SCHEMA,
        eval_harness.PROVIDER_CALL_START_SCHEMA,
        eval_harness.EXECUTION_RECEIPT_SCHEMA,
    ]
    assert raw[1]["source"] == "agent_worker_provider_run"
    assert raw[1]["provider"] == "dummy"
    assert raw[1]["execution_surface"] == raw[2]["execution_surface"]
    assert raw[2]["budget_settlement_basis"] == "observed_usage"


def test_worker_invalid_raw_route_records_receipt_and_closes_claim(
    tmp_path,
    monkeypatch,
):
    import message_queue

    repo_root = tmp_path / "repo"
    inbox = repo_root / "agents" / "messages" / "inbox"
    events = repo_root / "agents" / "runtime" / "events"
    claims = repo_root / "agents" / "runtime" / "claims"
    inbox.mkdir(parents=True)
    message = inbox / "MSG-20260730-000000-routing.md"
    message.write_text(
        "---\n"
        "id: MSG-20260730-000000-routing\n"
        "from: backend\n"
        "to: qa\n"
        "task_id: TASK-ROUTING\n"
        "routing_model: vendor/raw-expensive-model\n"
        "type: question\n"
        "status: open\n"
        "ts: 2026-07-30T00:00:00+09:00\n"
        "---\n"
        "must not reach provider\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(worker, "REPO_ROOT", repo_root)
    monkeypatch.setattr(worker, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(worker, "EVENTS_DIR", events)
    monkeypatch.setattr(message_queue, "MESSAGES_INBOX", inbox)
    monkeypatch.setattr(message_queue, "CLAIMS_DIR", claims)

    class _NeverCalledProvider:
        name = "never-called"
        tokens_per_call = 10

        def __init__(self):
            self.calls = []

        def run(self, role, instruction, context):
            self.calls.append((role, instruction, context))
            raise AssertionError("provider must not be called")

    provider = _NeverCalledProvider()
    receipt_log = tmp_path / "receipts.jsonl"
    cfg = worker.WorkerConfig(
        role="qa",
        provider_name="dummy",
        eval_log_path=receipt_log,
        verbose=False,
    )

    assert worker.process_one(cfg, provider) is True
    assert provider.calls == []
    updated_meta, _ = worker.parse_frontmatter(
        message.read_text(encoding="utf-8")
    )
    assert updated_meta["status"] == "answered"
    records = eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["status"] == "skipped"
    assert records[0]["source"] == "routing_policy"
    assert records[0]["error"].startswith("routing_policy_rejected:")
