"""Tests for the v3 agent-character sprites (TASK-AR-592 v3).

v3 pivot: built on the GrafxKid "RPG character" CC0 base; the 34 ORG-MODEL roles
are grouped into 8 CATEGORIES distinguished by an accessory (hat/item) + a
category token color (NOT 34 distinct bodies). Covers the deterministic Python
generator (catalog SVGs on disk), the live JS twin in the served bundle, their
cell-for-cell parity, role->category coverage (all 34 mapped), category
distinctness, the additive Office-Map render + v2 fallback, a11y, and that the
CC0 base is recorded. v1 + v2 are preserved.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "agents" / "project" / "assets" / "agent-characters"
V3_DIR = CHARS / "v3"
V2_DIR = CHARS / "v2"
V1_DIR = CHARS / "v1"

sys.path.insert(0, str(ROOT / "src"))


def _load_v3():
    spec = importlib.util.spec_from_file_location(
        "v3_generator", V3_DIR / "generate_sprites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_v2():
    spec = importlib.util.spec_from_file_location(
        "chibi_v2_generator", V2_DIR / "generate_sprites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Categories: 8 groups, distinct accent + accessory ----------------------

def test_v3_has_eight_categories():
    gen = _load_v3()
    assert len(gen.CATEGORIES) == 8, "Owner brief: ~8 categories"
    ids = [c[0] for c in gen.CATEGORIES]
    assert len(set(ids)) == 8, "category ids must be unique"


def test_v3_categories_are_distinct():
    # Each category must differ by accent OR accessory so its sprite is unique.
    gen = _load_v3()
    svgs = {cid: gen.category_svg(cid) for cid, *_ in gen.CATEGORIES}
    assert len(set(svgs.values())) == len(svgs), "expected distinct category sprites"
    # Pairwise: accent+accessory tuple must be unique per category.
    combos = {(c[2], c[3]) for c in gen.CATEGORIES}
    assert len(combos) == len(gen.CATEGORIES), "accent+accessory combo must be unique"


# --- Role -> category coverage: ALL 34 canonical roles mapped ---------------

def test_v3_role_category_covers_all_canonical_roles():
    gen = _load_v3()
    assert len(gen.CANONICAL_ROLES) == 34, "expected the canonical 34 ORG-MODEL roles"
    valid_categories = {c[0] for c in gen.CATEGORIES}
    for role in gen.CANONICAL_ROLES:
        cat = gen.category_for_role(role)
        assert cat in valid_categories, f"{role} -> unknown category {cat!r}"
    # Every explicit mapping must point at a real category.
    for role, cat in gen.ROLE_CATEGORY.items():
        assert cat in valid_categories, f"{role} maps to unknown category {cat!r}"


def test_v3_role_category_covers_v2_live_roles():
    # Every role the live console maps to an accent (v2) must resolve to a v3
    # category, so swapping to v3 never leaves an agent unmapped.
    gen = _load_v3()
    from agent_runtime import ui_design_assets

    valid = {c[0] for c in gen.CATEGORIES}
    for role in ui_design_assets._AVATAR_ROLE_ACCENT_PY:
        assert gen.category_for_role(role) in valid, f"v2 live role unmapped: {role}"


def test_v3_brief_categories_match_owner_grouping():
    # Spot-check the Owner's category color/role intent.
    gen = _load_v3()
    assert gen.category_for_role("lead-engineer") == "engineering"
    assert gen.category_for_role("worker-engineer") == "engineering"
    assert gen.category_for_role("lead-designer") == "design"
    assert gen.category_for_role("ux-evaluator") == "design"
    assert gen.category_for_role("qa") == "quality-audit"
    assert gen.category_for_role("independent-auditor") == "quality-audit"
    assert gen.category_for_role("research-agent") == "research"
    assert gen.category_for_role("managing-partner") == "leadership"
    assert gen.category_for_role("council") == "leadership"
    assert gen.category_for_role("finance-controller") == "finance-ops"
    assert gen.category_for_role("marketing-lead") == "marketing-sales"
    assert gen.category_for_role("doc-steward") == "docs"


# --- Generator: determinism + on-disk sync ----------------------------------

def test_v3_generator_is_deterministic():
    gen = _load_v3()
    a = gen.category_svg("engineering")
    b = gen.category_svg("engineering")
    assert a == b
    assert a.count("<rect") > 60, "densely filled, not a sparse outline"


def test_v3_on_disk_svgs_are_in_sync_with_generator():
    gen = _load_v3()
    for cat_id, *_rest in gen.CATEGORIES:
        expected = gen.category_svg(cat_id) + "\n"
        path = V3_DIR / f"{cat_id}.svg"
        assert path.is_file(), f"missing catalog SVG: {cat_id}"
        assert path.read_text(encoding="utf-8") == expected, (
            f"{cat_id}.svg out of sync -- rerun generate_sprites.py"
        )


# --- CC0 base recorded ------------------------------------------------------

def test_v3_cc0_base_is_recorded():
    base_dir = V3_DIR / "base"
    sources = base_dir / "SOURCES.md"
    assert sources.is_file(), "v3/base/SOURCES.md must exist"
    text = sources.read_text(encoding="utf-8")
    assert "CC0" in text
    assert "GrafxKid" in text
    assert "attribution" in text.lower()
    # The vendored base PNG itself must be present.
    pngs = list(base_dir.glob("*.png"))
    assert pngs, "v3/base must vendor the CC0 base PNG"


def test_v1_and_v2_preserved():
    # v3 must NOT delete v1 or v2.
    assert (V1_DIR / "generate_sprites.py").is_file()
    assert (V1_DIR / "lead-engineer.svg").is_file()
    assert (V2_DIR / "generate_sprites.py").is_file()
    assert (V2_DIR / "lead-engineer.svg").is_file()


# --- JS twin: served bundle, token-driven, ASCII-only -----------------------

def _bundle_js() -> str:
    from agent_runtime import ui_console

    return ui_console.build_response("/app.js", str(ROOT)).body.decode("utf-8")


def test_js_v3_sprite_present_and_token_driven():
    js = _bundle_js()
    assert "function patternV3Sprite" in js
    assert "function patternOfficeSprite" in js
    # The v3 data + helper block must be ASCII-only (cp949 node guard) and
    # must contain NO raw hex (design-system gate).
    start = js.index("var _V3_BASE")
    end = js.index("function patternOfficeMapPlacement")
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"v3 block must be ASCII-only, found: {non_ascii[:5]}"
    assert not re.search(r"#[0-9a-fA-F]{3,8}", block), "v3 JS twin must be hex-free"


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
    path = tmp_path / "v3_runner.mjs"
    path.write_text(script, encoding="utf-8")
    proc = subprocess.run(["node", str(path)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def _v3_harness(js: str) -> str:
    data = js[js.index("var _V3_BASE"):js.index("function _v3Fill")]
    shim = (
        "const escapeHtml=(s)=>String(s==null?\"\":s)"
        ".replace(/[&<>\"']/g,c=>({\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\","
        "'\\\"':\"&quot;\",\"'\":\"&#39;\"}[c]));\n"
    )
    return (
        shim
        + data
        + _extract(js, "_v3Fill")
        + _extract(js, "v3CategoryForRole")
        + _extract(js, "patternV3Sprite")
        + 'var OFFICE_SPRITE_ASSET_VERSION = "v3";\n'
        + _extract(js, "patternOfficeSprite")
    )


def test_js_v3_sprite_runs_and_is_category_distinct(tmp_path):
    js = _bundle_js()
    script = _v3_harness(js) + """
const eng = patternV3Sprite("lead-engineer", { size: 30 });
const des = patternV3Sprite("lead-designer", { size: 30 });
const qa = patternV3Sprite("qa", { size: 30 });
const lead = patternV3Sprite("managing-partner", { size: 30 });
const docs = patternV3Sprite("doc-steward", { size: 30 });
// same-category roles share a sprite (by design)
const eng2 = patternV3Sprite("worker-engineer", { size: 30 });
process.stdout.write(JSON.stringify({
  engIsSvg: eng.startsWith("<svg"),
  engHasPrimary: eng.includes("var(--primary)"),
  desHasTeal: des.includes("var(--teal)"),
  qaHasDanger: qa.includes("var(--danger)"),
  leadHasViolet: lead.includes("var(--violet)"),
  docsHasMuted: docs.includes("var(--muted)"),
  engHasSkin: eng.includes("var(--office-skin)"),
  engNoHex: !/#[0-9a-fA-F]{3,8}/.test(eng),
  distinct: (new Set([eng, des, qa, lead, docs])).size === 5,
  sameCategorySame: eng === eng2,
}));
"""
    data = json.loads(_run_node(tmp_path, script))
    assert data["engIsSvg"]
    assert data["engHasPrimary"]
    assert data["desHasTeal"]
    assert data["qaHasDanger"]
    assert data["leadHasViolet"]
    assert data["docsHasMuted"]
    assert data["engHasSkin"]
    assert data["engNoHex"]
    assert data["distinct"], "categories must be visually distinct"
    assert data["sameCategorySame"], "same-category roles share a sprite by design"


def test_js_v3_sprite_a11y_label_and_role(tmp_path):
    js = _bundle_js()
    script = _v3_harness(js) + """
const s = patternV3Sprite("qa", { size: 26, label: "Quinn the QA" });
process.stdout.write(s);
"""
    out = _run_node(tmp_path, script)
    assert 'role="img"' in out
    assert "<title>Quinn the QA</title>" in out
    assert 'aria-hidden="true"' in out


def test_js_v3_unknown_role_falls_back_to_base_category(tmp_path):
    js = _bundle_js()
    script = _v3_harness(js) + """
const s = patternV3Sprite("totally-unknown-role", { size: 26 });
process.stdout.write(JSON.stringify({ isSvg: s.startsWith("<svg"), len: s.length }));
"""
    data = json.loads(_run_node(tmp_path, script))
    assert data["isSvg"]
    assert data["len"] > 500


def test_js_office_sprite_additive_v2_fallback(tmp_path):
    # patternOfficeSprite prefers v3 but falls back to the v2 chibi twin when a
    # caller pins assetVersion="v2" (graceful v2-fallback path; v2 preserved).
    js = _bundle_js()
    # The fallback path calls patternChibiSprite, so include its harness too.
    chibi = (
        js[js.index("var _CHIBI_BASE"):js.index("function _chibiFill")]
        + _extract(js, "_chibiFill")
        + _extract(js, "patternChibiSprite")
    )
    script = _v3_harness(js) + chibi + """
const v3 = patternOfficeSprite("lead-engineer", { size: 30, assetVersion: "v3" });
const v2 = patternOfficeSprite("lead-engineer", { size: 30, assetVersion: "v2" });
process.stdout.write(JSON.stringify({
  v3IsV3: v3.includes("v3-sprite"),
  v2IsChibi: v2.includes("chibi-sprite"),
  bothSvg: v3.startsWith("<svg") && v2.startsWith("<svg"),
  different: v3 !== v2,
}));
"""
    data = json.loads(_run_node(tmp_path, script))
    assert data["v3IsV3"], "default/v3 path returns a v3 sprite"
    assert data["v2IsChibi"], "v2-fallback path returns the v2 chibi sprite"
    assert data["bothSvg"]
    assert data["different"]


# --- Office-Map render: placement injects a v3 sprite -----------------------

class _FakeClassList:
    def __init__(self):
        self._set = set()

    def add(self, *names):
        self._set.update(names)


class _FakeNode:
    def __init__(self, doc, tag):
        self._doc = doc
        self.tag = tag
        self.className = ""
        self.textContent = ""
        self.innerHTML = ""
        self.title = ""
        self.children = []
        self.style = type("S", (), {})()
        self.dataset = type("D", (), {})()
        self.attrs = {}
        self.firstChild = None

    def appendChild(self, child):
        self.children.append(child)
        self.firstChild = self.children[0] if self.children else None
        return child

    def removeChild(self, child):
        if child in self.children:
            self.children.remove(child)
        self.firstChild = self.children[0] if self.children else None

    def setAttribute(self, k, v):
        self.attrs[k] = v

    def _walk(self):
        yield self
        for c in self.children:
            yield from c._walk()


def test_office_map_render_uses_v3_sprite_via_node(tmp_path):
    # Drive the real patternOfficeMapPlacement in node with a tiny DOM stub and
    # assert the injected avatar sprite is a v3 sprite carrying the agent label.
    js = _bundle_js()
    # Compose the full sprite stack + placement function.
    chibi = (
        js[js.index("var _CHIBI_BASE"):js.index("function _chibiFill")]
        + _extract(js, "_chibiFill")
        + _extract(js, "patternChibiSprite")
    )
    shim = (
        "const escapeHtml=(s)=>String(s==null?\"\":s)"
        ".replace(/[&<>\"']/g,c=>({\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\","
        "'\\\"':\"&quot;\",\"'\":\"&#39;\"}[c]));\n"
    )
    v3 = (
        js[js.index("var _V3_BASE"):js.index("function _v3Fill")]
        + _extract(js, "_v3Fill")
        + _extract(js, "v3CategoryForRole")
        + _extract(js, "patternV3Sprite")
        + 'var OFFICE_SPRITE_ASSET_VERSION = "v3";\n'
        + _extract(js, "patternOfficeSprite")
    )
    placement = _extract(js, "patternOfficeMapPlacement")
    dom = """
function el(tag){ return { tag, className:"", textContent:"", innerHTML:"",
  title:"", style:{}, dataset:{}, attrs:{}, children:[], firstChild:null,
  appendChild(c){ this.children.push(c); this.firstChild=this.children[0]; return c; },
  removeChild(c){ const i=this.children.indexOf(c); if(i>=0)this.children.splice(i,1);
    this.firstChild=this.children[0]||null; },
  setAttribute(k,v){ this.attrs[k]=v; } }; }
const doc = { createElement: el };
const grid = el("div");
const rooms = [{ id:"dev", name:"Dev Room", token:"blue",
  rect:{col:0,row:0,cols:6,rows:4} }];
const agents = [{ id:"a1", role:"lead-engineer", room_id:"dev",
  display_name:"Lead Eng", action_label:"working", current_task_id:"TASK-AR-592",
  presence:"working", cell:{fx:0.5,fy:0.5}, glyph:"X", callsign:"ENG" }];
patternOfficeMapPlacement(grid, rooms, agents, { document: doc });
function walk(n, out){ out.push(n); n.children.forEach(c=>walk(c,out)); }
const all=[]; walk(grid, all);
const sprite = all.find(n => n.className === "office-agent-sprite");
const labeled = all.find(n => n.attrs && n.attrs["aria-label"]);
process.stdout.write(JSON.stringify({
  hasSprite: !!sprite,
  spriteIsV3: !!sprite && sprite.innerHTML.includes("v3-sprite"),
  ariaLabel: labeled ? labeled.attrs["aria-label"] : "",
}));
"""
    script = shim + chibi + v3 + placement + dom
    data = json.loads(_run_node(tmp_path, script))
    assert data["hasSprite"], "office map must place an agent sprite"
    assert data["spriteIsV3"], "placed sprite must be a v3 sprite"
    assert "Lead Eng" in data["ariaLabel"]
    assert "TASK-AR-592" in data["ariaLabel"]
    assert "working" in data["ariaLabel"]


# --- Parity: JS twin matches the Python catalog cell-for-cell --------------

def _resolve_python_cell_fills(gen, category_id):
    """Return [(x, y, var_fill)] for a Python-rendered category, CSS-class
    indirection normalized to a bare ``var(--token)`` (hex fallback stripped)."""
    disp, accent, accessory, _tok, _blurb = gen.CATEGORY_BY_ID[category_id][1:]
    pal = gen._resolve_palette(accent)
    cls_to_key = {v: k for k, v in gen._CLASS_TABLE.items()}
    grid = gen.compose_grid(accessory)
    svg = gen.render_svg(grid, accent, "t")
    rects = re.findall(r'<rect x="(\d+)" y="(\d+)"[^>]*class="p([A-Za-z0-9]+)"', svg)
    out = []
    for x, y, cls in rects:
        key = cls_to_key[cls]
        var, _hexv = pal[key]
        var = var.split(",")[0].rstrip(") ") + ")"  # strip hex fallback -> bare var()
        out.append((x, y, var))
    return out


def test_js_and_python_v3_grids_match(tmp_path):
    gen = _load_v3()
    py_rects = _resolve_python_cell_fills(gen, "engineering")

    js = _bundle_js()
    script = _v3_harness(js) + """
process.stdout.write(patternV3Sprite("lead-engineer", { size: 128 }));
"""
    js_svg = _run_node(tmp_path, script)
    js_rects = re.findall(r'<rect x="(\d+)" y="(\d+)"[^>]*fill="([^"]+)"', js_svg)
    assert js_rects == py_rects, "JS twin diverged from Python catalog grid (engineering)"
