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
