"""Crash-safe session JSON writes in the template orchestrator (issue #274 part 1).

A direct write_text interrupted mid-write leaves a half-written, unparseable
session JSON that crashes the next session's orchestrator/claim-reaper. The
temp-then-os.replace pattern guarantees readers only ever see the old or the
new record (host-proven on autofolio, forced-shutdown scenario included).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_orchestrator.py"
)
PRODUCTION_SCRIPTS = REPO_ROOT / "scripts"
PRODUCTION_DISPATCHER = PRODUCTION_SCRIPTS / "task_claim_dispatcher.py"
PRODUCTION_POINTER_GATE = PRODUCTION_SCRIPTS / "parallel_worktree_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("agent_orchestrator_under_test", ORCHESTRATOR)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves InitVar annotations via sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=None)
def _load_production_script(path: Path, module_name: str):
    """Load one live producer/consumer module without copying its contract."""

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    scripts_path = str(PRODUCTION_SCRIPTS)
    inserted = scripts_path not in sys.path
    if inserted:
        sys.path.insert(0, scripts_path)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(scripts_path)
    return module


POINTER_AGENT_FIELDS = tuple(
    _load_production_script(
        PRODUCTION_POINTER_GATE,
        "production_parallel_worktree_gate_under_test",
    ).POINTER_AGENT_FIELDS
)


def _claim_progress_args(
    claim_id: str,
    *,
    expected_revision: int = 3,
) -> list[str]:
    return [
        "claim-progress",
        "--claim-id",
        claim_id,
        "--agent-instance-id",
        "le-20260803-090000-kst-orchestrator",
        "--callsite-id",
        "terminal:wt-task-ar-655:tab-01",
        "--expected-revision",
        str(expected_revision),
        "--phase",
        "implementation",
        "--progress-pct",
        "60",
        "--step-index",
        "6",
        "--step-total",
        "10",
        "--status-text",
        "Delegating progress through claim heartbeat",
        "--now",
        "2026-08-03T09:20:00+09:00",
        "--json",
    ]


def _claim_progress_sentinels(
    root: Path,
    claim_id: str,
) -> tuple[Path, bytes, Path, bytes]:
    claim_path = root / "agents/runtime/task_claims" / f"{claim_id}.json"
    pointer_path = root / "agents/project/NEXT-SESSION-POINTER.yml"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text('{"sentinel":"serial claim authority"}\n', encoding="utf-8")
    pointer_path.write_text("sentinel: serial projection owner\n", encoding="utf-8")
    return (
        claim_path,
        claim_path.read_bytes(),
        pointer_path,
        pointer_path.read_bytes(),
    )


def _full_merge_dispatcher_response(root: Path, claim_id: str) -> dict[str, object]:
    """Build the success receipt from the live dispatcher's full projection."""

    claim_ref = f"agents/runtime/task_claims/{claim_id}.json"
    claim_path = root / claim_ref
    claim = {
        "claim_id": claim_id,
        "mutation_revision": 4,
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": "le-20260803-090000-kst-orchestrator",
        "display_name": "lead_engineer@orchestrator-03",
        "callsite_id": "terminal:wt-task-ar-655:tab-01",
        "pane_id": "terminal:wt-task-ar-655:tab-01",
        "task_id": "TASK-AR-655",
        "unit_id": "UNIT-TASK-AR-655-001",
        "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
        "status": "claimed",
        "phase": "implementation",
        "progress_pct": 60,
        "step_index": 6,
        "step_total": 10,
        "status_text": "Delegating progress through claim heartbeat",
        "worktree_path": ".worktrees/TASK-AR-655",
        "branch": "codex/task-ar-655-v080-lease-bounds",
        "handoff_path": f"agents/runtime/task_claims/{claim_id}.handoff.md",
        "log_path": f"agents/runtime/task_claims/{claim_id}.log.md",
        "last_heartbeat": "2026-08-03T09:20:00+09:00",
        "requested_model_tier": "worker_standard",
        "selected_model_tier": "planner_high",
        "routing_policy_id": "task-unit-tier-policy",
        "routing_escalation_reason": "trigger:data_integrity,repeated_failure",
        "task_token_budget": 200_000,
        "claim_token_budget": 100_000,
    }
    dispatcher = _load_production_script(
        PRODUCTION_DISPATCHER,
        "production_task_claim_dispatcher_under_test",
    )
    projection = dispatcher._projection_payload(  # noqa: SLF001
        root,
        claim_path,
        claim,
        include_revision=True,
    )
    return {
        "status": "heartbeated",
        "path": claim_ref,
        "claim": claim,
        "receipt": {"committed": True, "claim_revision": 4},
        "projection": projection,
    }


def _conflicting_pointer_agent_value(field: str, current: object) -> object:
    if type(current) is int:
        return current + 1
    if field == "status":
        return "in_progress"
    if field == "claim_path":
        return "agents/runtime/task_claims/CLAIM-AR655-W4B-OTHER.json"
    if field == "last_heartbeat":
        return "2026-08-03T09:21:00+09:00"
    return f"{current}-conflict"


def test_write_session_json_roundtrip_and_no_temp_residue(tmp_path: Path) -> None:
    mod = _load()
    target = tmp_path / "sessions" / "agent-1.json"
    mod.write_session_json(target, {"agent_id": "agent-1", "status": "active"})

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "agent_id": "agent-1",
        "status": "active",
    }
    # No temp file left behind, and the record ends with a newline.
    assert [p.name for p in target.parent.iterdir()] == ["agent-1.json"]
    assert target.read_text(encoding="utf-8").endswith("\n")


def test_write_session_json_replaces_existing_record(tmp_path: Path) -> None:
    mod = _load()
    target = tmp_path / "agent-2.json"
    mod.write_session_json(target, {"status": "active"})
    mod.write_session_json(target, {"status": "stopping"})
    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "stopping"}
    assert [p.name for p in tmp_path.iterdir()] == ["agent-2.json"]


def test_no_session_record_site_uses_direct_write_text() -> None:
    # Every session-record write must go through write_session_json; a direct
    # json.dumps write_text on a session path is the crash-unsafe pattern.
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    assert text.count("write_session_json(") >= 4  # def + 3 call sites
    for line in text.splitlines():
        if "session_path" in line and "write_text" in line:
            raise AssertionError(f"direct session write: {line.strip()}")


def test_kill_does_not_claim_unverified_task_completion(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)
    agent_id = "agent_0123456789ab"
    mod.write_session_json(
        tmp_path / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": "TASK-123", "status": "active"},
    )
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mod,
        "emit_allimbot_event",
        lambda event_type, data: calls.append((event_type, dict(data))),
    )

    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="completed"))

    assert outcome.code == 0
    record = json.loads((tmp_path / f"{agent_id}.json").read_text(encoding="utf-8"))
    assert record["status"] == "closed"
    assert record["outcome"] == "completed"
    assert calls == []


def test_kill_notifies_only_authoritative_task_completion(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    sessions_dir = tmp_path / "sessions"
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(mod, "SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(mod, "TASKS_DIR", tasks_dir)
    agent_id = "agent_1234567890ab"
    task_id = "TASK-123"
    mod.write_session_json(
        sessions_dir / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": task_id, "status": "active"},
    )
    (tasks_dir / f"{task_id}.md").write_text(
        "---\nid: TASK-123\nstatus: completed\nverification_status: passed\n---\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mod,
        "emit_allimbot_event",
        lambda event_type, data: calls.append((event_type, dict(data))),
    )

    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="completed"))

    assert outcome.code == 0
    assert calls == [
        (
            "task.state.changed",
            {
                "task_id": "TASK-123",
                "from_state": "review",
                "to_state": "completed",
                "owner_role": "runtime",
            },
        )
    ]


def test_kill_failure_is_labeled_as_worker_report(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)
    agent_id = "agent_fedcba987654"
    mod.write_session_json(
        tmp_path / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": "TASK-789", "status": "active"},
    )
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        mod,
        "emit_allimbot_event",
        lambda event_type, data: calls.append((event_type, dict(data))),
    )

    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="failed"))

    assert outcome.code == 0
    assert calls == [
        (
            "task.state.changed",
            {
                "task_id": "TASK-789",
                "from_state": "working",
                "to_state": "failed",
                "owner_role": "runtime",
            },
        )
    ]


def test_kill_default_stop_does_not_claim_task_completion(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)
    agent_id = "agent_abcdef012345"
    mod.write_session_json(
        tmp_path / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": "TASK-456", "status": "active"},
    )

    def unexpected_emit(*_args, **_kwargs):
        raise AssertionError("a stopped session is not a completed task")

    monkeypatch.setattr(mod, "emit_allimbot_event", unexpected_emit)
    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="stopped"))
    assert outcome.code == 0
    record = json.loads((tmp_path / f"{agent_id}.json").read_text(encoding="utf-8"))
    assert record["status"] == "stopping"
    assert record["outcome"] == "stopped"


def test_claim_progress_delegates_once_and_never_writes_claim_or_pointer(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-20260803-090000-task-ar-655-orchestrator"
    claim_path = tmp_path / "agents/runtime/task_claims" / f"{claim_id}.json"
    pointer_path = tmp_path / "agents/project/NEXT-SESSION-POINTER.yml"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text('{"sentinel":"serial claim authority"}\n', encoding="utf-8")
    pointer_path.write_text("sentinel: serial projection owner\n", encoding="utf-8")
    claim_before = claim_path.read_bytes()
    pointer_before = pointer_path.read_bytes()
    calls: list[tuple[list[str], dict[str, object]]] = []
    dispatcher_response = _full_merge_dispatcher_response(tmp_path, claim_id)

    def fake_run(command, **kwargs):
        calls.append((list(command), dict(kwargs)))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(dispatcher_response),
            stderr="",
        )

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    rc = mod.main(
        [
            "claim-progress",
            "--claim-id",
            claim_id,
            "--agent-instance-id",
            "le-20260803-090000-kst-orchestrator",
            "--callsite-id",
            "terminal:wt-task-ar-655:tab-01",
            "--expected-revision",
            "3",
            "--phase",
            "implementation",
            "--progress-pct",
            "60",
            "--step-index",
            "6",
            "--step-total",
            "10",
            "--status-text",
            "Delegating progress through claim heartbeat",
            "--now",
            "2026-08-03T09:20:00+09:00",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert Path(command[1]).name == "task_claim_dispatcher.py"
    assert command.count("heartbeat") == 1
    assert command[command.index("--root") + 1] == str(tmp_path)
    for flag, value in (
        ("--claim-id", claim_id),
        ("--agent-instance-id", "le-20260803-090000-kst-orchestrator"),
        ("--callsite-id", "terminal:wt-task-ar-655:tab-01"),
        ("--expected-revision", "3"),
        ("--phase", "implementation"),
        ("--progress-pct", "60"),
        ("--step-index", "6"),
        ("--step-total", "10"),
        ("--status-text", "Delegating progress through claim heartbeat"),
        ("--now", "2026-08-03T09:20:00+09:00"),
    ):
        assert command.count(flag) == 1
        assert command[command.index(flag) + 1] == value
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    rendered = json.loads(captured.out)
    assert rendered["receipt"]["claim_revision"] == 4
    assert rendered["projection"]["claim_revision"] == 4
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


@pytest.mark.parametrize(
    "response_kind",
    ("malformed", "non-object", "incomplete", "incoherent"),
)
def test_claim_progress_zero_exit_with_unverifiable_receipt_is_indeterminate(
    tmp_path: Path,
    monkeypatch,
    capsys,
    response_kind: str,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-20260803-090000-task-ar-655-indeterminate"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    expected_current = {
        "claim_id": None,
        "claim_revision": None,
        "receipt_revision": None,
        "projection_claim_id": None,
        "projection_revision": None,
    }
    if response_kind == "malformed":
        stdout = "{not-json"
    elif response_kind == "non-object":
        stdout = "[]"
    elif response_kind == "incomplete":
        stdout = json.dumps(
            {
                "status": "heartbeated",
                "claim": {"claim_id": claim_id},
            }
        )
        expected_current["claim_id"] = claim_id
    else:
        stdout = json.dumps(
            {
                "status": "heartbeated",
                "claim": {
                    "claim_id": f"{claim_id}-other",
                    "mutation_revision": 7,
                },
                "receipt": {"committed": True, "claim_revision": 4},
                "projection": {
                    "claim_id": claim_id,
                    "claim_revision": 5,
                    "operation": "merge",
                },
            }
        )
        expected_current.update(
            {
                "claim_id": f"{claim_id}-other",
                "claim_revision": 7,
                "receipt_revision": 4,
                "projection_claim_id": claim_id,
                "projection_revision": 5,
            }
        )
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return SimpleNamespace(
            returncode=0,
            stdout=stdout,
            stderr="bounded dispatcher stderr",
        )

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 2, captured.err or captured.out
    assert len(calls) == 1
    rendered = json.loads(captured.out)
    assert rendered["status"] == "claim_progress_receipt_indeterminate"
    assert rendered["commit_state"] == "unknown"
    assert rendered["retry_safe"] is False
    assert rendered["dispatcher_returncode"] == 0
    assert rendered["expected"] == {
        "claim_id": claim_id,
        "prior_revision": 3,
        "committed_revision": 4,
    }
    assert rendered["current"] == expected_current
    assert "receipt" not in rendered
    assert "Traceback" not in captured.out + captured.err
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


def test_claim_progress_zero_exit_with_conflicting_projection_authority_is_indeterminate(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-AR655-W4B-PROJECTION"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    other_ref = "agents/runtime/task_claims/CLAIM-OTHER.json"
    dispatcher_response = {
        "status": "heartbeated",
        "path": other_ref,
        "claim": {
            "claim_id": claim_id,
            "mutation_revision": 4,
            "task_id": "TASK-AR-655",
            "unit_id": "UNIT-TASK-AR-655-001",
            "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
        },
        "receipt": {"committed": True, "claim_revision": 4},
        "projection": {
            "status": "projection",
            "operation": "merge",
            "claim_id": claim_id,
            "claim_revision": 4,
            "task_claim_ref": other_ref,
            "task_id": "TASK-OTHER",
            "unit_id": "UNIT-TASK-OTHER-001",
            "task_set_id": "TASKSET-OTHER",
            "pointer": {
                "active_task": "TASK-OTHER",
                "active_task_set": "TASKSET-OTHER",
                "active_claims": [other_ref],
                "current_agents": [
                    {
                        "claim_id": "CLAIM-OTHER",
                        "task_id": "TASK-OTHER",
                        "unit_id": "UNIT-TASK-OTHER-001",
                        "task_set_id": "TASKSET-OTHER",
                        "mutation_revision": 999,
                    }
                ],
            },
        },
    }
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(dispatcher_response),
            stderr="",
        )

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 2, captured.err or captured.out
    assert len(calls) == 1
    rendered = json.loads(captured.out)
    assert rendered["status"] == "claim_progress_receipt_indeterminate"
    assert rendered["commit_state"] == "unknown"
    assert rendered["retry_safe"] is False
    assert rendered["dispatcher_returncode"] == 0
    assert rendered["expected"] == {
        "claim_id": claim_id,
        "prior_revision": 3,
        "committed_revision": 4,
    }
    assert rendered["current"] == {
        "claim_id": claim_id,
        "claim_revision": 4,
        "receipt_revision": 4,
        "projection_claim_id": claim_id,
        "projection_revision": 4,
    }
    assert "receipt" not in rendered
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


def test_claim_progress_committed_warning_receipt_passes_through_exactly_once(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-20260803-090000-task-ar-655-warning"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    dispatcher_response = _full_merge_dispatcher_response(tmp_path, claim_id)
    dispatcher_response["status"] = "heartbeat_committed_with_warnings"
    dispatcher_response["post_commit_warnings"] = [
        {
            "stage": "agent-instance-registry",
            "reason": "forced instance refresh failure",
        },
        {
            "stage": "claim-heartbeat-event",
            "reason": "forced pane event failure",
        },
    ]
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(dispatcher_response),
            stderr="warning details are carried by the JSON receipt",
        )

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    assert len(calls) == 1
    assert json.loads(captured.out) == dispatcher_response
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


@pytest.mark.parametrize(
    ("invented_pointer", "expected_rc"),
    ((False, 0), (True, 2)),
)
def test_claim_progress_overlay_projection_never_accepts_a_primary_pointer(
    tmp_path: Path,
    monkeypatch,
    capsys,
    invented_pointer: bool,
    expected_rc: int,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-AR655-OVERLAY-PROJECTION"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    claim_ref = f"agents/runtime/task_claims/{claim_id}.json"
    projection = {
        "status": "projection",
        "operation": "overlay-no-primary-pointer",
        "claim_id": claim_id,
        "claim_revision": 4,
        "task_claim_ref": claim_ref,
        "task_id": "TASK-AR-655-OVERLAY",
        "unit_id": None,
        "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
    }
    if invented_pointer:
        projection["pointer"] = {
            "active_task": "TASK-AR-655-OVERLAY",
            "active_claims": [claim_ref],
        }
    dispatcher_response = {
        "status": "heartbeated",
        "path": claim_ref,
        "claim": {
            "claim_id": claim_id,
            "mutation_revision": 4,
            "status": "claimed",
            "task_id": "TASK-AR-655-OVERLAY",
            "unit_id": None,
            "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
            "overlay": True,
        },
        "receipt": {"committed": True, "claim_revision": 4},
        "projection": projection,
    }

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout=json.dumps(dispatcher_response),
                stderr="",
            )
        ),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == expected_rc, captured.err or captured.out
    rendered = json.loads(captured.out)
    if invented_pointer:
        assert rendered["status"] == "claim_progress_receipt_indeterminate"
        assert rendered["retry_safe"] is False
    else:
        assert rendered == dispatcher_response
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


@pytest.mark.parametrize(
    "conflict",
    (
        "claim-unit-empty",
        "claim-taskset-empty",
        "claim-status-missing",
        "claim-status-inactive",
        "agent-claim-path-missing",
        "agent-claim-path-conflicting",
        "agent-status-missing",
        "agent-status-conflicting",
    ),
)
def test_claim_progress_zero_exit_rejects_incomplete_current_agent_authority(
    tmp_path: Path,
    monkeypatch,
    capsys,
    conflict: str,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-AR655-W4B-CURRENT-AGENT"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    claim_ref = f"agents/runtime/task_claims/{claim_id}.json"
    claim = {
        "claim_id": claim_id,
        "mutation_revision": 4,
        "status": "claimed",
        "task_id": "TASK-AR-655",
        "unit_id": "UNIT-TASK-AR-655-001",
        "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
    }
    current_agent = {
        "claim_id": claim_id,
        "mutation_revision": 4,
        "claim_path": claim_ref,
        "status": "claimed",
        "task_id": "TASK-AR-655",
        "unit_id": "UNIT-TASK-AR-655-001",
        "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
    }
    projection = {
        "status": "projection",
        "operation": "merge",
        "claim_id": claim_id,
        "claim_revision": 4,
        "task_claim_ref": claim_ref,
        "task_id": "TASK-AR-655",
        "unit_id": "UNIT-TASK-AR-655-001",
        "task_set_id": "TASKSET-AR-V080-OPERABILITY-HARDENING",
        "pointer": {
            "active_task": "TASK-AR-655",
            "active_task_set": "TASKSET-AR-V080-OPERABILITY-HARDENING",
            "active_claims": [claim_ref],
            "current_agents": [current_agent],
        },
    }
    if conflict == "claim-unit-empty":
        claim["unit_id"] = ""
        projection["unit_id"] = ""
        current_agent["unit_id"] = ""
    elif conflict == "claim-taskset-empty":
        claim["task_set_id"] = ""
        projection["task_set_id"] = ""
        projection["pointer"]["active_task_set"] = ""
        current_agent["task_set_id"] = ""
    elif conflict == "claim-status-missing":
        claim.pop("status")
    elif conflict == "claim-status-inactive":
        claim["status"] = "released"
        current_agent["status"] = "released"
    elif conflict == "agent-claim-path-missing":
        current_agent.pop("claim_path")
    elif conflict == "agent-claim-path-conflicting":
        current_agent["claim_path"] = (
            "agents/runtime/task_claims/CLAIM-OTHER.json"
        )
    elif conflict == "agent-status-missing":
        current_agent.pop("status")
    else:
        current_agent["status"] = "released"

    dispatcher_response = {
        "status": "heartbeated",
        "path": claim_ref,
        "claim": claim,
        "receipt": {"committed": True, "claim_revision": 4},
        "projection": projection,
    }
    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout=json.dumps(dispatcher_response),
                stderr="",
            )
        ),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 2, captured.err or captured.out
    rendered = json.loads(captured.out)
    assert rendered["status"] == "claim_progress_receipt_indeterminate"
    assert rendered["commit_state"] == "unknown"
    assert rendered["retry_safe"] is False
    assert rendered["dispatcher_returncode"] == 0
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


def test_claim_progress_accepts_full_production_dispatcher_merge_projection(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-AR655-W4B-FULL-POINTER-SUCCESS"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    dispatcher_response = _full_merge_dispatcher_response(tmp_path, claim_id)
    claim = dispatcher_response["claim"]
    projection = dispatcher_response["projection"]
    current_agent = projection["pointer"]["current_agents"][0]

    assert set(POINTER_AGENT_FIELDS).issubset(current_agent)
    for field in POINTER_AGENT_FIELDS:
        expected = (
            dispatcher_response["path"]
            if field == "claim_path"
            else claim[field]
        )
        assert current_agent[field] == expected
    for field in (
        "requested_model_tier",
        "selected_model_tier",
        "routing_policy_id",
        "routing_escalation_reason",
        "task_token_budget",
        "claim_token_budget",
    ):
        assert current_agent[field] == claim[field]

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout=json.dumps(dispatcher_response),
                stderr="",
            )
        ),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 0, captured.err or captured.out
    assert json.loads(captured.out) == dispatcher_response
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before


@pytest.mark.parametrize("mutation", ("missing", "conflicting"))
@pytest.mark.parametrize("field", POINTER_AGENT_FIELDS)
def test_claim_progress_rejects_every_unbound_canonical_pointer_agent_field(
    tmp_path: Path,
    monkeypatch,
    capsys,
    field: str,
    mutation: str,
) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    claim_id = "CLAIM-AR655-W4B-FULL-POINTER-RED"
    claim_path, claim_before, pointer_path, pointer_before = (
        _claim_progress_sentinels(tmp_path, claim_id)
    )
    dispatcher_response = _full_merge_dispatcher_response(tmp_path, claim_id)
    current_agent = dispatcher_response["projection"]["pointer"][
        "current_agents"
    ][0]
    if mutation == "missing":
        current_agent.pop(field)
    else:
        current_agent[field] = _conflicting_pointer_agent_value(
            field,
            current_agent[field],
        )

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *_args, **_kwargs: SimpleNamespace(
                returncode=0,
                stdout=json.dumps(dispatcher_response),
                stderr="",
            )
        ),
        raising=False,
    )

    rc = mod.main(_claim_progress_args(claim_id))

    captured = capsys.readouterr()
    assert rc == 2, captured.err or captured.out
    rendered = json.loads(captured.out)
    assert rendered["status"] == "claim_progress_receipt_indeterminate"
    assert rendered["commit_state"] == "unknown"
    assert rendered["retry_safe"] is False
    assert rendered["dispatcher_returncode"] == 0
    assert claim_path.read_bytes() == claim_before
    assert pointer_path.read_bytes() == pointer_before
