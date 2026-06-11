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


def _write_unit(root: Path, task_id: str, *, missing_section: str = "") -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"UNIT-{task_id}-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
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
  - input.md
target_files:
  - scripts/example.py
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
