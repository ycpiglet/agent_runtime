"""TASK-AR-331: automation_rules_gate execution + off-by-default safety.

The gate is the single EXECUTION point for declarative UI automation rules. It
must be wired into the owner-governance chain (root + template, chain-parity)
and stay no-op-safe so the stop-hook owner-governance approve path never breaks.
"""

import json
import subprocess
import sys
from pathlib import Path

from scripts import automation_rules_gate


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "automation_rules_gate.py"
TEMPLATE_SCRIPT = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "automation_rules_gate.py"


def _load_module():
    return automation_rules_gate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _rule(rules_dir: Path, rule_id: str, **fields) -> None:
    _write(rules_dir / f"{rule_id}.json", json.dumps({"id": rule_id, **fields}))


def _task(root: Path, task_id: str, *, status: str = "planned", **extra) -> None:
    lines = ["---", f"id: {task_id}", f"status: {status}", "owner: lead-engineer"]
    for key, value in extra.items():
        lines.append(f"{key}: {value}")
    lines += ["---", "", "## Goal", "", "Sample.", ""]
    _write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-sample.md", "\n".join(lines))


def test_gate_passes_with_no_rules_directory(tmp_path):
    module = _load_module()
    outcome = module.execute(tmp_path)
    assert outcome.rules_total == 0
    assert outcome.rules_executed == 0
    assert not any(finding.severity == "block" for finding in outcome.findings)


def test_gate_cli_check_is_zero_when_no_rules(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "rules_total=0" in result.stdout


def test_gate_executes_only_active_valid_rules(tmp_path):
    module = _load_module()
    rules_dir = tmp_path / "agents" / "project" / "automation" / "rules"
    _rule(rules_dir, "ACTIVE", trigger="blocked_too_long", action="escalation_message", active=True)
    _rule(rules_dir, "INACTIVE", trigger="status_change", action="board_regen", active=False)
    _rule(rules_dir, "INVALID", trigger="???", action="board_regen", active=True)
    _task(tmp_path, "TASK-1", status="blocked", blocked_since="2026-01-01")

    outcome = module.execute(tmp_path, apply_actions=False)
    assert outcome.rules_total == 3
    assert outcome.rules_active == 1
    assert outcome.rules_executed == 1
    assert outcome.rules_invalid == 1
    assert outcome.actions[0]["rule_id"] == "ACTIVE"
    assert "TASK-1" in outcome.actions[0]["matched_task_ids"]


def test_gate_apply_appends_event_without_block(tmp_path):
    module = _load_module()
    rules_dir = tmp_path / "agents" / "project" / "automation" / "rules"
    _rule(rules_dir, "DUE", trigger="due_passed", action="escalation_message", active=True)
    _task(tmp_path, "TASK-2", due="2026-01-01")

    outcome = module.execute(tmp_path, apply_actions=True)
    assert outcome.rules_executed == 1
    log = tmp_path / "agents" / "runtime" / "events" / "automation_rules.jsonl"
    assert log.exists()
    record = json.loads(log.read_text(encoding="utf-8").strip())
    assert record["event"] == "automation_rule_executed"
    assert record["rule_id"] == "DUE"


def test_gate_is_wired_into_owner_governance_chain_root_and_template():
    root_chain = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_chain = (REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert '"scripts/automation_rules_gate.py", "--check"' in root_chain
    assert '"scripts/automation_rules_gate.py", "--check"' in template_chain


def test_gate_script_mirrored_into_template_directory():
    assert TEMPLATE_SCRIPT.exists()
    assert SCRIPT.read_text(encoding="utf-8") == TEMPLATE_SCRIPT.read_text(encoding="utf-8")
