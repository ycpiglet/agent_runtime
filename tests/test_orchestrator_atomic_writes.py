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


def test_kill_notifies_only_an_explicit_completed_outcome(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)
    agent_id = "agent_0123456789ab"
    mod.write_session_json(
        tmp_path / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": "TASK-123", "status": "active"},
    )
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        mod.allimbot,
        "notify",
        lambda message, title="agent_runtime", **_kwargs: calls.append((message, title)) or False,
    )

    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="completed"))

    assert outcome.code == 0
    record = json.loads((tmp_path / f"{agent_id}.json").read_text(encoding="utf-8"))
    assert record["status"] == "closed"
    assert record["outcome"] == "completed"
    assert calls == [("TASK-123 completed", "agent_runtime task completed")]


def test_kill_default_stop_does_not_claim_task_completion(tmp_path: Path, monkeypatch) -> None:
    mod = _load()
    monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)
    agent_id = "agent_abcdef012345"
    mod.write_session_json(
        tmp_path / f"{agent_id}.json",
        {"agent_id": agent_id, "task_id": "TASK-456", "status": "active"},
    )

    def unexpected_notify(*_args, **_kwargs):
        raise AssertionError("a stopped session is not a completed task")

    monkeypatch.setattr(mod.allimbot, "notify", unexpected_notify)
    outcome = mod.cmd_kill(Namespace(agent_id=agent_id, dry_run=False, outcome="stopped"))
    assert outcome.code == 0
    record = json.loads((tmp_path / f"{agent_id}.json").read_text(encoding="utf-8"))
    assert record["status"] == "stopping"
    assert record["outcome"] == "stopped"
