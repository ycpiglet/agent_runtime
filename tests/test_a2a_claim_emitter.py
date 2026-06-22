"""Tests for live A2A emission wired into the claim lifecycle.

The A2A router (scripts/a2a_message_router.py) was complete + tested, but the
claim dispatch loop never called emit_message(), so the live stream
(agents/runtime/a2a/messages.jsonl) stayed empty. These tests pin the wiring:
a real claim create/release writes well-formed A2A messages whose chain the
trace gate can reconstruct, and emission never breaks the claim operation.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EMITTER_PATH = REPO_ROOT / "scripts" / "a2a_claim_emitter.py"
GATE_PATH = REPO_ROOT / "scripts" / "a2a_trace_gate.py"
DISPATCHER = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
LIVE_LOG = Path("agents") / "runtime" / "a2a" / "messages.jsonl"


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"module_{uuid.uuid4().hex}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_claim() -> dict:
    return {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-20260622-000000-task-ar-900-abcd",
        "task_id": "TASK-AR-900",
        "task_set_id": "TASKSET-AR-A2A",
        "agent_role": "lead-engineer",
        "agent_instance_id": "le-20260622-000000-utc-abcd",
        "display_name": "lead_engineer@work-01",
        "mode": "work",
        "status": "claimed",
        "claimed_at": "2026-06-22T00:00:00+00:00",
        "handoff_path": "agents/runtime/task_claims/CLAIM-x.handoff.md",
    }


def test_emit_claim_request_writes_wellformed_message(tmp_path: Path) -> None:
    emitter = _load_module(EMITTER_PATH)
    log_path = tmp_path / "agents" / "runtime" / "a2a" / "messages.jsonl"

    message = emitter.emit_claim_request(
        _sample_claim(), root=tmp_path, log_path=log_path
    )

    assert message is not None
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["schema_version"] == "agent-runtime-a2a-message/v1"
    assert row["event_type"] == "request"
    assert row["taskId"] == "TASK-AR-900"
    assert row["contextId"]  # derived, non-empty
    assert row["decision_cycle_id"]  # derived, non-empty
    assert row["parent_event_id"] == ""  # request opens the chain
    assert row["idempotency_key"]
    # route handoff: worker -> verifier
    assert row["route"]["from"] == row["sender"]
    assert row["route"]["to"] == row["receiver"]


def test_emit_request_is_idempotent_per_claim(tmp_path: Path) -> None:
    """A second emit for the same claim must not duplicate the request row."""
    emitter = _load_module(EMITTER_PATH)
    log_path = tmp_path / "messages.jsonl"
    claim = _sample_claim()

    first = emitter.emit_claim_request(claim, root=tmp_path, log_path=log_path)
    second = emitter.emit_claim_request(claim, root=tmp_path, log_path=log_path)

    rows = log_path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1  # duplicate suppressed, not raised
    assert first is not None
    assert second is None  # signals "already emitted"


def test_release_chain_completes_reconstructable_trace(tmp_path: Path) -> None:
    """create->request then release->review/decision/correction = full chain
    that a2a_trace_gate can reconstruct (status pass)."""
    emitter = _load_module(EMITTER_PATH)
    gate = _load_module(GATE_PATH)
    log_path = tmp_path / "messages.jsonl"
    claim = _sample_claim()

    emitter.emit_claim_request(claim, root=tmp_path, log_path=log_path)
    released = dict(claim)
    released["status"] = "released"
    released["released_at"] = "2026-06-22T01:00:00+00:00"
    messages = emitter.emit_claim_release_chain(
        released,
        root=tmp_path,
        log_path=log_path,
        verified_by="qa-20260622-000000-utc-zzzz",
        verifier_role="qa-reviewer",
        verification_evidence="reviews/TASK-AR-900-verify.json",
    )
    assert messages and len(messages) == 3  # review, decision, correction

    report = gate.evaluate(log_path)
    assert report["status"] == "pass", report["findings"]
    assert report["chains"] == 1
    assert report["chain_results"][0]["event_types"] == [
        "request",
        "review",
        "decision",
        "correction",
    ]


def test_emit_never_raises_on_router_failure(tmp_path: Path, monkeypatch) -> None:
    """An A2A emit failure must never break the claim operation."""
    emitter = _load_module(EMITTER_PATH)

    def _boom(*args, **kwargs):
        raise RuntimeError("router exploded")

    monkeypatch.setattr(emitter, "_emit_message", _boom)
    result = emitter.emit_claim_request(_sample_claim(), root=tmp_path, log_path=tmp_path / "m.jsonl")
    assert result is None  # swallowed, returns None


# --------------------------------------------------------------------------- CLI
# End-to-end: the real dispatcher CLI must emit live A2A traffic and the trace
# gate must reconstruct the chain from the LIVE stream (not the static baseline).


def _run_dispatcher(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DISPATCHER), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def test_dispatcher_create_release_emits_live_stream_trace_gate_passes(tmp_path: Path) -> None:
    gate = _load_module(GATE_PATH)
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-901")

    created = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-901",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "implement",
        "--now",
        "2026-06-22T09:00:00+09:00",
        "--suffix",
        "a2a1",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]

    live_log = tmp_path / LIVE_LOG
    assert live_log.exists(), "claim create must write the live A2A stream"
    rows = [json.loads(line) for line in live_log.read_text(encoding="utf-8").splitlines()]
    assert [r["event_type"] for r in rows] == ["request"]
    assert rows[0]["taskId"] == "TASK-AR-901"
    assert rows[0]["metadata"]["lifecycle"] == "claim_created"

    evidence_rel = "agents/runtime/task_claims/evidence/W4B.md"
    evidence = tmp_path / evidence_rel
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("# W4b\n- result: pass\n", encoding="utf-8")

    released = _run_dispatcher(
        tmp_path,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260622-091500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-22T09:15:00+09:00",
        "--json",
    )
    assert released.returncode == 0, released.stderr or released.stdout

    rows = [json.loads(line) for line in live_log.read_text(encoding="utf-8").splitlines()]
    assert [r["event_type"] for r in rows] == ["request", "review", "decision", "correction"]
    # the release-side events carry the real verifier identity in metadata
    review = next(r for r in rows if r["event_type"] == "review")
    assert review["metadata"]["verified_by"] == "qa-20260622-091500-kst-w4b1"
    assert review["metadata"]["verifier_role"] == "qa-reviewer"

    # The trace gate reconstructs the chain from the LIVE stream (status pass).
    report = gate.evaluate(live_log)
    assert report["status"] == "pass", report["findings"]
    assert report["chains"] == 1
    assert report["message_events"] == 4
    assert report["chain_results"][0]["event_types"] == [
        "request",
        "review",
        "decision",
        "correction",
    ]


def test_dispatcher_create_failure_does_not_emit(tmp_path: Path) -> None:
    """If claim creation is refused, no A2A request leaks into the live stream."""
    # No worktree -> non-orchestrator claim creation is refused.
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue\n", encoding="utf-8")
    refused = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-902",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-22T09:00:00+09:00",
        "--suffix",
        "a2a2",
        "--json",
    )
    assert refused.returncode == 1
    assert not (tmp_path / LIVE_LOG).exists()
