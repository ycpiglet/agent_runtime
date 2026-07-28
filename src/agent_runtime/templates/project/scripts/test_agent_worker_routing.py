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
    meta = {
        "id": "MSG-2",
        "task_id": "TASK-646",
        "eval_baseline_tokens": "40",
        "eval_baseline_model": "claude-opus-4-8",
        "eval_baseline_billed_cost": "0.08",
        "eval_baseline_currency": "USD",
    }
    recorded, reason = worker._record_eval_outcome(
        cfg,
        meta,
        decision,
        completed,
        observation,
        finish_reason="stop",
        error=None,
    )
    assert recorded is True
    assert reason is None

    rec = eval_harness.read_outcomes(cfg.eval_log_path)[0]
    assert rec["observed_model"] == "claude-haiku-4-5"
    assert rec["baseline_model"] == "claude-opus-4-8"
    report = eval_harness.report([rec])
    assert report["token_delta"]["saved_tokens"] == 24
    assert report["monetary_delta"]["by_currency"]["USD"][
        "saved_billed_cost"
    ] == 0.06


def test_wrong_or_missing_observed_model_cannot_record_eval(tmp_path):
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
    recorded, reason = worker._record_eval_outcome(
        cfg,
        meta,
        decision,
        route,
        observation,
        finish_reason="stop",
        error=None,
    )
    assert recorded is False
    assert reason == "routing_not_applied"
    assert not cfg.eval_log_path.exists()
