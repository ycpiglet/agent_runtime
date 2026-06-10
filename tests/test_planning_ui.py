from __future__ import annotations

import json
from pathlib import Path

from agent_runtime import ui_commands, ui_state


def test_planning_scan_ui_command_is_proposal_only(tmp_path: Path) -> None:
    record = ui_commands.submit_command(
        tmp_path,
        {"type": "planning.scan", "payload": {"actor": "operator", "reason": "cycle complete"}},
        now="2026-06-10T00:00:00+00:00",
        command_id="COMMAND-20260610000000-abcdef",
    )
    assert record["status"] == "queued"
    changed = record["result"]["changed"][0]
    request = json.loads((tmp_path / changed).read_text(encoding="utf-8"))
    assert request["mode"] == "B"
    assert request["canonical_mutation_allowed"] is False


def test_planning_scan_ui_command_blocks_mutation_attempt(tmp_path: Path) -> None:
    record = ui_commands.submit_command(
        tmp_path,
        {"type": "planning.scan", "payload": {"apply": True}},
        now="2026-06-10T00:00:00+00:00",
        command_id="COMMAND-20260610000000-fedcba",
    )
    assert record["status"] == "failed"
    assert "cannot apply canonical mutations" in "; ".join(record["errors"])


def test_planning_resource_lists_outbox_records(tmp_path: Path) -> None:
    outbox = tmp_path / "agents/planning/outbox"
    outbox.mkdir(parents=True)
    (outbox / "PROP-ABCDEF123456.json").write_text(
        json.dumps({"id": "PROP-ABCDEF123456", "status": "proposed", "risk_tier": "low"}),
        encoding="utf-8",
    )
    resource = ui_state.build_resource(tmp_path, "planning", now="2026-06-10T00:00:00+00:00")
    assert resource["items"]["summary"]["proposal_count"] == 1
    assert resource["items"]["proposals"][0]["source_path"] == "agents/planning/outbox/PROP-ABCDEF123456.json"
