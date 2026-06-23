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


def test_blueprints_dir_has_readme():
    assert BLUEPRINTS_README.exists()
    text = BLUEPRINTS_README.read_text(encoding="utf-8").lower()
    assert "draft" in text and "owner" in text
