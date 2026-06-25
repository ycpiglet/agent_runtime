"""Tests for the v2 chibi office-character sprites (TASK-AR-592 v2).

Covers the deterministic Python generator (catalog SVGs on disk), the live
JS twin embedded in the served bundle, and their cell-for-cell parity. Owner
acceptance: colourful, role-distinct chibi sprites with a FILLED center (no
empty middle), token-driven (no raw hex in the served bundle), accessible
(label/role, not color-only).
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
V2_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v2"
V1_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v1"

sys.path.insert(0, str(ROOT / "src"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "chibi_v2_generator", V2_DIR / "generate_sprites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Generator: determinism + role coverage --------------------------------

def test_v2_generator_role_coverage_matches_avatar_accent_map():
    # Every role with a sprite must map to a real accent key, and the set must
    # cover the live console's role->accent map (so no agent renders blank).
    gen = _load_generator()
    from agent_runtime import ui_design_assets

    role_ids = {r[0] for r in gen.ROLES}
    accent_keys = {r[2] for r in gen.ROLES}
    assert accent_keys <= set(gen.ACCENTS), "unknown accent key in ROLES"
    # The 25 roles that drive the office map (the JS _AVATAR_ROLE_ACCENT set)
    # must all have a sprite.
    live_roles = set(ui_design_assets._AVATAR_ROLE_ACCENT_PY)
    missing = live_roles - role_ids
    assert not missing, f"roles with no chibi sprite: {sorted(missing)}"
    assert len(gen.ROLES) >= 25


def test_v2_generator_is_deterministic():
    # Same role -> byte-identical SVG across two independent renders.
    gen = _load_generator()
    role = gen.ROLES[1]  # lead-engineer
    grid = gen.role_grid(role[3])
    a = gen.render_svg(grid, role[2], "x")
    b = gen.render_svg(grid, role[2], "x")
    assert a == b
    assert a.count("<rect") > 60  # densely filled, not a sparse outline


def test_v2_role_sprites_are_distinct():
    # Roles with different accent OR different prop must produce different SVGs
    # (role-distinct requirement). Compare lead-engineer vs lead-designer vs qa.
    gen = _load_generator()
    by_id = {r[0]: r for r in gen.ROLES}
    svgs = {}
    for rid in ("lead-engineer", "lead-designer", "qa", "managing-partner"):
        _, _, accent, prop, _d = by_id[rid]
        svgs[rid] = gen.render_svg(gen.role_grid(prop), accent, rid)
    assert len(set(svgs.values())) == len(svgs), "expected role-distinct sprites"


def test_v2_on_disk_svgs_are_in_sync_with_generator():
    # The committed catalog SVGs must equal a fresh render (regen discipline).
    gen = _load_generator()
    for role_id, display, accent, prop, _desc in gen.ROLES:
        expected = gen.render_svg(
            gen.role_grid(prop), accent, f"{display} -- agent character (chibi v2)"
        )
        path = V2_DIR / f"{role_id}.svg"
        assert path.is_file(), f"missing catalog SVG: {role_id}"
        assert path.read_text(encoding="utf-8") == expected, (
            f"{role_id}.svg out of sync -- rerun generate_sprites.py"
        )


def test_v2_fills_the_center_more_than_v1():
    # Owner feedback: v1 felt empty in the middle. v2 must paint the head
    # interior with skin (not the near-white panel tint), so the center column
    # band of the sprite is solidly filled. Assert v2 has strictly more painted
    # cells than v1 for the same role.
    gen = _load_generator()
    v2_svg = (V2_DIR / "lead-engineer.svg").read_text(encoding="utf-8")
    v1_svg = (V1_DIR / "lead-engineer.svg").read_text(encoding="utf-8")
    v2_cells = v2_svg.count("<rect")
    v1_cells = v1_svg.count("<rect")
    assert v2_cells > v1_cells, f"v2 ({v2_cells}) should fill more than v1 ({v1_cells})"
    # v2 introduces a dedicated warm skin fill that v1 lacked.
    assert "--office-skin" in v2_svg
    assert "--office-hair" in v2_svg


def test_v1_preserved():
    # v1 must NOT be deleted by the v2 work.
    assert (V1_DIR / "generate_sprites.py").is_file()
    assert (V1_DIR / "lead-engineer.svg").is_file()


# --- JS twin: served bundle, token-driven, ASCII-only ----------------------

def _bundle_js() -> str:
    from agent_runtime import ui_console

    return ui_console.build_response("/app.js", str(ROOT)).body.decode("utf-8")


def test_js_chibi_sprite_present_and_token_driven():
    js = _bundle_js()
    assert "function patternChibiSprite" in js
    # The sprite data + helper block must be ASCII-only (cp949 node-check guard).
    start = js.index("var _CHIBI_BASE")
    end = js.index("function patternOfficeMapPlacement")
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"chibi block must be ASCII-only, found: {non_ascii[:5]}"


def _extract(js: str, name: str) -> str:
    match = re.search(r"function " + re.escape(name) + r"\s*\(", js)
    assert match, name
    cursor = match.end() - 1
    depth = 0
    while cursor < len(js):
        if js[cursor] == "(":
            depth += 1
        elif js[cursor] == ")":
            depth -= 1
            if depth == 0:
                break
        cursor += 1
    body = js.index("{", cursor)
    depth = 0
    pos = body
    while pos < len(js):
        if js[pos] == "{":
            depth += 1
        elif js[pos] == "}":
            depth -= 1
            if depth == 0:
                return js[match.start():pos + 1]
        pos += 1
    raise AssertionError(name)


def _run_node(tmp_path, script: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node not available")
    path = tmp_path / "chibi_runner.mjs"
    path.write_text(script, encoding="utf-8")
    proc = subprocess.run(["node", str(path)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _chibi_harness(js: str) -> str:
    data = js[js.index("var _CHIBI_BASE"):js.index("function _chibiFill")]
    shim = (
        "const escapeHtml=(s)=>String(s==null?\"\":s)"
        ".replace(/[&<>\"']/g,c=>({\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\","
        "'\\\"':\"&quot;\",\"'\":\"&#39;\"}[c]));\n"
    )
    return shim + data + _extract(js, "_chibiFill") + _extract(js, "patternChibiSprite")


def test_js_chibi_sprite_runs_and_is_role_distinct(tmp_path):
    js = _bundle_js()
    script = _chibi_harness(js) + """
const eng = patternChibiSprite("lead-engineer", { size: 30 });
const des = patternChibiSprite("lead-designer", { size: 30 });
const qa = patternChibiSprite("qa", { size: 30 });
process.stdout.write(JSON.stringify({
  eng, des, qa,
  engIsSvg: eng.startsWith("<svg"),
  engHasPrimary: eng.includes("var(--primary)"),
  desHasTeal: des.includes("var(--teal)"),
  engHasSkin: eng.includes("var(--office-skin)"),
  engNoHex: !/#[0-9a-fA-F]{3,8}/.test(eng),
  distinct: (new Set([eng, des, qa])).size === 3,
}));
"""
    import json

    data = json.loads(_run_node(tmp_path, script))
    assert data["engIsSvg"]
    assert data["engHasPrimary"]
    assert data["desHasTeal"]
    assert data["engHasSkin"]  # filled center
    assert data["engNoHex"]  # token-driven (design-system gate)
    assert data["distinct"]  # role-distinct


def test_js_chibi_sprite_a11y_label_and_role(tmp_path):
    # Sprite carries role="img" + a <title> built from the label, never relying
    # on color alone to convey identity.
    js = _bundle_js()
    script = _chibi_harness(js) + """
const s = patternChibiSprite("qa", { size: 26, label: "Quinn the QA" });
process.stdout.write(s);
"""
    out = _run_node(tmp_path, script)
    assert 'role="img"' in out
    assert "<title>Quinn the QA</title>" in out
    assert 'aria-hidden="true"' in out  # decorative pixels hidden from SR


def test_js_chibi_sprite_unknown_role_falls_back_to_base(tmp_path):
    # An unmapped role still yields a non-empty base sprite (slot never blank).
    js = _bundle_js()
    script = _chibi_harness(js) + """
const s = patternChibiSprite("totally-unknown-role", { size: 26 });
process.stdout.write(JSON.stringify({ isSvg: s.startsWith("<svg"), len: s.length }));
"""
    import json

    data = json.loads(_run_node(tmp_path, script))
    assert data["isSvg"]
    assert data["len"] > 500


# --- Parity: JS twin matches the Python catalog cell-for-cell --------------

def _resolve_python_cell_fills(gen, role_id):
    """Return [(x, y, var_fill)] for a Python-rendered role, hex fallbacks and
    CSS-class indirection both normalized to a bare ``var(--token)``."""
    by_id = {r[0]: r for r in gen.ROLES}
    _, _display, accent, prop, _d = by_id[role_id]
    pal = gen._resolve_palette(accent)
    # class suffix -> art key (invert _CLASS_TABLE), then art key -> var token.
    cls_to_key = {v: k for k, v in gen._CLASS_TABLE.items()}
    svg = gen.render_svg(gen.role_grid(prop), accent, "t")
    rects = re.findall(r'<rect x="(\d+)" y="(\d+)"[^>]*class="p([A-Za-z0-9]+)"', svg)
    out = []
    for x, y, cls in rects:
        key = cls_to_key[cls]
        var, _hexv = pal[key]
        out.append((x, y, var))
    return out


def test_js_and_python_chibi_grids_match(tmp_path):
    # The JS BASE/PROPS/ROLE maps must equal the Python generator's, so the
    # served sprite matches the on-disk catalog SVG cell-for-cell.
    gen = _load_generator()
    py_rects = _resolve_python_cell_fills(gen, "lead-engineer")

    js = _bundle_js()
    script = _chibi_harness(js) + """
process.stdout.write(patternChibiSprite("lead-engineer", { size: 128 }));
"""
    js_svg = _run_node(tmp_path, script)
    js_rects = re.findall(r'<rect x="(\d+)" y="(\d+)"[^>]*fill="([^"]+)"', js_svg)
    assert js_rects == py_rects, "JS twin diverged from Python catalog grid"
