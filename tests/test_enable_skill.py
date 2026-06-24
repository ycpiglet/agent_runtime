"""Structural guards for the /enable skill (per-blueprint enablement pack).

The synthesis is conversational and not unit-tested; these tests assert the skill
file stays complete (blueprint input, live asset surfaces, ENABLEMENT sections) and
safe (boundary + OWNER-DECIDES + no auto-execution).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "enable" / "SKILL.md"

ASSET_SURFACES = [
    "skills/",
    "scripts/",
    "RUNTIME-ASSET-REGISTRY.json",
    "WORK-LANE-PLAYBOOKS.md",
    "BUSINESS-OPERATING-SYSTEM.md",
]
SECTIONS = [
    "Getting started",
    "Methodology → Asset map",
    "Tailored asset index",
    "Open choices",
]


def test_skill_exists_with_frontmatter_name():
    assert SKILL.exists()
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: enable" in text


def test_skill_declares_blueprint_input():
    text = SKILL.read_text(encoding="utf-8")
    assert "blueprints/" in text
    assert "VISION-DIRECTION.md" in text


def test_skill_reads_live_asset_surfaces():
    text = SKILL.read_text(encoding="utf-8")
    for surface in ASSET_SURFACES:
        assert surface in text, f"missing asset surface: {surface}"


def test_enablement_template_has_sections():
    text = SKILL.read_text(encoding="utf-8")
    assert "ENABLEMENT.md" in text
    for section in SECTIONS:
        assert section in text, f"missing section: {section}"


def test_safety_and_no_execute():
    text = SKILL.read_text(encoding="utf-8")
    assert "OWNER-DECIDES" in text
    assert "boundary" in text.lower()
    assert "not execute" in text.lower()
