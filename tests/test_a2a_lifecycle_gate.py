import json
from pathlib import Path

from scripts import a2a_lifecycle_gate


ROOT = Path(__file__).resolve().parents[1]


def test_default_a2a_lifecycle_record_passes():
    payload = a2a_lifecycle_gate.run()

    assert payload["status"] == "pass"
    assert payload["findings"] == []


def test_missing_lifecycle_step_blocks(tmp_path):
    source = ROOT / "agents" / "project" / "evidence" / "a2a" / "A2A-LIFECYCLE-2026-06-12.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["events"] = [event for event in payload["events"] if event["event_type"] != "decision"]
    record = tmp_path / "missing-decision.json"
    record.write_text(json.dumps(payload), encoding="utf-8")

    result = a2a_lifecycle_gate.run(record, root=ROOT)

    assert result["status"] == "block"
    assert any("missing-event:decision" in finding for finding in result["findings"])

