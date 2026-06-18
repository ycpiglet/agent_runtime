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
