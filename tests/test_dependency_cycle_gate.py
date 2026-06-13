"""Tests for the dependency cycle gate (TASK-AR-330).

The gate scans task frontmatter for circular ``blocks``/``blocked_by`` chains.
It must:
- exit 1 (warn/block) when a cycle exists,
- exit 0 with ``findings=0`` when the graph is acyclic,
- exit 0 (no-op safe) when no task declares blocks/blocked_by at all, and
- ship byte-identical in the root and template scripts directories so the
  owner-governance chain-parity guard stays satisfied.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_GATE = REPO_ROOT / "scripts" / "dependency_cycle_gate.py"
TEMPLATE_GATE = (
    REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "dependency_cycle_gate.py"
)


def _load_gate():
    spec = importlib.util.spec_from_file_location("dependency_cycle_gate_under_test", ROOT_GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _write_task(root: Path, task_id: str, *, blocks=None, blocked_by=None, parent_id=None) -> None:
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"id: {task_id}", "status: planned", "owner: lead-engineer"]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if blocks:
        lines.append("blocks:")
        lines.extend(f"  - {dep}" for dep in blocks)
    if blocked_by:
        lines.append("blocked_by:")
        lines.extend(f"  - {dep}" for dep in blocked_by)
    lines += ["---", "", "## Goal", "", f"Work {task_id}.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT_GATE), "--check", "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_gate_is_noop_safe_when_no_dependencies(tmp_path):
    _write_task(tmp_path, "TASK-AR-900")
    _write_task(tmp_path, "TASK-AR-901", parent_id="TASKSET-AR-DEP")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dependency_edges=0" in result.stdout
    assert "findings=0" in result.stdout


def test_gate_passes_on_acyclic_dependencies(tmp_path):
    _write_task(tmp_path, "TASK-AR-900", blocks=["TASK-AR-901"])
    _write_task(tmp_path, "TASK-AR-901", blocked_by=["TASK-AR-900"])
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    # blocks + blocked_by fold to a single deduped edge.
    assert "dependency_edges=1" in result.stdout
    assert "findings=0" in result.stdout


def test_gate_blocks_on_cycle(tmp_path):
    _write_task(tmp_path, "TASK-AR-900", blocks=["TASK-AR-901"])
    _write_task(tmp_path, "TASK-AR-901", blocks=["TASK-AR-902"])
    _write_task(tmp_path, "TASK-AR-902", blocks=["TASK-AR-900"])
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "findings=1" in result.stdout
    assert "cycle:" in result.stdout


def test_gate_blocks_on_self_managed_two_node_cycle(tmp_path):
    # blocks on one side, blocked_by on the other -> still a 2-node cycle.
    _write_task(tmp_path, "TASK-AR-900", blocks=["TASK-AR-901"])
    _write_task(tmp_path, "TASK-AR-901", blocks=["TASK-AR-900"])
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "findings=1" in result.stdout


def test_gate_handles_missing_tasks_dir(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "findings=0" in result.stdout


def test_detect_cycles_pure_function():
    gate = _load_gate()
    assert gate.detect_cycles([]) == []
    assert gate.detect_cycles([("A", "B"), ("B", "C")]) == []
    cycles = gate.detect_cycles([("A", "B"), ("B", "C"), ("C", "A")])
    assert len(cycles) == 1
    assert set(cycles[0]) == {"A", "B", "C"}


def test_template_gate_is_byte_identical_to_root():
    assert TEMPLATE_GATE.exists(), "template must ship dependency_cycle_gate.py"
    assert (
        ROOT_GATE.read_bytes() == TEMPLATE_GATE.read_bytes()
    ), "template dependency_cycle_gate.py drifted from root copy"


def test_gate_json_format(tmp_path):
    _write_task(tmp_path, "TASK-AR-900", blocks=["TASK-AR-901"])
    _write_task(tmp_path, "TASK-AR-901", blocks=["TASK-AR-900"])
    result = subprocess.run(
        [sys.executable, str(ROOT_GATE), "--check", "--root", str(tmp_path), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    import json

    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["findings"] == 1
    assert payload["cycles"]
