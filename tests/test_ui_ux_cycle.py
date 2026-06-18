from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "ui_ux_cycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ui_ux_cycle", SCRIPT)
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


def write_task(root: Path, task_id: str, *, target_files: list[str] | None = None, status: str = "planned") -> None:
    lines = [
        "---",
        f"id: {task_id}",
        f"title: {task_id} semantic token work",
        f"status: {status}",
        "priority: P2",
        "team: ui-ux",
        "owner: lead_engineer",
        "task_set_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION",
        "summary: Replace transitional UI token aliases with a semantic design-system scale.",
    ]
    if target_files:
        lines.append("target_files:")
        lines.extend(f"  - {item}" for item in target_files)
    lines.extend(["---", "", "# Task", ""])
    write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md", "\n".join(lines))


def write_gate(root: Path, *, status: str = "pass") -> None:
    gate = root / "scripts" / "design_system_gate.py"
    gate.parent.mkdir(parents=True, exist_ok=True)
    gate.write_text(
        "import json\n"
        f"print(json.dumps({{'status': {status!r}, 'scanned': 3, 'findings': []}}))\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def write_org(root: Path) -> None:
    write(
        root / "agents" / "project" / "ORG-MODEL.yml",
        "\n".join(
            [
                "roles:",
                "  - id: lead-designer",
                "  - id: design-system-steward",
                "  - id: interface-designer",
                "  - id: ux-evaluator",
            ]
        ),
    )


def write_fixture(root: Path, *, conflict: bool = False) -> None:
    write_gate(root)
    write_org(root)
    write_task(root, "TASK-AR-583", target_files=["src/agent_runtime/ui_console_assets.py"])
    write_task(root, "TASK-AR-584", target_files=["src/agent_runtime/ui_design_assets.py"])
    write(root / "reviews" / "SEMINAR-2026-06-18-ui-cycle.md", "UI design seminar\n")
    if conflict:
        write_json(
            root / "agents" / "runtime" / "task_claims" / "CLAIM-conflict.json",
            {
                "claim_id": "CLAIM-conflict",
                "task_id": "TASK-OTHER",
                "status": "claimed",
                "agent_role": "lead-engineer",
                "target_files": ["src/agent_runtime/ui_console_assets.py"],
            },
        )


def test_assess_selects_next_ui_refactor_when_unblocked(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))

    assert payload["schema"] == "agent-runtime-ui-ux-cycle-assessment/v1"
    assert payload["status"] == "ready"
    assert payload["next_refactor"]["status"] == "ready"
    assert payload["next_refactor"]["task"]["task_id"] == "TASK-AR-583"
    assert payload["next_refactor"]["task"]["target_files"] == ["src/agent_runtime/ui_console_assets.py"]
    assert payload["design_system_gate"]["status"] == "pass"
    assert payload["role_coverage"]["status"] == "pass"


def test_assess_marks_next_refactor_blocked_by_active_claim(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path, conflict=True)

    payload = module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))

    assert payload["status"] == "blocked"
    assert payload["next_refactor"]["status"] == "blocked_by_active_claim"
    assert payload["next_refactor"]["conflicts"][0]["claim_id"] == "CLAIM-conflict"
    assert payload["next_refactor"]["conflicts"][0]["overlap"] == ["src/agent_runtime/ui_console_assets.py"]


def test_assess_treats_current_cycle_claim_as_ready_after_release(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    write_json(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-cycle.json",
        {
            "claim_id": "CLAIM-cycle",
            "task_id": "TASK-AR-597",
            "task_set_id": "TASKSET-AR-UI-UX-CYCLE-AUTOMATION",
            "status": "claimed",
            "agent_role": "lead-engineer",
            "target_files": ["src/agent_runtime/ui_console_assets.py"],
        },
    )

    payload = module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))

    assert payload["status"] == "ready_after_cycle_release"
    assert payload["score"]["level"] == "ready_after_cycle_release"
    assert payload["next_refactor"]["status"] == "ready_after_cycle_release"
    assert payload["next_refactor"]["conflicts"][0]["cycle_claim"] is True


def test_quality_checklist_covers_owner_requested_dimensions(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))
    dimensions = {row["dimension"] for row in payload["quality_checklist"]}

    assert {"typography", "size_spacing", "color", "motion", "effects", "schema", "assets"} <= dimensions
    assert {"accessibility", "responsiveness", "interaction"} <= dimensions
    assert len(payload["review_plan"]["beta_tester"]["requirements"]) >= 5


def test_assess_does_not_write_files(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    assert after == before


def test_assess_infers_known_ui_target_files_from_task_body(tmp_path: Path) -> None:
    module = load_module()
    write_gate(tmp_path)
    write_org(tmp_path)
    write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-583.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-583",
                "title: Consolidate transitional px-alias tokens into a semantic scale",
                "status: planned",
                "priority: P2",
                "team: ui-ux",
                "owner: lead_engineer",
                "task_set_id: TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION",
                "summary: UI refactor",
                "---",
                "",
                "Edit ui_console_assets.py and ui_design_assets.py without changing visual behavior.",
            ]
        ),
    )

    payload = module.assess(tmp_path, now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc))

    assert payload["next_refactor"]["task"]["target_files"] == [
        "src/agent_runtime/ui_console_assets.py",
        "src/agent_runtime/ui_design_assets.py",
    ]


def test_report_dry_run_returns_path_without_writing(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.report(
        tmp_path,
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    assert payload["schema"] == "agent-runtime-ui-ux-cycle-report/v1"
    assert payload["status"] == "planned"
    assert payload["artifact"]["path"] == "reviews/REPORT-2026-06-19-ui-ux-cycle.md"
    assert not (tmp_path / payload["artifact"]["path"]).exists()
    assert {proposal["proposal_kind"] for proposal in payload["assessment"]["next_work_proposals"]} == {
        "design_direction_rfc",
        "implementation_refactor",
        "ux_evaluation_pass",
    }


def test_propose_dry_run_returns_three_proposal_kinds_without_writing(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    payload = module.propose(
        tmp_path,
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    assert after == before
    assert payload["schema"] == "agent-runtime-ui-ux-next-work-proposals/v1"
    assert payload["status"] == "planned"
    assert payload["artifact"]["path"] == "reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md"
    assert {proposal["proposal_kind"] for proposal in payload["proposals"]} == {
        "design_direction_rfc",
        "implementation_refactor",
        "ux_evaluation_pass",
    }
    assert payload["mutation_policy"]["generator_mutation_policy"] == "proposal-only"


def test_propose_refactor_proposal_has_role_routing_and_target_boundaries(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.propose(
        tmp_path,
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    refactor = next(proposal for proposal in payload["proposals"] if proposal["proposal_kind"] == "implementation_refactor")
    assert refactor["status"] == "ready_to_register"
    assert refactor["role_routing"]["lead_role"] == "interface-designer"
    assert "design-system-steward" in refactor["role_routing"]["supporting_roles"]
    assert refactor["target_file_boundaries"]["future_target_files"] == ["src/agent_runtime/ui_console_assets.py"]
    assert "agents/runtime/task_claims/*.json" in refactor["target_file_boundaries"]["generator_must_not_write"]
    assert refactor["registration_boundary"]["creates_claim"] is False
    assert refactor["registration_boundary"]["mutates_ui_files"] is False
    assert refactor["registration_boundary"]["mutates_claims"] is False
    assert refactor["registration_boundary"]["mutates_work_items"] is False


def test_propose_distinguishes_new_design_and_ux_evaluation_paths(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.propose(
        tmp_path,
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    design = next(proposal for proposal in payload["proposals"] if proposal["proposal_kind"] == "design_direction_rfc")
    evaluation = next(proposal for proposal in payload["proposals"] if proposal["proposal_kind"] == "ux_evaluation_pass")
    assert design["role_routing"]["lead_role"] == "lead-designer"
    assert "DESIGN.md" in design["target_file_boundaries"]["future_target_files"]
    assert evaluation["role_routing"]["lead_role"] == "ux-evaluator"
    assert any(path.startswith("reviews/BETA-TEST-") for path in evaluation["target_file_boundaries"]["future_target_files"])


def test_propose_write_records_only_proposal_artifact_and_index(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    payload = module.propose(
        tmp_path,
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=False,
    )

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    added = sorted(set(after) - set(before))
    assert payload["status"] == "recorded"
    assert added == ["reviews/INDEX.md", "reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md"]
    assert not any(path.startswith("src/agent_runtime/") for path in added)
    assert not any(path.startswith("agents/runtime/task_claims/") for path in added)
    text = (tmp_path / "reviews" / "PROPOSALS-2026-06-19-ui-ux-next-work.md").read_text(encoding="utf-8")
    assert "design_direction_rfc" in text
    assert "implementation_refactor" in text
    assert "ux_evaluation_pass" in text


def test_cli_assess_json(tmp_path: Path) -> None:
    write_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-19T00:00:00+00:00",
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
    assert payload["next_refactor"]["task"]["task_id"] == "TASK-AR-583"


def test_plan_review_dry_run_plans_artifacts_without_writing(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    payload = module.plan_review(
        tmp_path,
        task_id="TASK-AR-583",
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    assert after == before
    assert payload["schema"] == "agent-runtime-ui-ux-review-plan/v1"
    assert payload["status"] == "planned"
    assert payload["task"]["task_id"] == "TASK-AR-583"
    assert {artifact["kind"] for artifact in payload["artifacts"]} == {"seminar", "meeting", "beta_tester"}
    assert [artifact["status"] for artifact in payload["artifacts"]] == ["planned", "planned", "planned"]
    assert payload["index"]["status"] == "planned"


def test_plan_review_beta_tester_requires_exploratory_evidence(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.plan_review(
        tmp_path,
        task_id="TASK-AR-583",
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=True,
    )

    beta = next(artifact for artifact in payload["artifacts"] if artifact["kind"] == "beta_tester")
    fields = {row["field"] for row in beta["evidence_fields"]}
    assert {"user_like_actions", "recovery_attempts", "environment_notes", "failure_ids"} <= fields
    assert any("clicked or typed" in requirement for requirement in beta["requirements"])
    assert any("BTC-style" in requirement for requirement in beta["requirements"])


def test_plan_review_write_records_artifacts_and_updates_index(tmp_path: Path) -> None:
    module = load_module()
    write_fixture(tmp_path)

    payload = module.plan_review(
        tmp_path,
        task_id="TASK-AR-583",
        now=datetime(2026, 6, 19, 0, 0, tzinfo=timezone.utc),
        dry_run=False,
    )

    assert payload["status"] == "recorded"
    assert payload["index"]["status"] == "pass"
    for artifact in payload["artifacts"]:
        assert artifact["status"] == "recorded"
        assert (tmp_path / artifact["path"]).exists()
    beta_text = (tmp_path / "reviews" / "BETA-TEST-2026-06-19-task-ar-583-ui-ux.md").read_text(encoding="utf-8")
    assert "## User-Like Actions" in beta_text
    assert "## Recovery Attempts" in beta_text
    assert "## Failure IDs" in beta_text
    index_text = (tmp_path / "reviews" / "INDEX.md").read_text(encoding="utf-8")
    assert "BETA-TEST-2026-06-19-task-ar-583-ui-ux.md" in index_text


def test_cli_plan_review_json(tmp_path: Path) -> None:
    write_fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--now",
            "2026-06-19T00:00:00+00:00",
            "plan-review",
            "--task-id",
            "TASK-AR-583",
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
    assert payload["status"] == "planned"
    assert payload["artifacts"][0]["path"] == "reviews/SEMINAR-2026-06-19-task-ar-583-ui-ux.md"
