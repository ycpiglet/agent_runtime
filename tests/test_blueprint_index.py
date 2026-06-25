"""Tests for blueprint_index — pipeline status board over agents/project/blueprints/.

Reports, per blueprint, which artifacts exist and the next step in the
grill -> enable -> scaffold -> register flow. Drives the stage handoff.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import blueprint_index as bi  # noqa: E402


def _make(tmp_path: Path, slug: str, files: list[str], assets: bool = False) -> None:
    d = tmp_path / "agents" / "project" / "blueprints" / slug
    d.mkdir(parents=True, exist_ok=True)
    for name in files:
        (d / name).write_text("x", encoding="utf-8")
    if assets:
        (d / "assets").mkdir(exist_ok=True)


def test_next_step_grill_when_no_vision(tmp_path):
    _make(tmp_path, "a", ["INTAKE.md", "BLUEPRINT.md"])
    entry = next(b for b in bi.build_index(tmp_path)["blueprints"] if b["slug"] == "a")
    assert entry["artifacts"]["blueprint"] is True
    assert entry["artifacts"]["vision"] is False
    assert "/grill" in entry["next_step"]


def test_next_step_enable_when_vision_but_no_enablement(tmp_path):
    _make(tmp_path, "b", ["BLUEPRINT.md", "VISION-DIRECTION.md"])
    entry = next(b for b in bi.build_index(tmp_path)["blueprints"] if b["slug"] == "b")
    assert entry["next_step"] == "run /enable b"


def test_next_step_scaffold_when_enablement_but_no_assets(tmp_path):
    _make(tmp_path, "c", ["BLUEPRINT.md", "VISION-DIRECTION.md", "ENABLEMENT.md"])
    entry = next(b for b in bi.build_index(tmp_path)["blueprints"] if b["slug"] == "c")
    assert entry["next_step"] == "run /scaffold c"


def test_next_step_register_when_complete(tmp_path):
    _make(tmp_path, "d", ["BLUEPRINT.md", "VISION-DIRECTION.md", "ENABLEMENT.md"], assets=True)
    entry = next(b for b in bi.build_index(tmp_path)["blueprints"] if b["slug"] == "d")
    assert entry["artifacts"]["assets"] is True
    assert "register" in entry["next_step"].lower()
    assert "scripts/work.py" in entry["next_step"]


def test_readme_is_not_treated_as_a_blueprint(tmp_path):
    # the blueprints/README.md file (not a dir) must be ignored
    bp = tmp_path / "agents" / "project" / "blueprints"
    bp.mkdir(parents=True, exist_ok=True)
    (bp / "README.md").write_text("x", encoding="utf-8")
    _make(tmp_path, "real", ["BLUEPRINT.md", "VISION-DIRECTION.md"])
    slugs = {b["slug"] for b in bi.build_index(tmp_path)["blueprints"]}
    assert slugs == {"real"}


def test_cli_prints_valid_json(tmp_path, capsys):
    _make(tmp_path, "a", ["BLUEPRINT.md"])
    rc = bi.main(["--root", str(tmp_path), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema"] == "agent-runtime-blueprint-index/v1"
    assert any(b["slug"] == "a" for b in data["blueprints"])


def test_stage_handoff_wiring():
    skills = ROOT / "skills"
    grill = (skills / "grill" / "SKILL.md").read_text(encoding="utf-8")
    enable = (skills / "enable" / "SKILL.md").read_text(encoding="utf-8")
    scaffold = (skills / "scaffold" / "SKILL.md").read_text(encoding="utf-8")
    assert "/enable" in grill                 # grill -> enable
    assert "/scaffold" in enable              # enable -> scaffold
    assert "blueprint_index.py" in scaffold   # scaffold -> status board
