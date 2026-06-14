import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import host_feedback_intake as hfi  # noqa: E402


def test_real_queue_is_valid() -> None:
    queue = hfi.load_queue()
    assert hfi.check_queue(queue) == []
    assert queue["schema"] == hfi.SCHEMA
    # The seven seed host-feedback items (4 GH feedback issues + 3 open bugs).
    ids = [entry["id"] for entry in queue["entries"]]
    assert len(ids) == len(set(ids)) >= 7


def test_check_flags_invalid_category_status_and_dupes() -> None:
    bad = {
        "schema": hfi.SCHEMA,
        "categories": ["process"],
        "statuses": ["triage"],
        "entries": [
            {"id": "X1", "source": "s", "title": "t", "category": "process", "status": "triage"},
            {"id": "X1", "source": "s", "title": "t", "category": "nope", "status": "gone"},
            {"id": "", "source": "", "title": "", "category": "process", "status": "triage"},
        ],
    }
    findings = hfi.check_queue(bad)
    assert any("duplicate-id" in f for f in findings)
    assert any("invalid-category" in f for f in findings)
    assert any("invalid-status" in f for f in findings)
    assert any("missing-id" in f for f in findings)


def test_render_is_idempotent_and_lists_every_entry() -> None:
    queue = hfi.load_queue()
    first = hfi.render_md(queue)
    second = hfi.render_md(queue)
    assert first == second  # idempotent (no Date.now drift beyond date-only)
    for entry in queue["entries"]:
        assert entry["id"] in first
    # Triage guardrail wording is present.
    assert "first-class" in first
    assert "## Decision" in first
