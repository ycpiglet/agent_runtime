"""Tests for enablement_index — a machine-readable index of skills for /enable.

Generated at runtime from each skill's SKILL.md frontmatter (no committed snapshot,
so it never goes stale). /enable consults it for exact skill recommendations.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enablement_index as ei  # noqa: E402


def test_index_lists_skills():
    idx = ei.build_index(ROOT)
    names = {s["name"] for s in idx["skills"]}
    assert "grill" in names and "enable" in names


def test_index_entries_have_description_and_path():
    idx = ei.build_index(ROOT)
    by_name = {s["name"]: s for s in idx["skills"]}
    assert by_name["grill"]["description"]
    assert by_name["enable"]["path"] == "skills/enable"
    assert isinstance(by_name["grill"]["triggers"], list)


def test_index_is_json_serializable():
    idx = ei.build_index(ROOT)
    json.dumps(idx)  # must not raise
    assert idx["schema"] == "agent-runtime-enablement-index/v1"


def test_cli_prints_valid_json(capsys):
    rc = ei.main(["--root", str(ROOT), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert any(s["name"] == "enable" for s in data["skills"])


def test_enable_skill_references_the_index_generator():
    text = (ROOT / "skills" / "enable" / "SKILL.md").read_text(encoding="utf-8")
    assert "enablement_index.py" in text
    assert "version: 1.1.0" in text
