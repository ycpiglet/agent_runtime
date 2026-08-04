"""W0~W6 lifecycle defaults (TASK-AR-506).

Covers the deferred-revalidation discipline as the default for all work:
- T0: `work.py new` auto-records the plan-assumption snapshot
  (and --no-plan-snapshot opts out);
- T2: `task_claim_dispatcher.py create` refuses claims on drifted anchors
  with replan guidance (--skip-plan-check is a loud escape);
- W0: `work.py status` prints claims + worktrees + in-flight summary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime import claim_store


SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
import work as work_module  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]
WORK = REPO_ROOT / "scripts" / "work.py"
CLAIM_DISPATCHER = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
PLAN_GATE = REPO_ROOT / "scripts" / "plan_assumption_gate.py"
REGISTRY_REL = "agents/project/work-items/PLAN-ASSUMPTIONS.json"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _registration_payload() -> dict[str, object]:
    return {
        "schema_version": "agent-runtime-work-registration/v1",
        "project_id": "PROJECT-TEST",
        "origin_type": "owner_request",
        "origin_ref": "reviews/REVIEW-LIFECYCLE-DESIGN.md",
        "created_by": "planner-test",
        "now": "2026-06-13T10:00:00+09:00",
        "initiative": {
            "id": "INIT-TEST-LIFECYCLE",
            "title": "Lifecycle Defaults Initiative",
            "summary": "Exercise the W0~W6 default lifecycle wiring.",
            "owner": "lead_engineer",
        },
        "taskset": {
            "id": "TASKSET-TEST-LIFECYCLE",
            "display_name": "Lifecycle Defaults Test",
            "summary": "Lifecycle defaults test taskset.",
            "order": 502,
            "plan_slug": "2026-06-13-test-lifecycle",
        },
        "tasks": [
            {
                "display_id": "TASK-AR-921",
                "title": "First lifecycle task",
                "goal": "Create the first task from structured input.",
                "target_files": ["scripts/lifecycle_gate.py", "docs/notes.md"],
                "acceptance": ["First task exists."],
                "verification": ["python scripts/task_identity.py check --check"],
            },
            {
                "display_id": "TASK-AR-922",
                "title": "Second lifecycle task",
                "goal": "Create the second task from structured input.",
                "acceptance": ["Second task exists."],
                "verification": ["python scripts/task_identity.py check --check"],
            },
        ],
    }


def _write_input(root: Path) -> Path:
    path = root / "registration.json"
    path.write_text(json.dumps(_registration_payload(), indent=2), encoding="utf-8")
    return path


def _register(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    input_path = _write_input(root)
    return _run(WORK, "--root", str(root), "new", "--input", str(input_path), "--json", *extra)


def _registry(root: Path) -> dict[str, object]:
    return json.loads((root / REGISTRY_REL).read_text(encoding="utf-8"))


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def _record_snapshot(root: Path, taskset_id: str = "TASKSET-T-LC") -> None:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "dispatcher.py").write_text("v1\n", encoding="utf-8")
    (root / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "reviews" / "REVIEW-LC.md").write_text("# design\n", encoding="utf-8")
    recorded = _run(
        PLAN_GATE,
        "--root",
        str(root),
        "record",
        "--taskset",
        taskset_id,
        "--design-record",
        "reviews/REVIEW-LC.md",
        "--anchor",
        "reviews/REVIEW-LC.md",
        "--anchor",
        "scripts/dispatcher.py",
    )
    assert recorded.returncode == 0, recorded.stderr or recorded.stdout


def _create_claim(root: Path, task_id: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return _run(
        CLAIM_DISPATCHER,
        "--root",
        str(root),
        "create",
        "--task-id",
        task_id,
        "--task-set-id",
        "TASKSET-T-LC",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T11:00:00+09:00",
        "--suffix",
        "lc1",
        "--json",
        *extra,
    )


# --- T0: registration auto-snapshot -----------------------------------------


def test_work_new_records_t0_snapshot_by_default(tmp_path: Path) -> None:
    result = _register(tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-new: pass" in result.stdout
    assert "plan-assumption-gate: recorded TASKSET-TEST-LIFECYCLE" in result.stdout

    registry = _registry(tmp_path)
    sets = registry["assumption_sets"]
    assert len(sets) == 1
    entry = sets[0]
    assert entry["taskset_id"] == "TASKSET-TEST-LIFECYCLE"
    # origin_ref does not exist in the tmp root, so the generated registration
    # review becomes the design record.
    review_rel = "reviews/REVIEW-2026-06-13-taskset-test-lifecycle-registration.md"
    assert entry["design_record"] == review_rel
    anchors = {anchor["path"]: anchor for anchor in entry["anchors"]}
    assert set(anchors) == {
        review_rel,
        "scripts/work.py",
        "scripts/task_claim_dispatcher.py",
        "scripts/lifecycle_gate.py",
    }
    # Non-script target_files are not anchored.
    assert "docs/notes.md" not in anchors
    # The generated review exists -> hashed; flow scripts absent in tmp root
    # -> pinned absent (drift when they appear).
    assert anchors[review_rel]["kind"] == "sha256"
    assert anchors["scripts/work.py"]["kind"] == "absent"

    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["plan_snapshot"]["status"] == "recorded"
    assert payload["plan_snapshot"]["taskset_id"] == "TASKSET-TEST-LIFECYCLE"


def test_work_new_no_plan_snapshot_opt_out(tmp_path: Path) -> None:
    result = _register(tmp_path, "--no-plan-snapshot")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "plan-snapshot: skipped (--no-plan-snapshot)" in result.stdout
    assert not (tmp_path / REGISTRY_REL).exists()
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["plan_snapshot"] == {"status": "skipped", "reason": "--no-plan-snapshot"}


def test_work_new_rerun_preserves_existing_snapshot(tmp_path: Path) -> None:
    first = _register(tmp_path)
    assert first.returncode == 0, first.stderr or first.stdout
    before = (tmp_path / REGISTRY_REL).read_text(encoding="utf-8")

    second = _register(tmp_path)

    assert second.returncode == 0, second.stderr or second.stdout
    assert "plan-snapshot: skipped (records already existed" in second.stdout
    # Idempotent re-registration must not silently re-anchor (mask drift).
    assert (tmp_path / REGISTRY_REL).read_text(encoding="utf-8") == before


# --- T2: dispatch drift check ------------------------------------------------


def test_claim_create_refused_on_plan_drift_with_replan_guidance(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-931")
    _record_snapshot(tmp_path)
    (tmp_path / "scripts" / "dispatcher.py").write_text("v2-merged\n", encoding="utf-8")

    refused = _create_claim(tmp_path, "TASK-AR-931")

    assert refused.returncode == 1
    assert "plan assumption drift detected for TASKSET-T-LC" in refused.stderr
    assert "claim creation refused (T2 dispatch gate)" in refused.stderr
    assert "anchor-hash-changed:scripts/dispatcher.py" in refused.stderr
    assert "replan review" in refused.stderr
    assert "--skip-plan-check" in refused.stderr
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    assert not claim_dir.exists() or not list(claim_dir.glob("*.json"))


def test_claim_create_skip_plan_check_warns_and_proceeds(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-931")
    _record_snapshot(tmp_path)
    (tmp_path / "scripts" / "dispatcher.py").write_text("v2-merged\n", encoding="utf-8")

    created = _create_claim(tmp_path, "TASK-AR-931", "--skip-plan-check")

    assert created.returncode == 0, created.stderr or created.stdout
    assert "WARNING" in created.stderr
    assert "--skip-plan-check" in created.stderr
    assert "anchor-hash-changed:scripts/dispatcher.py" in created.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_claim_create_clean_snapshot_passes_t2(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-931")
    _record_snapshot(tmp_path)

    created = _create_claim(tmp_path, "TASK-AR-931")

    assert created.returncode == 0, created.stderr or created.stdout
    assert "plan-assumption-gate: pass (TASKSET-T-LC)" in created.stderr
    payload = json.loads(created.stdout)
    assert payload["claim"]["task_set_id"] == "TASKSET-T-LC"


def test_claim_create_without_snapshot_notes_missing_t0(tmp_path: Path) -> None:
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-931")

    created = _create_claim(tmp_path, "TASK-AR-931")

    assert created.returncode == 0, created.stderr or created.stdout
    assert "no plan-assumption snapshot recorded for TASKSET-T-LC" in created.stderr
    claim_files = list((tmp_path / "agents" / "runtime" / "task_claims").glob("*.json"))
    assert len(claim_files) == 1


def test_registration_snapshot_then_dispatch_end_to_end(tmp_path: Path) -> None:
    """T0 at registration feeds T2 at dispatch without any manual step."""
    registered = _register(tmp_path)
    assert registered.returncode == 0, registered.stderr or registered.stdout
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    _write_worktree(tmp_path, "TASK-AR-921")
    _write_worktree(tmp_path, "TASK-AR-922")

    first = _run(
        CLAIM_DISPATCHER,
        "--root",
        str(tmp_path),
        "create",
        "--task-id",
        "TASK-AR-921",
        "--task-set-id",
        "TASKSET-TEST-LIFECYCLE",
        "--agent-role",
        "lead-engineer",
        "--now",
        "2026-06-13T12:00:00+09:00",
        "--suffix",
        "e2e1",
        "--json",
    )
    assert first.returncode == 0, first.stderr or first.stdout
    assert "plan-assumption-gate: pass (TASKSET-TEST-LIFECYCLE)" in first.stderr

    # A merge-shaped change lands on an anchored design record -> drift.
    review_rel = "reviews/REVIEW-2026-06-13-taskset-test-lifecycle-registration.md"
    review = tmp_path / review_rel
    review.write_text(review.read_text(encoding="utf-8") + "\nchanged by merge\n", encoding="utf-8")

    second = _run(
        CLAIM_DISPATCHER,
        "--root",
        str(tmp_path),
        "create",
        "--task-id",
        "TASK-AR-922",
        "--task-set-id",
        "TASKSET-TEST-LIFECYCLE",
        "--agent-role",
        "lead-engineer",
        "--allow-parallel-task-set",
        "--now",
        "2026-06-13T12:05:00+09:00",
        "--suffix",
        "e2e2",
        "--json",
    )
    assert second.returncode == 1
    assert "plan assumption drift detected for TASKSET-TEST-LIFECYCLE" in second.stderr
    assert f"anchor-hash-changed:{review_rel}" in second.stderr


# --- W0: status visibility ---------------------------------------------------


def _write_claim(root: Path, *, task_id: str, status: str, suffix: str) -> Path:
    claim_dir = root / "agents" / "runtime" / "task_claims"
    claim_dir.mkdir(parents=True, exist_ok=True)
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": f"CLAIM-20260613-{suffix}-{task_id.lower()}",
        "task_id": task_id,
        "task_set_id": "TASKSET-T-LC",
        "agent_role": "lead-engineer",
        "agent_instance_id": f"le-20260613-{suffix}",
        "display_name": f"lead_engineer@work-{suffix}",
        "status": status,
        "worktree_path": f".worktrees/{task_id}",
        "branch": f"codex/{task_id.lower()}-work",
    }
    path = claim_dir / f"{claim['claim_id']}.json"
    path.write_text(
        json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    inspection = claim_store.inspect_store(root)
    if inspection.state == "migration-required":
        claim_store.initialize_store(root, witness_claim_id=str(claim["claim_id"]))
    return path


def test_work_status_lists_active_claims_and_inflight_summary(tmp_path: Path) -> None:
    _write_claim(tmp_path, task_id="TASK-AR-930", status="claimed", suffix="01")
    _write_claim(tmp_path, task_id="TASK-AR-931", status="released", suffix="02")

    workload = work_module._active_claim_workload(tmp_path)

    result = _run(WORK, "--root", str(tmp_path), "status")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-status: ok" in result.stdout
    assert "active_claims=1" in result.stdout
    assert "task=TASK-AR-930" in result.stdout
    assert "status=claimed" in result.stdout
    assert "agent=lead_engineer@work-01" in result.stdout
    assert "worktree=.worktrees/TASK-AR-930" in result.stdout
    # Released claims are not listed.
    assert "TASK-AR-931" not in result.stdout
    assert "worktrees=" in result.stdout
    assert "inflight:" in result.stdout
    assert workload == {
        "active_claim_count": 1,
        "by_team": {"unassigned": 1},
        "by_role": {"lead-engineer": 1},
    }


def test_work_status_json_shape(tmp_path: Path) -> None:
    _write_claim(tmp_path, task_id="TASK-AR-930", status="in_progress", suffix="03")

    result = _run(WORK, "--root", str(tmp_path), "status", "--json")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert set(payload) >= {"status", "root", "active_claims", "worktrees", "inflight"}
    assert len(payload["active_claims"]) == 1
    claim = payload["active_claims"][0]
    assert claim["task_id"] == "TASK-AR-930"
    assert claim["status"] == "in_progress"
    assert claim["worktree_path"] == ".worktrees/TASK-AR-930"
    assert payload["inflight"]["summary"].startswith("inflight:")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        pytest.param("task_id", ["TASK-AR-930"], id="list-task-id"),
        pytest.param(
            "task_set_id",
            {"id": "TASKSET-T-LC"},
            id="mapping-task-set-id",
        ),
        pytest.param("agent_instance_id", True, id="bool-agent-instance-id"),
        pytest.param("task_id", 930, id="number-task-id"),
        pytest.param("agent_instance_id", None, id="null-agent-instance-id"),
        pytest.param("agent_instance_id", "", id="blank-agent-instance-id"),
    ),
)
def test_work_status_rejects_present_malformed_core_identity_without_mutation(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    claim_path = _write_claim(
        tmp_path,
        task_id="TASK-AR-930",
        status="claimed",
        suffix=f"malformed-{field}",
    )
    payload = json.loads(claim_path.read_text(encoding="utf-8"))
    payload[field] = value
    if field == "agent_instance_id":
        payload.pop("display_name")
    claim_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    result = _run(WORK, "--root", str(tmp_path), "status", "--json")

    assert result.returncode == 1, result.stdout or result.stderr
    assert "work-status: fail" in result.stderr
    assert "active-claim-context-invalid" in result.stderr
    assert {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == before


def test_work_status_shares_one_canonical_claim_snapshot_with_inflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim_path = _write_claim(
        tmp_path,
        task_id="TASK-AR-933",
        status="claimed",
        suffix="shared-snapshot",
    )
    snapshot = work_module._canonical_claim_snapshot(
        tmp_path,
        surface="test-shared-snapshot",
    )
    reads = 0
    received: list[list[dict[str, object]] | None] = []

    def read_once(_root: Path, *, surface: str) -> list[dict[str, object]]:
        nonlocal reads
        assert surface == "work-status"
        reads += 1
        if reads > 1:
            raise AssertionError("W0 attempted a second claim-store snapshot")
        return snapshot

    def overlay_from_snapshot(
        _root: Path,
        base: str | None = None,
        *,
        claim_snapshot: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        del base
        received.append(claim_snapshot)
        index = work_module.inflight_overlay.claim_index_from_snapshot(
            claim_snapshot or []
        )
        assert index["TASK-AR-933"] == {
            "claim_status": "active",
            "claim_id": claim_path.stem,
        }
        return {
            "summary": {
                "divergent_tasks": 0,
                "divergent_records": 0,
                "branches_with_divergence": 0,
                "claimless": 0,
            }
        }

    monkeypatch.setattr(work_module, "_canonical_claim_snapshot", read_once)
    monkeypatch.setattr(work_module.inflight_overlay, "build_overlay", overlay_from_snapshot)

    result = work_module.status_work(tmp_path)

    assert reads == 1
    assert received == [snapshot]
    assert [row["claim_id"] for row in result["active_claims"]] == [claim_path.stem]
    assert result["inflight"]["counts"]["claimless"] == 0


def test_work_status_empty_root(tmp_path: Path) -> None:
    result = _run(WORK, "--root", str(tmp_path), "status")

    assert result.returncode == 0, result.stderr or result.stdout
    assert "work-status: ok" in result.stdout
    assert "active_claims=0" in result.stdout


@pytest.mark.parametrize("invalid_state", ("duplicate-status", "unknown-status", "one-sided-marker"))
def test_work_status_rows_and_workload_fail_closed_on_claim_integrity(
    tmp_path: Path,
    invalid_state: str,
) -> None:
    claim_path = _write_claim(
        tmp_path,
        task_id="TASK-AR-932",
        status="claimed",
        suffix=invalid_state,
    )
    if invalid_state == "duplicate-status":
        claim_path.write_text(
            '{"schema":"agent-runtime-task-claim/v1",'
            f'"claim_id":"{claim_path.stem}",'
            '"status":"claimed","status":"released"}\n',
            encoding="utf-8",
        )
    elif invalid_state == "unknown-status":
        payload = json.loads(claim_path.read_text(encoding="utf-8"))
        payload["status"] = "mystery"
        claim_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        (tmp_path / "agents/runtime/task_claims/.claim-store").unlink()

    with pytest.raises(work_module.WorkRegistrationError):
        work_module._active_claim_rows(tmp_path)
    with pytest.raises(work_module.WorkRegistrationError):
        work_module._active_claim_workload(tmp_path)

    result = _run(WORK, "--root", str(tmp_path), "status", "--json")

    assert result.returncode == 1
    assert "work-status: fail" in result.stderr
    assert "active-claim-context-invalid" in result.stderr
