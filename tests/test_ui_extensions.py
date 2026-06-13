"""TASK-AR-331: custom properties, labels, automation rules, triage queue.

Covers the read-only state derivations (ui_state), the proposal-only CRUD
command path (ui_commands), the served UI surface (ui_console), and the
gate-chain rule executor (scripts/automation_rules_gate.py), including the
off-by-default no-op safety that keeps the owner-governance approve path green.
"""

import json
import subprocess
import sys
from pathlib import Path

from agent_runtime import ui_commands
from agent_runtime import ui_console
from agent_runtime import ui_state


NOW = "2026-06-13T12:00:00+09:00"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task(
    root: Path,
    task_id: str,
    *,
    status: str = "planned",
    task_set_id: str | None = "TASKSET-AR-SAMPLE",
    tags: list[str] | None = None,
    extra: dict[str, str] | None = None,
) -> None:
    lines = ["---", f"id: {task_id}", f"status: {status}", "owner: lead-engineer", "priority: P1"]
    if task_set_id:
        lines.append(f"task_set_id: {task_set_id}")
    for key, value in (extra or {}).items():
        lines.append(f"{key}: {value}")
    lines.append("tags:")
    for tag in tags or ["ui-console"]:
        lines.append(f"  - {tag}")
    lines += ["---", "", "## Goal", "", "Sample task.", ""]
    _write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-sample.md", "\n".join(lines))


# ----- Custom properties: parse / display / filter -----


def test_custom_property_parse_display_and_filter(tmp_path):
    _write(
        tmp_path / ui_state.CUSTOM_PROPERTIES_REL,
        json.dumps(
            {
                "properties": [
                    {"key": "severity", "label": "Severity", "type": "select", "options": ["low", "high"]},
                    {"key": "estimate", "type": "number"},
                    {"key": "bad_type", "type": "nonsense"},
                ]
            }
        ),
    )
    _task(tmp_path, "TASK-UI-001", extra={"severity": "high", "estimate": "5"})
    _task(tmp_path, "TASK-UI-002", extra={"severity": "low"})

    state = ui_state.build_state(tmp_path, now=NOW)
    props = state["custom_properties"]
    by_key = {definition["key"]: definition for definition in props["definitions"]}
    assert by_key["severity"]["type"] == "select"
    assert by_key["severity"]["options"] == ["low", "high"]
    assert by_key["bad_type"]["type"] == "text"  # invalid type coerced to text

    tasks = state["tasks"]
    first = next(task for task in tasks if task["id"] == "TASK-UI-001")
    assert first["custom_properties"]["severity"]["display"] == "high"
    assert first["custom_properties"]["estimate"]["display"] == "5"

    high = ui_state.filter_tasks_by_custom_properties(tasks, {"severity": "high"})
    assert [task["id"] for task in high] == ["TASK-UI-001"]


# ----- Labels: CRUD definition load + computed usage counts + tokenized colors -----


def test_label_usage_count_and_token_only_colors(tmp_path):
    _write(
        tmp_path / ui_state.LABELS_REL,
        json.dumps({"labels": [{"name": "urgent", "color": "red; background:url(evil)"}]}),
    )
    _task(tmp_path, "TASK-UI-010", tags=["urgent", "frontend"])
    _task(tmp_path, "TASK-UI-011", tags=["urgent"])

    labels = ui_state.build_labels(tmp_path, ui_state.load_tasks(tmp_path, NOW, []), NOW, [])
    by_name = {label["name"].lower(): label for label in labels["labels"]}
    assert by_name["urgent"]["usage_count"] == 2
    assert by_name["urgent"]["defined"] is True
    # The malicious color string was mapped onto a fixed semantic token, never raw CSS.
    assert by_name["urgent"]["color_token"] in ui_state.LABEL_COLOR_TOKENS
    # A tag used on tasks but not defined still surfaces with a token color.
    assert by_name["frontend"]["defined"] is False
    assert by_name["frontend"]["usage_count"] == 1
    assert by_name["frontend"]["color_token"] in ui_state.LABEL_COLOR_TOKENS


# ----- Automation rules: declarative load + active/inactive + validity -----


def test_automation_rules_load_active_inactive_and_invalid(tmp_path):
    rules_dir = tmp_path / "agents" / "project" / "automation" / "rules"
    _write(rules_dir / "RULE-A.json", json.dumps({"id": "RULE-A", "trigger": "blocked_too_long", "action": "escalation_message", "active": True}))
    _write(rules_dir / "RULE-B.json", json.dumps({"id": "RULE-B", "trigger": "status_change", "action": "board_regen", "active": False}))
    _write(rules_dir / "RULE-C.json", json.dumps({"id": "RULE-C", "trigger": "bogus", "action": "board_regen", "active": True}))

    data = ui_state.load_automation_rules(tmp_path, NOW, [])
    by_id = {rule["id"]: rule for rule in data["rules"]}
    assert by_id["RULE-A"]["active"] is True and not by_id["RULE-A"]["invalid"]
    assert by_id["RULE-B"]["active"] is False
    assert by_id["RULE-C"]["invalid"]  # unknown trigger flagged
    assert data["totals"] == {"rules": 3, "active": 1, "inactive": 1, "invalid": 1}


# ----- Triage queue collection logic -----


def test_triage_collects_unclassified_overdue_and_long_blocked(tmp_path):
    _task(tmp_path, "TASK-UI-020", task_set_id=None)  # unclassified
    _task(tmp_path, "TASK-UI-021", extra={"due": "2026-06-01"})  # overdue
    _task(tmp_path, "TASK-UI-022", status="blocked", extra={"blocked_since": "2026-06-01"})  # long blocked
    _task(tmp_path, "TASK-UI-023", status="completed", task_set_id=None)  # done -> excluded
    _task(tmp_path, "TASK-UI-024")  # healthy -> excluded

    tasks = ui_state.load_tasks(tmp_path, NOW, [])
    triage = ui_state.build_triage(tasks, NOW)
    by_id = {item["id"]: item for item in triage["items"]}
    assert "unclassified" in by_id["TASK-UI-020"]["reasons"]
    assert "overdue" in by_id["TASK-UI-021"]["reasons"]
    assert "long_blocked" in by_id["TASK-UI-022"]["reasons"]
    assert "TASK-UI-023" not in by_id  # completed excluded
    assert "TASK-UI-024" not in by_id  # healthy excluded
    assert triage["totals"]["total"] == 3
    assert triage["totals"]["unclassified"] >= 1


def test_triage_empty_when_repo_is_clean(tmp_path):
    _task(tmp_path, "TASK-UI-030")
    triage = ui_state.build_triage(ui_state.load_tasks(tmp_path, NOW, []), NOW)
    assert triage["items"] == []
    assert triage["totals"]["total"] == 0


# ----- Command path: proposal-only (no canonical SSoT write) -----


def test_label_command_is_proposal_only_and_tokenized(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "label.create", "payload": {"name": "urgent", "color": "javascript:alert(1)"}},
        now=NOW,
        command_id="COMMAND-1",
    )
    assert result["status"] == "queued"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    assert result["result"]["color_token"] in ui_commands.LABEL_COLOR_TOKENS
    # Proposal written to .ui_outbox, NOT to the canonical labels.json.
    proposals = list((tmp_path / ".ui_outbox" / "labels").glob("LABELREQ-*.json"))
    assert len(proposals) == 1
    assert not (tmp_path / ui_state.LABELS_REL).exists()


def test_property_command_validates_and_is_proposal_only(tmp_path):
    ok = ui_commands.submit_command(
        tmp_path,
        {"type": "property.create", "payload": {"key": "severity", "type": "select", "options": ["a", "b"]}},
        now=NOW,
        command_id="COMMAND-2",
    )
    assert ok["status"] == "queued"
    assert ok["result"]["changed"][0].startswith(".ui_outbox/properties/")

    bad = ui_commands.submit_command(
        tmp_path,
        {"type": "property.create", "payload": {"key": "severity", "type": "select"}},
        now=NOW,
        command_id="COMMAND-3",
    )
    assert bad["status"] == "failed"
    assert any("select property requires" in error for error in bad["errors"])
    assert not (tmp_path / ui_state.CUSTOM_PROPERTIES_REL).exists()


def test_automation_command_crud_and_toggle_proposal_only(tmp_path):
    created = ui_commands.submit_command(
        tmp_path,
        {"type": "automation.create", "payload": {"name": "Escalate blocks", "trigger": "blocked_too_long", "action": "escalation_message", "active": True}},
        now=NOW,
        command_id="COMMAND-4",
    )
    assert created["status"] == "queued"
    assert created["result"]["execution_boundary"] == "gate_chain"
    rule_id = created["result"]["rule_id"]

    toggled = ui_commands.submit_command(
        tmp_path,
        {"type": "automation.toggle", "target": rule_id, "payload": {"active": False}},
        now=NOW,
        command_id="COMMAND-5",
    )
    assert toggled["status"] == "queued"

    # Two proposals written, NO canonical rule file created by the console.
    proposals = list((tmp_path / ".ui_outbox" / "automation").glob("AUTOREQ-*.json"))
    assert len(proposals) == 2
    toggle_proposal = json.loads(
        next(path for path in proposals if json.loads(path.read_text(encoding="utf-8"))["action"] == "toggle").read_text(encoding="utf-8")
    )
    assert toggle_proposal["active"] is False
    canonical = tmp_path / "agents" / "project" / "automation" / "rules"
    assert not (canonical.exists() and list(canonical.glob("*.json")))

    invalid = ui_commands.submit_command(
        tmp_path,
        {"type": "automation.create", "payload": {"trigger": "nope", "action": "board_regen"}},
        now=NOW,
        command_id="COMMAND-6",
    )
    assert invalid["status"] == "failed"
    assert any("invalid trigger" in error for error in invalid["errors"])


def test_ui_config_command_types_in_allowlist():
    for command_type in (
        "property.create",
        "label.create",
        "automation.create",
        "automation.toggle",
        "automation.delete",
    ):
        assert command_type in ui_commands.COMMAND_TYPES


# ----- Served UI surface -----


def test_ui_console_serves_new_views_and_tokenized_label_css(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    for marker in ('data-view="triage"', 'data-view="automation"', 'data-view="properties"', 'data-view="labels"'):
        assert marker in html
    for view_id in ("view-triage", "view-automation", "view-properties", "view-labels"):
        assert f'id="{view_id}"' in html

    # Label color chips consume a token via data-color; CSS resolves to var(--token).
    assert '.label-chip[data-color="danger"]::before { background: var(--danger); }' in css
    assert "data-color=" in js
    for marker in ("renderTriage", "renderAutomation", "renderLabels", "automation.toggle", "label.create"):
        assert marker in js


def test_state_resource_exposes_new_resources(tmp_path):
    _task(tmp_path, "TASK-UI-040", task_set_id=None)
    for resource in ("custom_properties", "labels", "automation_rules", "triage"):
        assert resource in ui_state.RESOURCE_NAMES
        payload = ui_state.build_resource(tmp_path, resource, now=NOW)
        assert payload["resource"] == resource
        assert "items" in payload


# ----- Gate-chain rule execution: off-by-default safe + executes active rules -----


def test_automation_gate_is_noop_safe_when_no_rules(tmp_path):
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "automation_rules_gate.py"), "--root", str(tmp_path), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "automation-rules-gate: pass" in result.stdout
    assert "rules_total=0" in result.stdout


def test_automation_gate_executes_active_rule_and_skips_inactive(tmp_path):
    _task(tmp_path, "TASK-UI-050", status="blocked", extra={"blocked_since": "2026-01-01"})
    rules_dir = tmp_path / "agents" / "project" / "automation" / "rules"
    _write(rules_dir / "RULE-ACTIVE.json", json.dumps({"id": "RULE-ACTIVE", "trigger": "blocked_too_long", "action": "escalation_message", "active": True}))
    _write(rules_dir / "RULE-OFF.json", json.dumps({"id": "RULE-OFF", "trigger": "status_change", "action": "board_regen", "active": False}))

    from scripts import automation_rules_gate  # noqa: WPS433 - executable module import for unit coverage

    outcome = automation_rules_gate.execute(tmp_path, apply_actions=True)
    assert outcome.rules_total == 2
    assert outcome.rules_active == 1
    assert outcome.rules_executed == 1
    executed = {action["rule_id"] for action in outcome.actions}
    assert executed == {"RULE-ACTIVE"}
    matched = outcome.actions[0]["matched_task_ids"]
    assert "TASK-UI-050" in matched
    # Active execution appended an event log entry (proposal-via-event, no SSoT write).
    log = tmp_path / "agents" / "runtime" / "events" / "automation_rules.jsonl"
    assert log.exists()


def test_automation_gate_check_passes_even_with_rules(tmp_path):
    rules_dir = tmp_path / "agents" / "project" / "automation" / "rules"
    _write(rules_dir / "RULE-X.json", json.dumps({"id": "RULE-X", "trigger": "due_passed", "action": "label_apply", "active": True}))
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "automation_rules_gate.py"), "--root", str(tmp_path), "--check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "automation-rules-gate: pass" in result.stdout
