from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
GATE = SCRIPTS_DIR / "attribution_gate.py"
PANE_EVENT_LOG = SCRIPTS_DIR / "pane_event_log.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_instance_registry import record_claim_instance  # noqa: E402
from pane_event_log import append_census_event, census, load_events  # noqa: E402


HISTORICAL_TS = "2026-06-10T12:00:00+09:00"
POST_CUTOFF_TS = "2026-06-13T12:00:00+09:00"


def _run(script: Path, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return path


def _claim_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": "CLAIM-20260613-120000-task-ar-901-aa11",
        "task_id": "TASK-AR-901",
        "agent_role": "qa",
        "team_id": "evaluation-office",
        "agent_instance_id": "qa-20260613-120000-kst-aa11",
        "display_name": "qa@review-01",
        "callsite_id": "terminal:wt-task-ar-901:tab-01",
        "pane_id": "terminal:wt-task-ar-901:tab-01",
        "status": "claimed",
        "task_set_id": "TASKSET-TEST",
        "project_id": "PROJECT-TEST",
        "unit_id": "UNIT-TASK-AR-901-001",
        "worktree_path": ".worktrees/TASK-AR-901",
        "claimed_at": POST_CUTOFF_TS,
        "updated_at": POST_CUTOFF_TS,
    }
    payload.update(overrides)
    return payload


def _write_claim(root: Path, payload: dict[str, object]) -> Path:
    return _write_json(root / "agents" / "runtime" / "task_claims" / f"{payload['claim_id']}.json", payload)


def _write_instance(root: Path, agent_instance_id: str, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema": "agent-runtime-agent-instance/v1",
        "agent_instance_id": agent_instance_id,
        "role": "qa",
        "spawned_at": POST_CUTOFF_TS,
    }
    payload.update(overrides)
    return _write_json(root / "agents" / "runtime" / "instances" / f"{agent_instance_id}.json", payload)


# -- claims ------------------------------------------------------------------


def test_role_only_claim_blocks_after_cutoff_and_watches_before(tmp_path: Path) -> None:
    _write_claim(
        tmp_path,
        _claim_payload(
            claim_id="CLAIM-20260613-120000-task-ar-901-aa11",
            agent_instance_id="",
            claimed_at=POST_CUTOFF_TS,
            updated_at=POST_CUTOFF_TS,
        ),
    )
    result = _run(GATE, tmp_path, "--check")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "attribution-gate: fail" in result.stdout
    assert "block agents/runtime/task_claims/CLAIM-20260613-120000-task-ar-901-aa11.json: attribution:claim-role-only" in result.stdout

    historical = tmp_path / "historical"
    _write_claim(
        historical,
        _claim_payload(
            claim_id="CLAIM-20260610-120000-task-ar-900-bb22",
            agent_instance_id="",
            claimed_at=HISTORICAL_TS,
            updated_at=HISTORICAL_TS,
        ),
    )
    result = _run(GATE, historical, "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "attribution-gate: pass" in result.stdout
    assert "watch agents/runtime/task_claims/CLAIM-20260610-120000-task-ar-900-bb22.json: attribution:claim-role-only" in result.stdout


def test_instance_attributed_claim_passes(tmp_path: Path) -> None:
    claim = _claim_payload()
    _write_claim(tmp_path, claim)
    _write_instance(tmp_path, str(claim["agent_instance_id"]))

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "attribution-gate: pass" in result.stdout
    assert "findings=0" in result.stdout


# -- pane events ---------------------------------------------------------------


def test_pane_event_role_only_actor_watch_then_block_by_cutoff(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl",
        [
            {"schema": "agent-runtime-pane-event/v1", "seq": 1, "ts": HISTORICAL_TS, "event": "claim_created", "actor": "qa"},
            {"schema": "agent-runtime-pane-event/v1", "seq": 2, "ts": POST_CUTOFF_TS, "event": "claim_created", "actor": "qa"},
            {
                "schema": "agent-runtime-pane-event/v1",
                "seq": 3,
                "ts": POST_CUTOFF_TS,
                "event": "claim_created",
                "actor": "qa-20260613-120000-kst-aa11",
                "agent_instance_id": "qa-20260613-120000-kst-aa11",
            },
        ],
    )

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "watch agents/runtime/pane_events/pane-events.jsonl:1: attribution:pane-event-role-only:qa" in result.stdout
    assert "block agents/runtime/pane_events/pane-events.jsonl:2: attribution:pane-event-role-only:qa" in result.stdout
    assert "pane-events.jsonl:3" not in result.stdout


# -- a2a -----------------------------------------------------------------------


def test_a2a_role_only_parties_block_after_cutoff_and_instance_parties_pass(tmp_path: Path) -> None:
    _write_instance(tmp_path, "le-20260613-120000-kst-cc33", role="lead-engineer")
    _write_jsonl(
        tmp_path / "agents" / "project" / "a2a" / "a2a-trace-2026-06-13.jsonl",
        [
            {"timestamp": POST_CUTOFF_TS, "sender": "qa", "receiver": "lead-engineer"},
            {"timestamp": HISTORICAL_TS, "sender": "qa", "receiver": "lead-engineer"},
            {
                "timestamp": POST_CUTOFF_TS,
                "sender": "le-20260613-120000-kst-cc33",
                "receiver": "qa",
                "receiver_instance_id": "qa-20260613-120000-kst-aa11",
            },
        ],
    )

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "block agents/project/a2a/a2a-trace-2026-06-13.jsonl:1: attribution:a2a-role-only:sender:qa" in result.stdout
    assert "block agents/project/a2a/a2a-trace-2026-06-13.jsonl:1: attribution:a2a-role-only:receiver:lead-engineer" in result.stdout
    assert "watch agents/project/a2a/a2a-trace-2026-06-13.jsonl:2: attribution:a2a-role-only:sender:qa" in result.stdout
    assert "a2a-trace-2026-06-13.jsonl:3" not in result.stdout


# -- evidence --------------------------------------------------------------------


def test_evidence_role_only_blocks_after_cutoff_and_tool_actor_stays_watch(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "evidence" / "verification" / "V-1.json",
        {"verified_at": POST_CUTOFF_TS, "verified_by": "qa"},
    )
    _write_json(
        tmp_path / "reviews" / "VERIFY-2026-06-13-sample.json",
        {"verified_at": POST_CUTOFF_TS, "verified_by": "codex"},
    )
    _write_json(
        tmp_path / "agents" / "project" / "evidence" / "verification" / "V-2.json",
        {
            "verified_at": POST_CUTOFF_TS,
            "verified_by": "qa",
            "agent_instance_id": "qa-20260613-120000-kst-aa11",
        },
    )

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "block agents/project/evidence/verification/V-1.json: attribution:evidence-role-only:verified_by:qa" in result.stdout
    assert "watch reviews/VERIFY-2026-06-13-sample.json: attribution:evidence-actor-unresolved:verified_by:codex" in result.stdout
    assert "V-2.json" not in result.stdout


def test_evidence_nested_events_are_checked(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "agents" / "project" / "evidence" / "a2a" / "LIFECYCLE-2026-06-13.json",
        {
            "generated_at": POST_CUTOFF_TS,
            "agent_instance_id": "qa-20260613-120000-kst-aa11",
            "events": [{"ts": POST_CUTOFF_TS, "actor_role": "qa"}],
        },
    )

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "block agents/project/evidence/a2a/LIFECYCLE-2026-06-13.json#events[0]: attribution:evidence-role-only:actor_role:qa" in result.stdout


# -- causal links -----------------------------------------------------------------


def test_causal_links_validate_parent_instance_and_on_behalf_of(tmp_path: Path) -> None:
    claim = _claim_payload(
        parent_instance_id="inst-missing-parent",
        on_behalf_of="UNIT-NOPE-999",
    )
    _write_claim(tmp_path, claim)
    _write_instance(tmp_path, str(claim["agent_instance_id"]))

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "attribution:claim-parent-instance-missing:inst-missing-parent" in result.stdout
    assert "attribution:claim-on-behalf-of-unresolved:UNIT-NOPE-999" in result.stdout

    valid = tmp_path / "valid"
    claim = _claim_payload(
        parent_instance_id="le-20260613-120000-kst-cc33",
        on_behalf_of="UNIT-TASK-AR-901-001",
    )
    _write_claim(valid, claim)
    _write_instance(valid, str(claim["agent_instance_id"]))
    _write_instance(valid, "le-20260613-120000-kst-cc33", role="lead-engineer")

    result = _run(GATE, valid, "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "findings=0" in result.stdout


def test_instance_record_causal_links_are_validated(tmp_path: Path) -> None:
    _write_instance(
        tmp_path,
        "qa-20260613-120000-kst-aa11",
        parent_instance_id="inst-missing-parent",
    )

    result = _run(GATE, tmp_path, "--check")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "attribution:instance-parent-instance-missing:inst-missing-parent" in result.stdout


# -- lifecycle census ----------------------------------------------------------------


def test_census_append_and_point_in_time_query(tmp_path: Path) -> None:
    append_census_event(
        tmp_path,
        "instance_spawned",
        agent_instance_id="qa-20260613-120000-kst-aa11",
        actor_role="qa",
        display_name="qa@review-01",
        task_id="TASK-AR-901",
        task_set_id="TASKSET-TEST",
        ts="2026-06-13T12:00:00+09:00",
    )
    append_census_event(
        tmp_path,
        "instance_heartbeat",
        agent_instance_id="qa-20260613-120000-kst-aa11",
        ts="2026-06-13T12:30:00+09:00",
    )
    append_census_event(
        tmp_path,
        "instance_terminated",
        agent_instance_id="qa-20260613-120000-kst-aa11",
        ts="2026-06-13T13:00:00+09:00",
    )

    events = load_events(tmp_path)
    assert [event["event"] for event in events] == [
        "instance_spawned",
        "instance_heartbeat",
        "instance_terminated",
    ]
    assert all(event["agent_instance_id"] == "qa-20260613-120000-kst-aa11" for event in events)
    assert all(event["actor"] == "qa-20260613-120000-kst-aa11" for event in events)

    midpoint = census(events, at="2026-06-13T12:45:00+09:00")
    assert midpoint["summary"] == {"instance_count": 1, "active_count": 1, "terminated_count": 0}
    assert midpoint["instances"][0]["active"] is True
    assert midpoint["instances"][0]["actor_role"] == "qa"
    assert midpoint["instances"][0]["task_id"] == "TASK-AR-901"

    final = census(events)
    assert final["summary"] == {"instance_count": 1, "active_count": 0, "terminated_count": 1}
    assert final["instances"][0]["terminated_at"] == "2026-06-13T13:00:00+09:00"


def test_census_cli_record_and_query(tmp_path: Path) -> None:
    recorded = _run(
        PANE_EVENT_LOG,
        tmp_path,
        "census-record",
        "--event",
        "instance_spawned",
        "--agent-instance-id",
        "le-20260613-120000-kst-cc33",
        "--actor-role",
        "lead-engineer",
        "--now",
        "2026-06-13T12:00:00+09:00",
        "--json",
    )
    assert recorded.returncode == 0, recorded.stderr or recorded.stdout
    payload = json.loads(recorded.stdout)
    assert payload["event"]["event"] == "instance_spawned"
    assert payload["event"]["agent_instance_id"] == "le-20260613-120000-kst-cc33"

    queried = _run(PANE_EVENT_LOG, tmp_path, "census", "--json")
    assert queried.returncode == 0, queried.stderr or queried.stdout
    result = json.loads(queried.stdout)
    assert result["summary"]["active_count"] == 1
    assert result["instances"][0]["agent_instance_id"] == "le-20260613-120000-kst-cc33"


def test_census_record_rejects_non_census_event_and_missing_instance(tmp_path: Path) -> None:
    try:
        append_census_event(tmp_path, "claim_created", agent_instance_id="x")
        raise AssertionError("expected ValueError for non-census event")
    except ValueError:
        pass
    try:
        append_census_event(tmp_path, "instance_spawned", agent_instance_id="  ")
        raise AssertionError("expected ValueError for missing agent_instance_id")
    except ValueError:
        pass


# -- spawn record ----------------------------------------------------------------------


def test_spawn_record_roundtrips_skill_versions_and_prompt_config_hash(tmp_path: Path) -> None:
    claim = _claim_payload()
    claim_path = _write_claim(tmp_path, claim)

    path, payload = record_claim_instance(
        tmp_path,
        claim,
        claim_path=claim_path,
        skill_versions={"qa": "1.2.0", "skeptic": "0.4.1"},
        prompt_config_hash="sha256:abc123",
    )

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["skill_versions"] == {"qa": "1.2.0", "skeptic": "0.4.1"}
    assert stored["prompt_config_hash"] == "sha256:abc123"
    assert payload["skill_versions"] == {"qa": "1.2.0", "skeptic": "0.4.1"}

    events = load_events(tmp_path)
    spawned = [event for event in events if event["event"] == "instance_spawned"]
    assert len(spawned) == 1
    assert spawned[0]["agent_instance_id"] == claim["agent_instance_id"]
    assert spawned[0]["actor"] == claim["agent_instance_id"]
    assert spawned[0]["actor_role"] == "qa"
    assert spawned[0]["claim_id"] == claim["claim_id"]
    assert spawned[0]["task_id"] == claim["task_id"]
    assert spawned[0]["ts"] == claim["claimed_at"]
    # Census event must not duplicate full claim payload fields.
    assert "model_tier" not in spawned[0]
    assert "unit_spec" not in spawned[0]

    # Idempotent re-record: refs unchanged, no duplicate spawn event.
    path, payload = record_claim_instance(tmp_path, claim, claim_path=claim_path)
    assert payload["skill_versions"] == {"qa": "1.2.0", "skeptic": "0.4.1"}
    assert payload["prompt_config_hash"] == "sha256:abc123"
    events = load_events(tmp_path)
    assert len([event for event in events if event["event"] == "instance_spawned"]) == 1

    gate = _run(GATE, tmp_path, "--check")
    assert gate.returncode == 0, gate.stdout + gate.stderr
    assert "findings=0" in gate.stdout


def test_spawn_record_reads_claim_embedded_fields_without_kwargs(tmp_path: Path) -> None:
    claim = _claim_payload(
        skill_versions={"qa": "2.0.0"},
        prompt_config_hash="sha256:def456",
    )
    claim_path = _write_claim(tmp_path, claim)

    path, _ = record_claim_instance(tmp_path, claim, claim_path=claim_path, emit_spawn_event=False)

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["skill_versions"] == {"qa": "2.0.0"}
    assert stored["prompt_config_hash"] == "sha256:def456"
    assert load_events(tmp_path) == []


# -- wiring ---------------------------------------------------------------------------------


def test_owner_governance_runs_attribution_gate_in_both_copies() -> None:
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")
    assert '"scripts/attribution_gate.py", "--check"' in root_gate
    assert '"scripts/attribution_gate.py", "--check"' in template_gate


def test_template_mirrors_match_root_scripts() -> None:
    template_scripts = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts"
    for name in ("attribution_gate.py", "pane_event_log.py", "agent_instance_registry.py"):
        root_text = (REPO_ROOT / "scripts" / name).read_text(encoding="utf-8")
        template_text = (template_scripts / name).read_text(encoding="utf-8")
        assert root_text == template_text, f"template mirror out of sync: {name}"


def test_attribution_gate_passes_on_real_repo() -> None:
    result = _run(GATE, REPO_ROOT, "--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "attribution-gate: pass" in result.stdout
    assert "block=0" in result.stdout
