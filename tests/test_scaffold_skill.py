"""Structural guards for the /scaffold skill (starter enablement asset files).

The scaffolding is conversational and not unit-tested; these tests assert the skill
stays complete (blueprint input, the four starter files, output under the blueprint
folder) and safe (drafts only, never promotes to live assets).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scaffold" / "SKILL.md"

STARTER_FILES = ["README.md", "MANUAL.md", "API-REFERENCE.md", "SKILL.skeleton.md"]


def test_skill_exists_with_frontmatter_name():
    assert SKILL.exists()
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: scaffold" in text


def test_skill_declares_blueprint_input():
    text = SKILL.read_text(encoding="utf-8")
    assert "blueprints/" in text
    assert "BLUEPRINT.md" in text


def test_output_under_blueprint_assets_folder():
    text = SKILL.read_text(encoding="utf-8")
    assert "blueprints/<slug>/assets/" in text


def test_lists_the_four_starter_files():
    text = SKILL.read_text(encoding="utf-8")
    for name in STARTER_FILES:
        assert name in text, f"missing starter file: {name}"


def test_safety_drafts_only_not_live():
    text = SKILL.read_text(encoding="utf-8")
    low = text.lower()
    assert "OWNER-DECIDES" in text
    assert "boundary" in low
    # must NOT auto-promote into the real skills/ or scripts/ trees
    assert "not promote" in low or "never" in low
    assert "draft" in low
