from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "self_improvement_cycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("self_improvement_cycle", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def claim(role: str, *, claim_id: str) -> dict:
    return {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": "TASK-1",
        "agent_role": role,
        "team_id": "agent-runtime-core",
        "status": "released",
        "phase": "taskset-completed",
        "progress_pct": 100,
        "last_heartbeat": "2026-06-17T08:00:00+09:00",
    }


def policy() -> dict:
    return {
        "schema": "agent-runtime-collaboration-governance/v1",
        "version": 1,
        "min_claims_for_role_coverage": 1,
        "minimum_claim_roles": {"scribe": 1},
        "monitored_roles": ["reviewer"],
        "required_review_artifacts": [],
        "required_root_capabilities": {},
        "lifecycle_thresholds": {
            "future_heartbeat_watch_minutes": 5,
            "released_claim_expected_phase": "taskset-completed",
            "released_claim_expected_progress_pct": 100,
        },
        "waiver_contract": {
            "directory": "agents/project/waivers",
            "schema": "agent-runtime-collaboration-waiver/v1",
            "required_fields": [
                "schema",
                "id",
                "subjects",
                "reason",
                "approved_by",
                "created_at",
                "expires_at",
                "mitigation",
            ],
        },
    }


def registry() -> dict:
    return {
        "schema": "agent-runtime-asset-registry/v1",
        "assets": [
            {
                "id": "skill.sleepy",
                "kind": "skill",
                "status": "active",
                "lifecycle": "keep",
                "paths": ["skills/sleepy/SKILL.md"],
                "evidence_paths": ["reviews/REVIEW-fixture.md"],
                "tokens": ["sleepy-skill-token"],
                "min_recent_uses": 1,
            }
        ],
    }


def write_fixture(root: Path) -> None:
    write_json(root / "agents/project/COLLABORATION-GOVERNANCE.json", policy())
    write_json(root / "agents/runtime/task_claims/CLAIM-qa.json", claim("qa", claim_id="CLAIM-qa"))
    write_json(
        root / "agents/project/waivers/WAIVER-scribe.json",
        {
            "schema": "agent-runtime-collaboration-waiver/v1",
            "id": "WAIVER-scribe",
            "subjects": ["role-usage:scribe"],
            "reason": "fixture waiver",
            "approved_by": "owner",
            "created_at": "2026-06-17T08:00:00+09:00",
            "expires_at": "2026-06-18T08:00:00+09:00",
            "mitigation": "create scribe claim evidence",
        },
    )
    write_json(root / "agents/project/RUNTIME-ASSET-REGISTRY.json", registry())
    write(root / "skills/sleepy/SKILL.md", "# Sleepy\n")
    write(root / "reviews/REVIEW-fixture.md", "review without the asset token\n")
    write(
        root / "agents/lead_engineer/STATUS.md",
        "## 현재 한 줄 요약\n" + "\n".join(f"- item {index}" for index in range(13)) + "\n",
    )


def test_assess_classifies_role_asset_and_advisory_gaps(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.assess(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))

    role_causes = {gap["role"]: gap["root_cause"] for gap in payload["collaboration"]["role_gaps"]}
    assert role_causes["scribe"] == "waiver_debt"
    assert role_causes["reviewer"] == "missing_claim_evidence"
    assert payload["runtime_assets"]["asset_gaps"][0]["root_cause"] == "no_usage_evidence"
    assert payload["advisory_signals"]["scribe"]["state"] == "due"
    assert payload["score"]["value"] < 100
    assert payload["maturity_level"] in {"immature", "improving"}


def test_assessment_can_be_mature_when_evidence_is_present(tmp_path: Path) -> None:
    module = load_module()
    mature_policy = policy()
    mature_policy["minimum_claim_roles"] = {"scribe": 1}
    mature_policy["monitored_roles"] = []
    write_json(tmp_path / "agents/project/COLLABORATION-GOVERNANCE.json", mature_policy)
    write_json(tmp_path / "agents/runtime/task_claims/CLAIM-scribe.json", claim("scribe", claim_id="CLAIM-scribe"))
    good_registry = registry()
    good_registry["assets"][0]["evidence_paths"] = ["reviews/REVIEW-fixture.md", "reviews/MEETING-fixture.md"]
    write_json(tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json", good_registry)
    write(tmp_path / "skills/sleepy/SKILL.md", "# Sleepy\n")
    write(tmp_path / "reviews/REVIEW-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "reviews/MEETING-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "agents/lead_engineer/STATUS.md", "## 현재 한 줄 요약\n- one\n")

    payload = module.assess(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))

    assert payload["maturity_level"] == "mature"
    assert payload["score"]["value"] == 100
    assert payload["collaboration"]["role_gaps"] == []
    assert payload["runtime_assets"]["asset_gaps"] == []


def test_assessment_uses_root_status_when_role_status_missing(tmp_path: Path) -> None:
    module = load_module()
    mature_policy = policy()
    mature_policy["minimum_claim_roles"] = {"scribe": 1}
    mature_policy["monitored_roles"] = []
    write_json(tmp_path / "agents/project/COLLABORATION-GOVERNANCE.json", mature_policy)
    write_json(tmp_path / "agents/runtime/task_claims/CLAIM-scribe.json", claim("scribe", claim_id="CLAIM-scribe"))
    good_registry = registry()
    good_registry["assets"][0]["evidence_paths"] = ["reviews/REVIEW-fixture.md", "reviews/MEETING-fixture.md"]
    write_json(tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json", good_registry)
    write(tmp_path / "skills/sleepy/SKILL.md", "# Sleepy\n")
    write(tmp_path / "reviews/REVIEW-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "reviews/MEETING-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "STATUS.md", "## 현재 한 줄 요약\n- one\n- two\n")

    payload = module.assess(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))

    assert payload["advisory_signals"]["scribe"]["state"] == "ok"
    assert payload["advisory_signals"]["scribe"]["hot_entries"] == 2


def test_cli_assess_json(tmp_path: Path) -> None:
    write_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-17T08:00:00+00:00",
            "assess",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "agent-runtime-self-improvement-assessment/v1"
    assert payload["collaboration"]["role_gaps"]
    assert payload["runtime_assets"]["asset_gaps"]


def test_cycle_dry_run_plans_every_required_surface_without_writing(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.cycle(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    assert payload["schema"] == "agent-runtime-self-improvement-cycle/v1"
    assert payload["status"] == "planned"
    assert payload["requires_compound"] is True
    kinds = {artifact["kind"] for artifact in payload["artifacts"]}
    assert {"review", "meeting", "seminar", "retro", "compound", "casebook"} <= kinds
    assert all(artifact["status"] == "planned" for artifact in payload["artifacts"])
    assert payload["assessment"]["role_gaps"] == 2
    assert payload["assessment"]["asset_gaps"] == 1
    assert not (tmp_path / "reviews/REVIEW-2026-06-17-self-improvement-cycle.md").exists()
    assert not (tmp_path / "agents/lead_engineer/compound_log.md").exists()


def test_cycle_write_mode_records_artifacts_and_casebook(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.cycle(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc),
        dry_run=False,
    )

    assert payload["status"] == "recorded"
    review = tmp_path / "reviews/REVIEW-2026-06-17-self-improvement-cycle.md"
    meeting = tmp_path / "reviews/MEETING-2026-06-17-self-improvement-cycle-sync.md"
    seminar = tmp_path / "reviews/SEMINAR-2026-06-17-self-improvement-cadence.md"
    retro = tmp_path / "reviews/RETRO-2026-06-17-self-improvement-cycle.md"
    compound = tmp_path / "agents/lead_engineer/compound_log.md"
    casebook = tmp_path / "agents/project/casebooks/failure-and-compound-casebook.md"
    for path in [review, meeting, seminar, retro, compound, casebook]:
        assert path.exists(), path

    review_text = review.read_text(encoding="utf-8")
    retro_text = retro.read_text(encoding="utf-8")
    assert "Next-Cycle Thresholds" in review_text
    assert "scribe" in review_text
    assert "doc_steward" in review_text
    assert "Section 5 Forward Actions" in retro_text
    assert "role-usage:scribe" in retro_text
    assert "COMPOUND-2026-06-17-001" in compound.read_text(encoding="utf-8")
    assert "CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT" in casebook.read_text(encoding="utf-8")

    dry_run_after_write = module.cycle(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 30, tzinfo=timezone.utc),
        dry_run=True,
    )
    assert dry_run_after_write["compound_id"] == "COMPOUND-2026-06-17-001"
    assert {artifact["status"] for artifact in dry_run_after_write["artifacts"]} == {"exists"}


def test_cycle_skips_compound_when_assessment_is_mature(tmp_path: Path) -> None:
    module = load_module()
    mature_policy = policy()
    mature_policy["minimum_claim_roles"] = {"scribe": 1}
    mature_policy["monitored_roles"] = []
    write_json(tmp_path / "agents/project/COLLABORATION-GOVERNANCE.json", mature_policy)
    write_json(tmp_path / "agents/runtime/task_claims/CLAIM-scribe.json", claim("scribe", claim_id="CLAIM-scribe"))
    good_registry = registry()
    good_registry["assets"][0]["evidence_paths"] = ["reviews/REVIEW-fixture.md", "reviews/MEETING-fixture.md"]
    write_json(tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json", good_registry)
    write(tmp_path / "skills/sleepy/SKILL.md", "# Sleepy\n")
    write(tmp_path / "reviews/REVIEW-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "reviews/MEETING-fixture.md", "sleepy-skill-token\n")
    write(tmp_path / "agents/lead_engineer/STATUS.md", "## 현재 한 줄 요약\n- one\n")

    payload = module.cycle(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    assert payload["assessment"]["maturity_level"] == "mature"
    assert payload["requires_compound"] is False
    kinds = {artifact["kind"] for artifact in payload["artifacts"]}
    assert "compound" not in kinds
    assert "casebook" not in kinds


def test_cli_cycle_dry_run_json(tmp_path: Path) -> None:
    write_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-17T08:00:00+00:00",
            "cycle",
            "--dry-run",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "agent-runtime-self-improvement-cycle/v1"
    assert payload["status"] == "planned"
    assert payload["artifacts"]


def test_assess_next_actions_shift_after_cycle_artifacts_exist(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    module.cycle(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))
    payload = module.assess(tmp_path, now=datetime(2026, 6, 17, 8, 30, tzinfo=timezone.utc))

    assert payload["product_surfaces"]["current_cycle"]["recorded"] is True
    assert not any(action.startswith("Run the cycle unit") for action in payload["next"])
    assert payload["next"]


def test_report_dry_run_marks_goal_active_when_evidence_is_immature(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    module.cycle(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))

    payload = module.report(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 30, tzinfo=timezone.utc),
        dry_run=True,
    )

    assert payload["schema"] == "agent-runtime-self-improvement-report/v1"
    assert payload["goal_state"]["complete"] is False
    assert payload["goal_state"]["operating_state"] == "cycle_recorded_but_evidence_immature"
    assert payload["artifact"]["status"] == "planned"
    assert payload["artifact"]["path"] == "reviews/REPORT-2026-06-17-self-improvement-maturity.md"
    assert "waiver_debt" in payload["goal_state"]["blocking_gates"]
    assert not (tmp_path / "reviews/REPORT-2026-06-17-self-improvement-maturity.md").exists()


def test_report_write_mode_records_maturity_report(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    module.cycle(tmp_path, now=datetime(2026, 6, 17, 8, 0, tzinfo=timezone.utc))

    payload = module.report(
        tmp_path,
        now=datetime(2026, 6, 17, 8, 30, tzinfo=timezone.utc),
    )

    report = tmp_path / "reviews/REPORT-2026-06-17-self-improvement-maturity.md"
    assert payload["status"] == "recorded"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "Persistent thread goal complete: `false`" in text
    assert "cycle_artifacts" in text
    assert "Maturity Gates" in text


def test_cli_report_dry_run_json(tmp_path: Path) -> None:
    write_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-17T08:00:00+00:00",
            "report",
            "--dry-run",
            "--json",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "agent-runtime-self-improvement-report/v1"
    assert payload["goal_state"]["complete"] is False
