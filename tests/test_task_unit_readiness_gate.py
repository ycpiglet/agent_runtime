from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_unit_readiness_gate.py"


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write_task(root: Path, task_id: str, *, status: str = "planned") -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
id: {task_id}
status: {status}
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
worker_model_tier: worker_standard
tags: []
---

## Goal
- Test task.
""",
        encoding="utf-8",
    )


def _write_unit(
    root: Path,
    task_id: str,
    *,
    missing_section: str = "",
    target_file: str = "scripts/example.py",
    input_file: str = "input.md",
    create_paths: bool = True,
) -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"UNIT-{task_id}-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if create_paths:
        for rel in (target_file, input_file):
            if rel.startswith("new:") or "*" in rel or "://" in rel:
                continue
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("fixture\n", encoding="utf-8")
    sections = {
        "Context": "This unit exists for a gate test.",
        "Inputs": "- input.md",
        "Target Files": "- scripts/example.py",
        "Scope": "Only this test unit.",
        "Steps": "1. Edit.\n2. Verify.",
        "Acceptance Criteria": "- It passes.",
        "Verification": "- python scripts/task_unit_readiness_gate.py --check",
        "Handoff": "Report the result.",
        "Stop Boundary": "Stop after this unit.",
    }
    body = "\n\n".join(
        f"## {name}\n\n{text}" for name, text in sections.items() if name != missing_section
    )
    path.write_text(
        f"""---
unit_id: UNIT-{task_id}-001
task_id: {task_id}
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: worker_ready
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity]
context: "Gate test context."
inputs:
  - {input_file}
target_files:
  - {target_file}
scope: "Only this test unit."
acceptance:
  - "It passes."
verification:
  - "python scripts/task_unit_readiness_gate.py --check"
handoff: "Report the result."
stop_condition: "Stop after this unit."
---

# UNIT-{task_id}-001

{body}
""",
        encoding="utf-8",
    )


def test_ready_unit_passes_required_gate(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--require-ready", "--check")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "task-unit-readiness-gate: pass" in result.stdout


def test_gate_names_missing_required_section(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344", missing_section="Verification")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--require-ready", "--check")

    assert result.returncode == 1
    assert "unit:missing-section:verification" in result.stdout


def test_gate_blocks_active_worker_claim_without_unit(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344", status="in_progress")
    claims_dir = tmp_path / "agents" / "runtime" / "task_claims"
    claims_dir.mkdir(parents=True)
    (claims_dir / "CLAIM-344.json").write_text(
        """{
  "claim_id": "CLAIM-344",
  "task_id": "TASK-AR-344",
  "task_set_id": "TASKSET-AR-PM-OPERATING-SYSTEM",
  "status": "working",
  "model_tier": "worker_standard"
}
""",
        encoding="utf-8",
    )

    result = _run(tmp_path, "--check")

    assert result.returncode == 1
    assert "unit:active-worker-missing-unit-spec" in result.stdout


def test_gate_blocks_nonexistent_declared_target_file(tmp_path: Path) -> None:
    # GH #125: target_files feeds collision detection, so a typo'd/nonexistent
    # declared path must fail readiness instead of silently passing.
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344", target_file="tests/unit/test_compliance_gate.py", create_paths=False)
    (tmp_path / "input.md").write_text("fixture\n", encoding="utf-8")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--check")

    assert result.returncode == 1
    assert "unit:target-files-not-found:tests/unit/test_compliance_gate.py" in result.stdout


def test_gate_blocks_nonexistent_declared_input(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344", input_file="docs/missing-brief.md", create_paths=False)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "example.py").write_text("fixture\n", encoding="utf-8")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--check")

    assert result.returncode == 1
    assert "unit:inputs-not-found:docs/missing-brief.md" in result.stdout


def test_gate_allows_to_be_created_target_with_new_prefix(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344", target_file="new:reviews/REPORT-TO-CREATE.md")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--check")

    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_exempts_completed_parent_task_from_path_existence(tmp_path: Path) -> None:
    # Historical units of finished tasks may reference since-deleted paths
    # (e.g. a task whose scope WAS deleting a waiver file).
    _write_task(tmp_path, "TASK-AR-344", status="completed")
    _write_unit(tmp_path, "TASK-AR-344", target_file="agents/project/waivers/DELETED.json", create_paths=False)
    (tmp_path / "input.md").write_text("fixture\n", encoding="utf-8")

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--check")

    assert result.returncode == 0, result.stdout + result.stderr


def test_gate_skips_glob_and_domain_like_entries(tmp_path: Path) -> None:
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344", target_file="src/**/*.py", input_file="github.com/fnando/sparkline", create_paths=False)

    result = _run(tmp_path, "--task-id", "TASK-AR-344", "--check")

    assert result.returncode == 0, result.stdout + result.stderr


def _inject(root: Path, task_id: str, marker: str) -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"UNIT-{task_id}-001.md"
    text = path.read_text(encoding="utf-8").replace("- It passes.", f"- It passes {marker}.")
    path.write_text(text, encoding="utf-8")


def test_ar629_needs_clarification_marker_blocks(tmp_path: Path) -> None:
    # TASK-AR-629: an unresolved [NEEDS CLARIFICATION: ...] placeholder is not worker-ready.
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344")
    _inject(tmp_path, "TASK-AR-344", "[NEEDS CLARIFICATION: which output format?]")
    result = _run(tmp_path, "--check")
    assert result.returncode == 1
    assert "unit:unresolved-clarification" in result.stdout


def test_ar629_prose_mention_without_colon_not_blocked(tmp_path: Path) -> None:
    # Describing the convention ("[NEEDS CLARIFICATION] marker", no colon) must not trip the gate.
    _write_task(tmp_path, "TASK-AR-344")
    _write_unit(tmp_path, "TASK-AR-344")
    _inject(tmp_path, "TASK-AR-344", "documented via the [NEEDS CLARIFICATION] marker")
    result = _run(tmp_path, "--check")
    assert "unit:unresolved-clarification" not in result.stdout
