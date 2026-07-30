"""Economic guardrails for the explicit live SDK verification helper."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_sdk_backend as verify  # noqa: E402


def test_live_verifier_reserves_budget_and_records_terminal_receipt(
    tmp_path,
    monkeypatch,
):
    calls = []

    class FakeProvider:
        name = "claude"
        backend = "sdk"
        model = "fake-model"
        per_dispatch_cap = 10

        def run(self, role, instruction, context):
            calls.append((role, instruction, context))
            return SimpleNamespace(
                text="OK",
                tokens_in=2,
                tokens_out=1,
                finish_reason="stop",
                error=None,
                model="fake-model",
                reasoning_effort=None,
                billed_cost=0.01,
                currency="USD",
            )

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setattr(verify, "get_provider", lambda name: FakeProvider())
    monkeypatch.setattr(
        verify.eval_harness,
        "EVAL_LOG",
        tmp_path / "receipts.jsonl",
    )

    assert verify.main() == 0
    assert len(calls) == 1
    receipts = verify.eval_harness.read_outcomes(verify.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["source"] == "verify_sdk_backend"
    assert receipts[0]["status"] == "completed"
    assert receipts[0]["tokens"] == 3
    assert receipts[0]["provider"] == "claude-agent"
    assert receipts[0]["observed_provider"] is None
    economic_report = verify.eval_harness.report(receipts)
    assert economic_report["token_delta"]["eligible_records"] == 0
    assert economic_report["monetary_delta"]["eligible_records"] == 0


def test_live_verifier_preserves_explicit_completion_provider(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        verify.eval_harness,
        "EVAL_LOG",
        tmp_path / "receipts.jsonl",
    )
    route = {
        "provider": "claude-agent",
        "requested_tier": "worker_standard",
        "selected_tier": "worker_standard",
        "resolved_model": "claude-sonnet-4-6",
        "reasoning_effort": None,
        "model_source": "test",
        "reasoning_source": "unsupported",
        "route_status": "configured_unverified",
        "application_status": "configured_unverified",
        "model_changed": None,
        "route_changed": None,
    }
    verify._record(
        dispatch_id="verify-sdk-explicit-provider",
        claim_id=None,
        route=route,
        preflight={},
        status="completed",
        finish_reason="stop",
        result=SimpleNamespace(
            provider="claude-agent",
            model="claude-sonnet-4-6",
            reasoning_effort=None,
            tokens_in=2,
            tokens_out=1,
            billed_cost=0.01,
            currency="USD",
        ),
    )

    receipts = verify.eval_harness.read_outcomes(verify.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["provider"] == "claude-agent"
    assert receipts[0]["observed_provider"] == "claude-agent"
    assert verify.eval_harness._route_observation_complete(receipts[0]) is True


def test_live_verifier_obeys_authoritative_zero_budget_before_provider(
    tmp_path,
    monkeypatch,
):
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-SDK.json").write_text(
        """{
  "schema": "agent-runtime-task-claim/v1",
  "claim_id": "CLAIM-SDK",
  "task_id": "verify-sdk",
  "status": "claimed",
  "task_token_budget": 0,
  "claim_token_budget": 0
}
""",
        encoding="utf-8",
    )
    calls = []

    class FakeProvider:
        name = "claude"
        backend = "sdk"
        model = "fake-model"
        per_dispatch_cap = 10

        def run(self, *args, **kwargs):
            calls.append((args, kwargs))
            raise AssertionError("provider must not be called")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("AGENT_RUNTIME_CLAIM_ID", "CLAIM-SDK")
    monkeypatch.setattr(verify, "ROOT", tmp_path)
    monkeypatch.setattr(verify, "get_provider", lambda name: FakeProvider())
    monkeypatch.setattr(
        verify.eval_harness,
        "EVAL_LOG",
        tmp_path / "receipts.jsonl",
    )

    assert verify.main() == 1
    assert calls == []
    receipts = verify.eval_harness.read_outcomes(verify.eval_harness.EVAL_LOG)
    assert len(receipts) == 1
    assert receipts[0]["status"] == "skipped"
    assert receipts[0]["error"] == "task_budget_insufficient"
