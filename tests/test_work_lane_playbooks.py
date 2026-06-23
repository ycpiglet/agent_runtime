"""Structural guard for the per-lane operating playbooks.

WORK-LANE-PLAYBOOKS.md is the per-lane companion to BUSINESS-OPERATING-SYSTEM.md.
These tests assert it stays complete (all five lanes), safe (draft-only boundary
and OWNER-DECIDES markers preserved), and in parity with the project template —
without asserting any specific business content (that is the Owner's domain).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "agents" / "project" / "WORK-LANE-PLAYBOOKS.md"
TEMPLATE = ROOT / "src" / "agent_runtime" / "templates" / "project" / "agents" / "project" / "WORK-LANE-PLAYBOOKS.md"

LANES = [
    "finance-accounting",
    "marketing-growth",
    "sales-revenue",
    "operations-support",
    "planning-strategy",
]


def test_playbook_exists_live_and_template():
    assert LIVE.exists(), "live WORK-LANE-PLAYBOOKS.md missing"
    assert TEMPLATE.exists(), "template WORK-LANE-PLAYBOOKS.md missing"


def test_all_five_lanes_have_a_playbook_section():
    text = LIVE.read_text(encoding="utf-8")
    for lane in LANES:
        assert f"## Lane: {lane}" in text, f"missing playbook section for {lane}"


def test_safe_effect_boundary_is_present():
    text = LIVE.read_text(encoding="utf-8")
    # process/safety scaffolding must survive edits
    assert "OWNER-DECIDES" in text
    assert "Escalate to Owner" in text
    assert "draft" in text.lower()
    # each lane must spell out what NOT to perform
    assert text.count("Escalate to Owner (do not perform):") >= len(LANES)


def test_links_back_to_business_operating_system():
    text = LIVE.read_text(encoding="utf-8")
    assert "BUSINESS-OPERATING-SYSTEM.md" in text


def test_live_and_template_playbooks_are_in_parity():
    assert LIVE.read_text(encoding="utf-8") == TEMPLATE.read_text(encoding="utf-8")
