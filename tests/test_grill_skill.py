"""Structural guards for the /grill skill (discovery -> blueprint -> vision).

The interview itself is conversational and not unit-tested; these tests assert the
skill file stays complete (six-part frame, three phases), safe (boundary +
OWNER-DECIDES), wired to the lane playbooks, and that its output convention exists.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "grill" / "SKILL.md"
BLUEPRINTS_README = ROOT / "agents" / "project" / "blueprints" / "README.md"

FRAME = [
    "Asset",
    "Problem & who",
    "Value & differentiation",
    "Constraints",
    "Goals",
    "Monetization hypothesis",
]
PHASES = ["Phase A", "Phase B", "Phase C"]


def test_blueprints_dir_has_readme():
    assert BLUEPRINTS_README.exists()
    text = BLUEPRINTS_README.read_text(encoding="utf-8").lower()
    assert "draft" in text and "owner" in text


def test_skill_exists_with_frontmatter_name():
    assert SKILL.exists()
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: grill" in text


def test_skill_covers_six_part_frame():
    text = SKILL.read_text(encoding="utf-8")
    for item in FRAME:
        assert item in text, f"missing frame item: {item}"


def test_skill_has_three_phases():
    text = SKILL.read_text(encoding="utf-8")
    for phase in PHASES:
        assert phase in text, f"missing {phase}"


def test_skill_states_safety_and_owner_decides():
    text = SKILL.read_text(encoding="utf-8")
    assert "OWNER-DECIDES" in text
    assert "boundary" in text.lower()
    assert "draft" in text.lower()


def test_skill_links_playbooks_and_packet():
    text = SKILL.read_text(encoding="utf-8")
    assert "WORK-LANE-PLAYBOOKS.md" in text
    assert "BUSINESS-OPERATING-SYSTEM.md" in text


def test_skill_includes_artifact_templates():
    text = SKILL.read_text(encoding="utf-8")
    assert "BLUEPRINT.md" in text and "VISION-DIRECTION.md" in text
    assert "Revenue hypothesis" in text  # blueprint field
    assert "Methodology" in text  # vision-direction section
