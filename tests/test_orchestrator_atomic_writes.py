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
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_orchestrator.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("agent_orchestrator_under_test", ORCHESTRATOR)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves InitVar annotations via sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
    dispatcher_response = {
        "status": "heartbeated",
        "receipt": {"committed": True, "claim_revision": 4},
        "projection": {"claim_revision": 4, "operation": "merge"},
    }

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
