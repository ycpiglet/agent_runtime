"""Unit tests for the bounded synchronous auto-dispatch runner (TASK-208).

These assert the anti-runaway invariants by construction: every halt condition
(work_exhausted / max_dispatches / stop_file / session_budget) fires before a
billable call, budget accounting is synchronous and monotonic, and one bad
dispatch is captured rather than aborting the run or orphaning. All providers
are dummy or fakes — no live token spend, so this is CI-safe.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auto_dispatch  # noqa: E402
import subagent_dispatch  # noqa: E402
from auto_dispatch import SessionBudget, run_bounded_dispatch  # noqa: E402


class _FakeResult:
    def __init__(
        self,
        tokens_in=0,
        tokens_out=0,
        finish_reason="stop",
        error=None,
        *,
        model=None,
        billed_cost=None,
        currency=None,
    ):
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.finish_reason = finish_reason
        self.error = error
        self.model = model
        self.billed_cost = billed_cost
        self.currency = currency


class _FakeProvider:
    """Records every run() call and returns a fixed per-call token cost."""

    def __init__(
        self,
        tokens_per_call=10,
        tokens_out_per_call=0,
        raise_on=None,
        model=None,
        *,
        observed_model=None,
        billed_cost=None,
        currency=None,
    ):
        self.tokens_per_call = tokens_per_call
        self.tokens_out_per_call = tokens_out_per_call
        self.raise_on = raise_on  # index that should raise
        self.model = model
        self.observed_model = observed_model
        self.billed_cost = billed_cost
        self.currency = currency
        self.calls = []

    def run(self, role, instruction, context):
        idx = len(self.calls)
        self.calls.append((role, instruction, context))
        if self.raise_on is not None and idx == self.raise_on:
            raise RuntimeError("boom")
        return _FakeResult(
            tokens_in=self.tokens_per_call,
            tokens_out=self.tokens_out_per_call,
            model=self.observed_model,
            billed_cost=self.billed_cost,
            currency=self.currency,
        )


@pytest.fixture
def patch_provider(monkeypatch):
    """Swap get_provider for a fake so budget/error paths are deterministic and
    never touch a live backend."""
    def _install(provider):
        monkeypatch.setattr(auto_dispatch, "get_provider", lambda name: provider)
        return provider
    return _install


@pytest.fixture(autouse=True)
def isolate_dispatch_events(monkeypatch, tmp_path_factory):
    import message_queue

    events_dir = tmp_path_factory.mktemp("auto-dispatch-events")
    monkeypatch.setattr(
        auto_dispatch,
        "EVENTS_DIR",
        events_dir,
    )
    monkeypatch.setattr(
        message_queue,
        "CLAIMS_DIR",
        tmp_path_factory.mktemp("auto-dispatch-claims"),
    )
    receipt_log = tmp_path_factory.mktemp("auto-dispatch-receipts") / "receipts.jsonl"
    monkeypatch.setattr(auto_dispatch.eval_harness, "EVAL_LOG", receipt_log)
    return events_dir


def _items(n):
    return [{"role": "worker", "instruction": f"t{i}"} for i in range(n)]


def _run(items, provider, **kw):
    kw.setdefault("out", io.StringIO())
    provider_name = kw.pop("provider_name", "fake")
    return run_bounded_dispatch(items, provider_name, **kw)


# ---- SessionBudget ----

def test_budget_remaining_never_negative():
    b = SessionBudget(total=100)
    b.record(150)
    assert b.remaining() == 0
    assert b.exhausted() is True


def test_budget_record_is_monotonic_and_clamps_negative():
    b = SessionBudget(total=100)
    b.record(30)
    b.record(-50)  # defensive clamp — spend cannot decrease
    assert b.spent == 30


# ---- halt conditions ----

def test_halts_on_work_exhausted(patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=1))
    summary = _run(_items(3), p, session_budget=1000, max_dispatches=10)
    assert summary["halt_reason"] == "work_exhausted"
    assert summary["dispatched"] == 3
    assert len(p.calls) == 3


def test_halts_on_max_dispatches_before_billing(patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=1))
    summary = _run(_items(10), p, session_budget=10_000, max_dispatches=4)
    assert summary["halt_reason"] == "max_dispatches (4)"
    assert summary["dispatched"] == 4
    assert len(p.calls) == 4  # never dispatched the 5th


def test_halts_on_session_budget_blocks_next_dispatch(patch_provider):
    # Hard ceiling: if the next dispatch cannot fit in the remaining session
    # budget, it is skipped before the provider is called.
    p = patch_provider(_FakeProvider(tokens_per_call=40))
    summary = _run(_items(10), p, session_budget=100, max_dispatches=10)
    assert summary["halt_reason"] == "session_budget (100)"
    assert summary["spent"] == 80
    assert len(p.calls) == 2
    assert summary["results"][-1]["finish_reason"] == "skipped"
    assert summary["results"][-1]["error"] == "budget_insufficient"


def test_session_budget_caps_provider_per_dispatch_before_call(patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=80_000))
    summary = _run(_items(1), p, session_budget=50_000, max_dispatches=10)

    assert summary["halt_reason"] == "session_budget (50000)"
    assert summary["spent"] == 0
    assert len(p.calls) == 0
    assert summary["results"][0]["finish_reason"] == "skipped"
    assert summary["results"][0]["error"] == "budget_insufficient"


def test_halts_on_stop_file(tmp_path, patch_provider):
    stop = tmp_path / "STOP_LOOP"
    stop.write_text("halt")
    p = patch_provider(_FakeProvider(tokens_per_call=1))
    summary = _run(_items(5), p, max_dispatches=10, stop_files=(stop,))
    assert summary["halt_reason"] == f"stop_file ({stop.name})"
    assert summary["dispatched"] == 0
    assert len(p.calls) == 0  # not a single billable call once stop present


# ---- error capture ----

def test_provider_error_is_captured_not_raised(patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=10, raise_on=1))
    summary = _run(_items(3), p, session_budget=10_000, max_dispatches=10)
    # all three still attempted; accounting not aborted by the middle failure
    assert summary["dispatched"] == 3
    bad = summary["results"][1]
    assert bad["finish_reason"] == "error"
    assert "RuntimeError" in bad["error"]
    assert bad["tokens"] == 0
    # spend reflects only the two good calls
    assert summary["spent"] == 20


def test_summary_token_total_sums_in_and_out(patch_provider):
    class _BothProvider(_FakeProvider):
        def run(self, role, instruction, context):
            self.calls.append((role, instruction, context))
            return _FakeResult(tokens_in=7, tokens_out=5)

    p = patch_provider(_BothProvider())
    summary = _run(_items(2), p, session_budget=10_000, max_dispatches=10)
    assert summary["spent"] == 24  # (7+5) * 2
    assert summary["results"][0]["tokens"] == 12


# ---- live gate (real get_provider, no monkeypatch) ----

def test_live_provider_blocked_without_env(monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    with pytest.raises(SystemExit):
        run_bounded_dispatch(_items(1), "claude", out=io.StringIO())


def test_dummy_provider_runs_without_env(monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    summary = run_bounded_dispatch(_items(2), "dummy", max_dispatches=10,
                                   out=io.StringIO())
    assert summary["dispatched"] == 2
    assert summary["halt_reason"] == "work_exhausted"


def test_unknown_provider_raises():
    with pytest.raises(SystemExit):
        run_bounded_dispatch(_items(1), "no_such_provider", out=io.StringIO())


def test_empty_work_list_no_dispatch(patch_provider):
    p = patch_provider(_FakeProvider())
    summary = _run([], p, session_budget=1000, max_dispatches=10)
    assert summary["dispatched"] == 0
    assert summary["spent"] == 0
    assert summary["halt_reason"] == "work_exhausted"
    assert p.calls == []


# ---- inbox work-source adapter (TASK-210) ----

def _write_msg(inbox, name, *, to, status, mtype="question", body="do the thing",
               routing_model=None, routing_grade=None):
    routing_lines = ""
    if routing_model:
        routing_lines += f"routing_model: {routing_model}\n"
    if routing_grade:
        routing_lines += f"routing_grade: {routing_grade}\n"
    msg = inbox / name
    msg.write_text(
        "---\n"
        f"id: {name[:-3]}\n"
        "from: backend\n"
        f"to: {to}\n"
        f"type: {mtype}\n"
        f"status: {status}\n"
        "ts: 2026-06-03T07:00:00+09:00\n"
        f"{routing_lines}"
        "---\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return msg


def test_inbox_work_items_selects_open_non_reply(tmp_path):
    _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    _write_msg(tmp_path, "MSG-20260603-070001-bbbbbb.md", to="qa", status="claimed")
    _write_msg(tmp_path, "MSG-20260603-070002-cccccc.md", to="qa", status="open", mtype="reply")
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    assert len(items) == 1  # only the open, non-reply message
    assert items[0]["role"] == "qa"
    assert items[0]["instruction"] == "do the thing"
    assert items[0]["context"]["type"] == "question"


def test_inbox_work_items_carries_routing_metadata(tmp_path):
    _write_msg(
        tmp_path,
        "MSG-20260603-070000-aaaaaa.md",
        to="qa",
        status="open",
        routing_model="auto",
        routing_grade="Low",
        body="find and list files",
    )
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    assert items[0]["routing_model"] == "auto"
    assert items[0]["routing_grade"] == "Low"


def test_inbox_work_items_carries_eval_baseline_and_task_id(tmp_path):
    _write_msg(
        tmp_path,
        "MSG-20260603-070000-aaaaaa.md",
        to="qa",
        status="open",
        routing_model="auto",
        routing_grade="Low",
        body="find and list files",
    )
    msg = tmp_path / "MSG-20260603-070000-aaaaaa.md"
    msg.write_text(
        msg.read_text(encoding="utf-8").replace(
            "routing_grade: Low\n",
            "routing_grade: Low\ntask_id: none\neval_baseline_tokens: 3000\n",
        ),
        encoding="utf-8",
    )
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    assert items[0]["context"]["task_id"] == "MSG-20260603-070000-aaaaaa"
    assert items[0]["eval_baseline_tokens"] == "3000"


def test_inbox_work_items_preserves_standard_dispatch_authority(tmp_path):
    msg = _write_msg(
        tmp_path,
        "MSG-20260603-070000-aaaaaa.md",
        to="subagent-scribe",
        status="open",
        routing_model="opus",
        body="archive bounded state",
    )
    msg.write_text(
        msg.read_text(encoding="utf-8").replace(
            "routing_model: opus\n",
            "routing_model: opus\n"
            "task_id: TASK-652\n"
            "dispatch_id: dispatch-explicit-652\n"
            "claim_id: CLAIM-652\n"
            "task_token_budget: 1200\n"
            "claim_token_budget: 300\n"
            "eval_workload_id: WORKLOAD-652\n"
            "eval_baseline_receipt_id: receipt-baseline-652\n"
            "eval_baseline_model: gpt-5.6-sol\n"
            "eval_baseline_reasoning_effort: high\n"
            "escalation_triggers:\n"
            "  - data_integrity\n",
        ),
        encoding="utf-8",
    )

    item = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)[0]
    assert item["role"] == "scribe"
    assert item["dispatch_id"] == "dispatch-explicit-652"
    assert item["claim_id"] == "CLAIM-652"
    assert item["task_token_budget"] == "1200"
    assert item["claim_token_budget"] == "300"
    assert item["eval_workload_id"] == "WORKLOAD-652"
    assert item["eval_baseline_receipt_id"] == "receipt-baseline-652"
    assert item["eval_baseline_model"] == "gpt-5.6-sol"
    assert item["eval_baseline_reasoning_effort"] == "high"
    assert item["escalation_triggers"] == ["data_integrity"]
    assert item["context"]["msg_id"] == "MSG-20260603-070000-aaaaaa"


def test_inbox_work_items_derives_stable_dispatch_id_from_message_id(tmp_path):
    _write_msg(
        tmp_path,
        "MSG-20260603-070000-aaaaaa.md",
        to="qa",
        status="open",
    )

    item = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)[0]
    assert item["dispatch_id"] == "MSG-20260603-070000-aaaaaa"
    assert item["context"]["dispatch_id"] == "MSG-20260603-070000-aaaaaa"


def test_auto_dispatch_role_policy_is_mandatory_and_denies_scribe_opus():
    implicit = auto_dispatch._routing_decision_for_item(
        {"role": "scribe"},
        "archive bounded state",
    )
    assert implicit["role_policy_id"] == "scribe"
    assert implicit["selected_tier"] == "worker_low"

    denied = auto_dispatch._routing_decision_for_item(
        {"role": "scribe", "routing_model": "opus"},
        "archive bounded state",
    )
    assert denied["selected_tier"] == "worker_low"
    assert denied["routing_status"] == "high_tier_denied"
    assert denied["denied_requested_tier"] == "planner_high"


def test_inbox_work_items_filters_by_role(tmp_path):
    _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    _write_msg(tmp_path, "MSG-20260603-070001-bbbbbb.md", to="backend", status="open")
    qa = auto_dispatch.inbox_work_items("qa", inbox_dir=tmp_path)
    assert [i["role"] for i in qa] == ["qa"]


def test_inbox_work_items_bounded_by_limit(tmp_path):
    for i in range(5):
        _write_msg(tmp_path, f"MSG-20260603-07000{i}-aaaaa{i}.md", to="qa", status="open")
    items = auto_dispatch.inbox_work_items(limit=2, inbox_dir=tmp_path)
    assert len(items) == 2  # never builds more than `limit`


def test_inbox_work_items_is_read_only(tmp_path):
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    before = msg.read_text(encoding="utf-8")
    auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    assert msg.read_text(encoding="utf-8") == before  # snapshot did not claim/mutate


def test_inbox_work_items_missing_dir_returns_empty(tmp_path):
    assert auto_dispatch.inbox_work_items(inbox_dir=tmp_path / "nope") == []


def test_inbox_items_run_through_dispatch(tmp_path, monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    _write_msg(tmp_path, "MSG-20260603-070001-bbbbbb.md", to="backend", status="open")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    summary = run_bounded_dispatch(items, "dummy", max_dispatches=10, out=io.StringIO())
    assert summary["dispatched"] == 2
    assert summary["halt_reason"] == "work_exhausted"


def test_dispatch_records_routing_result(patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=1))
    items = [{
        "role": "qa",
        "instruction": "find and list files",
        "context": {"task_id": "TASK-239"},
        "routing_model": "auto",
        "routing_grade": "Low",
    }]
    summary = _run(items, p, session_budget=1000, max_dispatches=10)
    result = summary["results"][0]
    assert result["routing_grade"] == "RolePolicy"
    assert result["policy_model"] == "reviewer_standard"
    assert result["selected_model"] == "reviewer_standard"


def test_dispatch_records_routed_eval_outcome_when_baseline_present(tmp_path, patch_provider):
    receipt_log = tmp_path / "eval.jsonl"
    baseline = auto_dispatch.eval_harness.record_execution_receipt(
        dispatch_id="TASK-239-baseline",
        task_id="TASK-239",
        workload_id="WORKLOAD-239",
        provider="claude-agent",
        resolved_model="claude-opus-4-8",
        resolved_model_source="adapter_default:test",
        resolved_reasoning_source="unsupported",
        observed_provider="claude-agent",
        observed_model="claude-opus-4-8",
        tokens_in=2500,
        tokens_out=500,
        source="provider_completion",
        status="completed",
        path=receipt_log,
    )
    p = patch_provider(
        _FakeProvider(
            tokens_per_call=11,
            tokens_out_per_call=1,
            model="request-default",
            observed_model="claude-haiku-4-5",
        )
    )
    items = [{
        "role": "scribe",
        "instruction": "find and list files",
        "context": {"task_id": "TASK-239"},
        "routing_model": "auto",
        "routing_grade": "Low",
        "eval_baseline_model": "claude-opus-4-8",
        "eval_baseline_receipt_id": baseline["receipt_id"],
        "eval_workload_id": "WORKLOAD-239",
    }]
    summary = _run(
        items,
        p,
        provider_name="claude-agent",
        session_budget=1000,
        max_dispatches=10,
        eval_log_path=receipt_log,
    )
    assert summary["results"][0]["eval_recorded"] is True
    recs = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(recs) == 2
    rec = recs[-1]
    assert rec["task_id"] == "TASK-239"
    assert rec["grade"] == "RolePolicy"
    assert rec["tokens"] == 12
    assert rec["policy_model"] == "worker_low"
    assert rec["selected_model"] == "worker_low"
    assert rec["baseline_tokens"] == 3000
    assert rec["observed_model"] == "claude-haiku-4-5"
    assert rec["baseline_model"] == "claude-opus-4-8"
    assert rec["model_changed"] is True
    assert rec["route_changed"] is True
    assert rec["baseline_observation_status"] == "observed"
    assert rec["baseline_reference_status"] == "verified"
    assert rec["schema"] == auto_dispatch.eval_harness.EXECUTION_RECEIPT_SCHEMA


def test_auto_dispatch_records_eval_on_provider_exception_non_write_back(tmp_path, patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=12, raise_on=0, model="haiku"))
    items = [{
        "role": "qa",
        "instruction": "find and list files",
        "context": {"task_id": "TASK-239"},
        "routing_model": "auto",
        "routing_grade": "Low",
        "eval_baseline_tokens": 3000,
    }]
    summary = _run(items, p, session_budget=1000, max_dispatches=10, eval_log_path=tmp_path / "eval.jsonl")
    assert summary["results"][0]["eval_recorded"] is True
    assert summary["results"][0]["receipt_recorded"] is True
    assert summary["results"][0]["eval_skip_reason"] == "model_observation_unavailable"
    recs = auto_dispatch.eval_harness.read_outcomes(tmp_path / "eval.jsonl")
    assert len(recs) == 1
    assert recs[0]["status"] == "error"
    assert recs[0]["source"] == "provider_error"


def test_routing_eval_requires_applied_provider_model(tmp_path, patch_provider):
    p = patch_provider(
        _FakeProvider(
            tokens_per_call=12,
            model="gpt-5.2-codex",
            observed_model="gpt-5.2-codex",
        )
    )
    items = [{
        "role": "qa",
        "instruction": "find and list files",
        "context": {"task_id": "TASK-239"},
        "routing_model": "auto",
        "routing_grade": "Low",
        "eval_baseline_tokens": 3000,
        "eval_baseline_model": "gpt-5.2-codex",
        "eval_baseline_observation_status": "observed",
    }]
    summary = run_bounded_dispatch(
        items,
        "codex-agent",
        session_budget=1000,
        max_dispatches=10,
        eval_log_path=tmp_path / "eval.jsonl",
        out=io.StringIO(),
    )
    result = summary["results"][0]
    assert result["selected_model"] == "reviewer_standard"
    assert result["eval_recorded"] is True
    assert result["receipt_recorded"] is True
    assert result["route_status"] == "ineffective_equivalent"
    assert result["model_changed"] is False
    assert result["eval_skip_reason"] == "route_not_effective"
    recs = auto_dispatch.eval_harness.read_outcomes(tmp_path / "eval.jsonl")
    assert len(recs) == 1
    assert recs[0]["route_changed"] is False


def test_every_completion_records_one_receipt_without_routing(tmp_path, patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=7))
    receipt_log = tmp_path / "receipts.jsonl"
    summary = _run(
        [{
            "dispatch_id": "dispatch-generic-1",
            "role": "worker",
            "instruction": "bounded work",
            "context": {"task_id": "TASK-GENERIC"},
        }],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert len(p.calls) == 1
    assert summary["results"][0]["receipt_recorded"] is True
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["dispatch_id"] == "dispatch-generic-1"
    assert records[0]["task_id"] == "TASK-GENERIC"
    assert records[0]["source"] == "provider_completion"


def test_durable_task_budget_survives_runner_restart(tmp_path, patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=10))
    receipt_log = tmp_path / "receipts.jsonl"
    first = {
        "dispatch_id": "dispatch-budget-1",
        "role": "worker",
        "instruction": "first",
        "task_id": "TASK-BUDGET",
        "task_token_budget": 15,
    }
    second = {
        "dispatch_id": "dispatch-budget-2",
        "role": "worker",
        "instruction": "second",
        "task_id": "TASK-BUDGET",
        "task_token_budget": 15,
    }

    first_summary = _run(
        [first],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )
    second_summary = _run(
        [second],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert first_summary["results"][0]["finish_reason"] == "stop"
    assert len(p.calls) == 1
    blocked = second_summary["results"][0]
    assert blocked["finish_reason"] == "skipped"
    assert blocked["error"] == "task_budget_insufficient"
    assert blocked["budget_preflight"]["task_tokens_used"] == 10
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert [record["status"] for record in records] == ["completed", "skipped"]


def test_configured_budget_blocks_unknown_dispatch_ceiling(tmp_path, patch_provider):
    class _UnknownCeilingProvider:
        name = "unknown-ceiling"

        def __init__(self):
            self.calls = []

        def run(self, role, instruction, context):
            self.calls.append((role, instruction, context))
            return _FakeResult(tokens_in=1)

    p = patch_provider(_UnknownCeilingProvider())
    receipt_log = tmp_path / "receipts.jsonl"
    summary = _run(
        [{
            "dispatch_id": "dispatch-unknown-ceiling",
            "role": "worker",
            "instruction": "do not call",
            "task_id": "TASK-BUDGET",
            "task_token_budget": 100,
        }],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert p.calls == []
    assert summary["results"][0]["error"] == "dispatch_ceiling_unavailable"
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["source"] == "budget_preflight"


@pytest.mark.parametrize(
    ("configured_budget", "reason"),
    [(0, "task_budget_insufficient"), ("not-an-int", "invalid_task_token_budget")],
)
def test_zero_and_invalid_budget_fail_closed(
    tmp_path,
    patch_provider,
    configured_budget,
    reason,
):
    p = patch_provider(_FakeProvider(tokens_per_call=10))
    summary = _run(
        [{
            "dispatch_id": f"dispatch-{reason}",
            "role": "worker",
            "instruction": "do not call",
            "task_id": "TASK-BUDGET",
            "task_token_budget": configured_budget,
        }],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=tmp_path / "receipts.jsonl",
    )

    assert p.calls == []
    assert summary["results"][0]["error"] == reason


def test_duplicate_dispatch_id_is_not_called_or_rewritten(tmp_path, patch_provider):
    p = patch_provider(_FakeProvider(tokens_per_call=5))
    receipt_log = tmp_path / "receipts.jsonl"
    item = {
        "dispatch_id": "dispatch-once",
        "role": "worker",
        "instruction": "exactly once",
        "task_id": "TASK-ONCE",
    }

    _run(
        [item],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )
    duplicate = _run(
        [item],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert len(p.calls) == 1
    assert duplicate["results"][0]["error"] == "duplicate_dispatch_id"
    assert duplicate["results"][0]["receipt_recorded"] is False
    assert len(auto_dispatch.eval_harness.read_outcomes(receipt_log)) == 1


def test_replaying_same_open_inbox_snapshot_calls_provider_exactly_once(
    tmp_path,
    patch_provider,
):
    _write_msg(
        tmp_path,
        "MSG-20260603-070000-aaaaaa.md",
        to="qa",
        status="open",
    )
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    p = patch_provider(_FakeProvider(tokens_per_call=5))
    receipt_log = tmp_path / "receipts.jsonl"

    first = _run(
        items,
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )
    replay = _run(
        auto_dispatch.inbox_work_items(inbox_dir=tmp_path),
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert first["results"][0]["receipt_recorded"] is True
    assert len(p.calls) == 1
    assert replay["results"][0]["error"] == "duplicate_dispatch_id"
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["dispatch_id"] == "MSG-20260603-070000-aaaaaa"


def test_invalid_raw_route_records_terminal_receipt_without_provider_call(
    tmp_path,
    patch_provider,
):
    p = patch_provider(_FakeProvider(tokens_per_call=5))
    receipt_log = tmp_path / "receipts.jsonl"

    summary = _run(
        [
            {
                "dispatch_id": "dispatch-invalid-route",
                "role": "scribe",
                "instruction": "archive bounded state",
                "task_id": "TASK-652",
                "routing_model": "vendor/raw-expensive-model",
            }
        ],
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
    )

    assert p.calls == []
    assert summary["results"][0]["finish_reason"] == "skipped"
    assert summary["results"][0]["error"].startswith("routing_policy_rejected:")
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["dispatch_id"] == "dispatch-invalid-route"
    assert records[0]["source"] == "routing_policy"
    assert records[0]["status"] == "skipped"


def test_inbox_without_claim_id_uses_active_zero_budget_authority(
    tmp_path,
    monkeypatch,
    patch_provider,
):
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True)
    (claim_dir / "CLAIM-AUTO-652.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-AUTO-652",
                "task_id": "TASK-652",
                "status": "claimed",
                "task_token_budget": 0,
                "claim_token_budget": 0,
            }
        ),
        encoding="utf-8",
    )
    inbox = tmp_path / "agents" / "messages" / "inbox"
    monkeypatch.setattr(subagent_dispatch, "MESSAGES_INBOX", inbox)
    message = subagent_dispatch.emit_call_message(
        role_id="scribe",
        task_id="TASK-652",
        intent="archive bounded state",
    )
    assert message.is_file()
    monkeypatch.setattr(auto_dispatch, "REPO_ROOT", tmp_path)
    p = patch_provider(_FakeProvider(tokens_per_call=5))
    receipt_log = tmp_path / "receipts.jsonl"

    summary = _run(
        auto_dispatch.inbox_work_items(inbox_dir=inbox),
        p,
        session_budget=1000,
        max_dispatches=1,
        eval_log_path=receipt_log,
        stop_files=(),
    )

    assert p.calls == []
    blocked = summary["results"][0]
    assert blocked["error"] == "task_budget_insufficient"
    assert (
        blocked["budget_preflight"]["budget_authority"]["claim_id"]
        == "CLAIM-AUTO-652"
    )
    records = auto_dispatch.eval_harness.read_outcomes(receipt_log)
    assert len(records) == 1
    assert records[0]["claim_id"] == "CLAIM-AUTO-652"


def test_dispatch_telemetry_does_not_infer_observed_model(
    patch_provider,
    isolate_dispatch_events,
):
    p = patch_provider(_FakeProvider(tokens_per_call=12, model="request-default"))
    items = [{
        "role": "qa",
        "instruction": "bounded implementation",
        "routing_model": "haiku",
        "routing_grade": "Low",
    }]
    summary = _run(
        items,
        p,
        provider_name="claude-agent",
        session_budget=1000,
        max_dispatches=10,
    )
    result = summary["results"][0]
    assert result["resolved_model"] == "claude-haiku-4-5"
    assert result["observed_model"] is None
    assert result["model_observation_status"] == "unverified"
    assert result["token_usage_status"] == "partial"
    assert result["tokens_in"] == 12
    assert result["tokens_out"] is None
    assert result["latency_status"] == "observed"
    assert result["billed_cost_status"] == "unavailable"
    event = json.loads(
        next(isolate_dispatch_events.glob("*.jsonl")).read_text(
            encoding="utf-8"
        )
    )
    assert event["dispatch_id"] == result["dispatch_id"]
    assert event["resolved_model"] == "claude-haiku-4-5"
    assert event["observed_model"] is None
    assert event["deterministic_preflight"] == "not_required"


# ---- write-back path (TASK-212) ----

def _reply_metas(inbox, exclude):
    from agent_worker import parse_frontmatter
    out = []
    for p in inbox.iterdir():
        if p.name == exclude or p.suffix != ".md":
            continue
        out.append(parse_frontmatter(p.read_text(encoding="utf-8"))[0])
    return out


def _status_of(path):
    from agent_worker import parse_frontmatter
    return parse_frontmatter(path.read_text(encoding="utf-8"))[0]["status"]


def test_write_back_replies_and_marks_answered(tmp_path, monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    summary = run_bounded_dispatch(items, "dummy", max_dispatches=10,
                                   write_back=True, out=io.StringIO())
    assert summary["dispatched"] == 1
    assert summary["replied"] == 1
    assert summary["spent"] > 0  # dummy reports a non-zero token estimate
    # original walked open -> claimed -> answered (same lifecycle as a worker)
    assert _status_of(msg) == "answered"
    # a reply addressed back to the sender was written into the same inbox
    replies = _reply_metas(tmp_path, exclude=msg.name)
    assert any(m.get("type") == "reply"
               and m.get("in_reply_to") == "MSG-20260603-070000-aaaaaa"
               and m.get("to") == "backend"  # original's `from`
               for m in replies)


def test_write_back_skips_when_not_open_costs_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)  # snapshot while open
    # a worker claims it before dispatch — the snapshot is now stale
    _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="claimed")
    summary = run_bounded_dispatch(items, "dummy", max_dispatches=10,
                                   write_back=True, out=io.StringIO())
    r = summary["results"][0]
    assert r["finish_reason"] == "skipped"
    assert r["error"] == "claim_lost"
    assert summary["spent"] == 0   # claim lost => no billable call
    assert summary["replied"] == 0
    assert _status_of(msg) == "claimed"  # we did not touch the worker's claim
    assert _reply_metas(tmp_path, exclude=msg.name) == []


def test_write_back_provider_error_still_answers(tmp_path, patch_provider):
    p = patch_provider(_FakeProvider(raise_on=0))
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    summary = _run(items, p, max_dispatches=10, write_back=True)
    assert summary["results"][0]["finish_reason"] == "error"
    assert summary["replied"] == 1               # error reply still written...
    assert _status_of(msg) == "answered"         # ...so the claim is not orphaned


def test_write_back_reports_reply_even_if_mark_answered_fails(tmp_path, monkeypatch):
    # If the reply is written but the status flip raises (IO error), the reply
    # must still be reported (accounting correct); message stays 'claimed'.
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)

    def _boom(_path, **_kwargs):
        raise OSError("disk full")
    # auto_dispatch intentionally imports the lease primitive directly; patch
    # the actual call seam rather than agent_worker's unrelated wrapper.
    monkeypatch.setattr(auto_dispatch, "lease_mark_answered", _boom)

    summary = run_bounded_dispatch(items, "dummy", max_dispatches=10,
                                   write_back=True, out=io.StringIO())
    assert summary["replied"] == 1                       # reply still written...
    assert summary["results"][0]["reply"] is not None
    assert _status_of(msg) == "claimed"                  # ...flip failed: left claimed
    assert _reply_metas(tmp_path, exclude=msg.name)      # a reply file exists


def test_write_back_off_keeps_inbox_read_only(tmp_path, monkeypatch):
    monkeypatch.delenv("DISPATCH_ENABLE_LIVE", raising=False)
    msg = _write_msg(tmp_path, "MSG-20260603-070000-aaaaaa.md", to="qa", status="open")
    before = msg.read_text(encoding="utf-8")
    items = auto_dispatch.inbox_work_items(inbox_dir=tmp_path)
    summary = run_bounded_dispatch(items, "dummy", max_dispatches=10, out=io.StringIO())
    assert summary["dispatched"] == 1
    assert summary.get("replied", 0) == 0
    assert msg.read_text(encoding="utf-8") == before     # original untouched
    assert [p.name for p in tmp_path.iterdir()] == [msg.name]  # no reply file
