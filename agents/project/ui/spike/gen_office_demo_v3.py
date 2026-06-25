#!/usr/bin/env python3
"""Generate office-map-demo-v3.html for the v3 agent-sprite system (TASK-AR-592 v3).

Self-contained: replicates the real Office Map (office CSS + room layout + the
v3 CATEGORY sprites) populated with ~12 SAMPLE agents so the Owner can SEE the
v3 look FILLED. Renders each v3 sprite with INLINE fill= attributes (resolved
from the deterministic generator), so multiple sprites on one page never collide
on shared CSS classes -- exactly how the live JS twin (patternV3Sprite) emits.

Reads NOTHING from the live console at runtime; it only copies the static CSS /
room rects we already use, so the live console is untouched. The v3 sprites are
built on the GrafxKid "RPG character" CC0 base (provenance: v3/base/SOURCES.md).
"""
from __future__ import annotations

import html
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve()
# .../agents/project/ui/spike/gen_office_demo_v3.py -> repo worktree root
ROOT = HERE.parents[4]
V3_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v3"
OUT = HERE.parent / "office-map-demo-v3.html"


def _load_v3():
    spec = importlib.util.spec_from_file_location("v3_gen", V3_DIR / "generate_sprites.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_v3()

OFFICE_MAP_COLS = 12
OFFICE_MAP_ROWS = 8
ROOMS = [
    {"id": "planning", "name": "Planning Room", "token": "violet",
     "rect": {"col": 0, "row": 0, "cols": 6, "rows": 4}},
    {"id": "dev", "name": "Dev Room", "token": "blue",
     "rect": {"col": 6, "row": 0, "cols": 6, "rows": 4}},
    {"id": "qa", "name": "QA Room", "token": "amber",
     "rect": {"col": 0, "row": 4, "cols": 4, "rows": 4}},
    {"id": "meeting", "name": "Meeting Room", "token": "primary",
     "rect": {"col": 4, "row": 4, "cols": 4, "rows": 4}},
    {"id": "release", "name": "Release Room", "token": "success",
     "rect": {"col": 8, "row": 4, "cols": 4, "rows": 4}},
]

ACTION_GLYPHS = {
    "working": "\U0001F4BB", "recording": "\U0001F4DD", "reviewing": "\U0001F50D",
    "meeting": "\U0001F465", "idle": "\U0001F4A4",
}
ACTION_LABELS = {
    "working": "working", "recording": "recording", "reviewing": "reviewing",
    "meeting": "in meeting", "idle": "idle",
}

# 12 SAMPLE agents covering ALL 8 categories (role -> v3 category sprite).
AGENTS = [
    # Planning Room (violet) -- Leadership + Research
    {"name": "Mng Partner", "role": "managing-partner", "room": "planning",
     "presence": "working", "action": "recording", "task": "Drafting portfolio memo"},
    {"name": "Council", "role": "council", "room": "planning",
     "presence": "online", "action": "idle", "task": "Awaiting escalation"},
    {"name": "Research", "role": "research-agent", "room": "planning",
     "presence": "reviewing", "action": "reviewing", "task": "Scanning CC0 sources"},
    {"name": "Biz Analyst", "role": "business-analyst", "room": "planning",
     "presence": "working", "action": "working", "task": "Sizing TASK-AR-592"},
    # Dev Room (blue) -- Engineering
    {"name": "Lead Eng.", "role": "lead-engineer", "room": "dev",
     "presence": "working", "action": "working", "task": "Wiring v3 sprite slot"},
    {"name": "Worker Eng.", "role": "worker-engineer", "room": "dev",
     "presence": "working", "action": "working", "task": "Generating category SVGs"},
    {"name": "Doc Steward", "role": "doc-steward", "room": "dev",
     "presence": "online", "action": "recording", "task": "Updating ASSET-REFERENCES"},
    # QA Room (amber) -- Quality/Audit
    {"name": "QA", "role": "qa", "room": "qa",
     "presence": "reviewing", "action": "reviewing", "task": "Running gate chain"},
    {"name": "Auditor", "role": "independent-auditor", "room": "qa",
     "presence": "reviewing", "action": "reviewing", "task": "Auditing release SHA"},
    # Release Room (success) -- Finance/Ops + Marketing/Sales
    {"name": "Finance", "role": "finance-controller", "room": "release",
     "presence": "working", "action": "working", "task": "Unit economics review"},
    {"name": "Marketing", "role": "marketing-lead", "room": "release",
     "presence": "online", "action": "recording", "task": "Drafting launch note"},
    # Meeting Room (primary) -- Design
    {"name": "Lead Design", "role": "lead-designer", "room": "meeting",
     "presence": "in_meeting", "action": "meeting", "task": "v3 sprite design review"},
]

# --- Office CSS (mirrors ui_console_assets.py; .v3-sprite sized like chibi) ---
OFFICE_CSS = """
.office-map { display: flex; flex-direction: column; gap: var(--space-2xl); }
.office-map-header {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: var(--space-2xl); flex-wrap: wrap;
}
.office-map-header h2 { margin: 0; }
.office-map-summary { margin: 0; font-size: var(--font-size-ui-12); color: var(--muted); }
.office-map-stage {
  border: 1px solid var(--office-room-line); border-radius: var(--radius-xl);
  padding: var(--space-xl); background: var(--office-floor);
}
.office-map-grid {
  position: relative; display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: repeat(8, minmax(34px, 1fr));
  gap: var(--space-md); width: 100%; aspect-ratio: 3 / 2;
}
.office-room {
  position: relative; border: 1px solid var(--office-room-line);
  border-top: 3px solid var(--office-room-line); border-radius: var(--radius-lg);
  background: var(--office-room-bg); padding: var(--space-md) var(--space-lg);
  overflow: hidden;
}
.office-room.token-violet { border-top-color: var(--violet); }
.office-room.token-blue { border-top-color: var(--blue); }
.office-room.token-amber { border-top-color: var(--amber); }
.office-room.token-success { border-top-color: var(--success); }
.office-room.token-primary { border-top-color: var(--primary); }
.office-room-name {
  font-size: var(--font-size-ui-11); font-weight: 600; color: var(--muted);
  letter-spacing: 0.02em;
}
.office-room-count { font-size: var(--font-size-ui-10); color: var(--subtle); }
.office-agent {
  position: absolute; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center;
  gap: var(--space-hairline); width: 46px; text-align: center;
}
.office-agent-glyph { font-size: var(--font-size-ui-14); line-height: 1; }
.office-agent-sprite {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--font-size-ui-10); font-weight: 700; color: var(--ink);
  background: var(--office-avatar-bg); border: 2px solid var(--office-room-line);
  animation: office-idle-bob 3.2s ease-in-out infinite;
}
.office-agent-sprite .v3-sprite {
  width: 30px; height: 30px; display: block; image-rendering: pixelated;
}
.office-agent.presence-working .office-agent-sprite { border-color: var(--blue); }
.office-agent.presence-reviewing .office-agent-sprite { border-color: var(--amber); }
.office-agent.presence-in_meeting .office-agent-sprite { border-color: var(--violet); }
.office-agent.presence-online .office-agent-sprite { border-color: var(--success); }
.office-agent.presence-offline .office-agent-sprite {
  border-color: var(--office-room-line); opacity: 0.7; animation: none;
}
.office-agent.presence-working .office-agent-sprite { animation-delay: 0s; }
.office-agent.presence-reviewing .office-agent-sprite { animation-delay: 0.5s; }
.office-agent.presence-in_meeting .office-agent-sprite { animation-delay: 1s; }
.office-agent.presence-online .office-agent-sprite { animation-delay: 1.5s; }
@keyframes office-idle-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
@media (prefers-reduced-motion: reduce) { .office-agent-sprite { animation: none; } }
.office-agent-status {
  font-size: var(--font-size-ui-9); font-weight: 600; color: var(--muted);
  letter-spacing: 0.02em; max-width: 46px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}
.office-agent-name {
  font-size: var(--font-size-ui-9); color: var(--muted); max-width: 46px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.office-map-legend {
  display: flex; flex-wrap: wrap; gap: var(--space-3xl); margin: 0; padding: 0;
  list-style: none; font-size: var(--font-size-ui-11); color: var(--muted);
}
.office-map-legend li { display: inline-flex; align-items: center; gap: var(--space-md); }
.office-map-legend .legend-glyph { font-size: var(--font-size-ui-14); }
.cat-legend { display:flex; flex-wrap:wrap; gap:14px; max-width:980px; margin:0 auto 16px; }
.cat-legend .chip { display:inline-flex; align-items:center; gap:6px;
  font-size:11px; color:var(--muted); border:1px solid var(--line-strong);
  border-radius:8px; padding:4px 8px; background:var(--panel); }
.cat-legend .chip svg { width:24px; height:24px; image-rendering:pixelated; }
"""

# Token defaults so the demo is self-contained (light + dark subset).
TOKENS = """
:root {
  color-scheme: light;
  --font-sans: "Geist", "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --canvas:#ffffff; --paper:#ffffff; --panel:#f7f7f5; --panel-strong:#f1f1ef;
  --ink:#37352f; --muted:#787774; --subtle:#9b9a97; --on-accent:#ffffff;
  --line:#e9e9e7; --line-strong:#d3d1cb;
  --primary:#2e6fdb; --primary-hover:#1f5bc0; --success:#0f7b55;
  --warning:#cb7509; --danger:#e03e3e; --teal:#0f9488; --blue:#2e6fdb;
  --amber:#cb7509; --red:#e03e3e; --violet:#6a48c9; --info:#2e6fdb;
  --primary-soft:#dde8f9; --teal-soft:#d2efeb; --danger-soft:#fbdada;
  --violet-soft:#e3dbf6; --warning-soft:#f7e4c8; --success-soft:#cfeadd;
  --raise-strong:#e6e6e3;
  --surface-grad: linear-gradient(180deg, var(--panel), var(--panel));
  --shadow-pop: 0 10px 30px rgba(15,15,15,0.16);
  --office-floor: var(--surface-grad); --office-room-bg: var(--panel);
  --office-room-line: var(--line-strong); --office-avatar-bg: var(--panel-strong);
  --office-skin:#f6caa6; --office-skin-shade:#e0a878; --office-hair:#5b4636;
  --font-size-ui-9:9px; --font-size-ui-10:10px; --font-size-ui-11:11px;
  --font-size-ui-12:12px; --font-size-ui-13:13px; --font-size-ui-14:14px;
  --font-size-ui-16:16px; --font-size-ui-22:22px;
  --space-hairline:1px; --space-md:6px; --space-lg:8px; --space-xl:10px;
  --space-2xl:12px; --space-3xl:14px; --space-4xl:16px;
  --radius:8px; --radius-lg:10px; --radius-xl:12px;
}
[data-theme="dark"] {
  color-scheme: dark;
  --canvas:#010102; --paper:#010102; --panel:#0f1011; --panel-strong:#15171a;
  --ink:#f7f8f8; --muted:#a2a8b3; --subtle:#62666d; --on-accent:#ffffff;
  --line:#23252a; --line-strong:#343844;
  --primary:#5e6ad2; --success:#27a644; --warning:#d99a2b; --danger:#f04438;
  --blue:#57a0ff; --amber:#d99a2b; --violet:#5e6ad2; --teal:#2dd4bf;
  --primary-soft:#1c2740; --teal-soft:#0e3b37; --danger-soft:#3a1717;
  --violet-soft:#211c40; --warning-soft:#3a2c12; --success-soft:#10311f;
  --raise-strong:#23252a;
  --office-skin:#f6caa6; --office-skin-shade:#cf9a64; --office-hair:#6b5240;
}
"""


def v3_inline_svg(role: str, size: int = 30) -> str:
    """Render the role's v3 category sprite with INLINE fills (collision-free)."""
    cat_id = GEN.category_for_role(role)
    _disp, accent, accessory, _tok, _blurb = GEN.CATEGORY_BY_ID[cat_id][1:]
    grid = GEN.compose_grid(accessory)
    pal = GEN._resolve_palette(accent)
    px = 8
    rects = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            var = pal[ch][0].split(",")[0].rstrip(") ") + ")"  # bare var()
            rects.append(
                f'<rect x="{c * px}" y="{r * px}" width="{px}" height="{px}" fill="{var}"/>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
        f'width="{size}" height="{size}" class="agent-character v3-sprite" '
        f'shape-rendering="crispEdges" role="img" aria-hidden="true">'
        + "".join(rects)
        + "</svg>"
    )


def agent_cells():
    by_room: dict[str, list[dict]] = {}
    for a in AGENTS:
        by_room.setdefault(a["room"], []).append(a)
    placed = []
    for room in ROOMS:
        occ = by_room.get(room["id"], [])
        count = len(occ)
        per_row = max(1, int(count ** 0.5 + 0.999)) if count else 1
        rows_used = max(1, (count + per_row - 1) // per_row) if count else 1
        for i, a in enumerate(occ):
            col = i % per_row
            row = i // per_row
            fx = (col + 0.5) / per_row
            fy = (row + 0.5) / rows_used
            placed.append((room, a, fx, fy))
    return placed


def render_room(room: dict) -> str:
    r = room["rect"]
    style = (f"grid-column: {r['col'] + 1} / span {r['cols']}; "
             f"grid-row: {r['row'] + 1} / span {r['rows']};")
    count = sum(1 for a in AGENTS if a["room"] == room["id"])
    return (
        f'<div class="office-room token-{room["token"]}" style="{style}">'
        f'<div class="office-room-name">{html.escape(room["name"])}</div>'
        f'<div class="office-room-count">{count} agents</div>'
        f'</div>'
    )


def render_agent(room, a, fx, fy) -> str:
    r = room["rect"]
    left = (r["col"] + fx * r["cols"]) / OFFICE_MAP_COLS * 100
    top = (r["row"] + fy * r["rows"]) / OFFICE_MAP_ROWS * 100
    glyph = ACTION_GLYPHS[a["action"]]
    label = ACTION_LABELS[a["action"]]
    sprite = v3_inline_svg(a["role"])
    role = a["role"]
    cat = GEN.category_for_role(role)
    tip = f"{role} · {label} · {a['task']}"
    return (
        f'<div class="office-agent presence-{a["presence"]}" '
        f'style="left:{left:.2f}%; top:{top:.2f}%;" '
        f'role="img" aria-label="{html.escape(tip)}" '
        f'title="{html.escape(tip)}" '
        f'data-role="{html.escape(role)}" data-cat="{html.escape(cat)}" '
        f'data-status="{html.escape(label)}" data-task="{html.escape(a["task"])}">'
        f'<span class="office-agent-glyph" aria-hidden="true">{glyph}</span>'
        f'<span class="office-agent-sprite">{sprite}</span>'
        f'<span class="office-agent-name">{html.escape(a["name"])}</span>'
        f'<span class="office-agent-status">{html.escape(label)}</span>'
        f'</div>'
    )


def build() -> str:
    rooms_html = "\n".join(render_room(r) for r in ROOMS)
    agents_html = "\n".join(render_agent(*p) for p in agent_cells())
    legend = "".join(
        f'<li><span class="legend-glyph">{g}</span> {ACTION_LABELS[k]}</li>'
        for k, g in ACTION_GLYPHS.items()
    )
    cat_chips = "".join(
        f'<span class="chip">{v3_inline_svg_for_cat(cid, 24)}'
        f'{html.escape(disp)} ({tok})</span>'
        for cid, disp, _acc, _accs, tok, _b in GEN.CATEGORIES
    )
    total = len(AGENTS)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Office Map Demo v3 -- GrafxKid-CC0 category sprites</title>
<style>
{TOKENS}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 24px; background: var(--canvas); color: var(--ink);
  font-family: var(--font-sans);
}}
.spike-banner {{
  max-width: 980px; margin: 0 auto 18px; padding: 12px 16px;
  border: 1px solid var(--line-strong); border-left: 3px solid var(--primary);
  border-radius: 8px; background: var(--panel); font-size: 13px; color: var(--muted);
}}
.spike-banner b {{ color: var(--ink); }}
.spike-controls {{ max-width: 980px; margin: 0 auto 14px; display:flex; gap:10px; }}
.spike-controls button {{
  font: inherit; font-size: 12px; padding: 6px 12px; cursor: pointer;
  border: 1px solid var(--line-strong); border-radius: 8px;
  background: var(--panel); color: var(--ink);
}}
.office-map {{ max-width: 980px; margin: 0 auto; }}
{OFFICE_CSS}
.office-agent {{ cursor: pointer; }}
.office-agent .tip {{
  position: absolute; bottom: calc(100% + 6px); left: 50%;
  transform: translateX(-50%); z-index: 30;
  min-width: 170px; max-width: 230px; text-align: left;
  padding: 8px 10px; border: 1px solid var(--line-strong); border-radius: 8px;
  background: var(--paper); color: var(--ink); box-shadow: var(--shadow-pop);
  font-size: 11px; line-height: 1.45; white-space: normal;
  opacity: 0; pointer-events: none; transition: opacity .12s ease;
}}
.office-agent:hover .tip {{ opacity: 1; }}
.office-agent .tip b {{ display:block; color: var(--ink); font-size: 12px; margin-bottom: 2px; }}
.office-agent .tip .row {{ color: var(--muted); }}
.office-agent .tip .row span {{ color: var(--ink); }}
</style>
</head>
<body>
<div class="spike-banner">
  <b>SPIKE / DEMO (not the live console).</b> Office Map populated with {total}
  <b>sample</b> agents using the new <b>v3 category sprites</b> -- a cute pixel
  character built on the <b>GrafxKid "RPG character" CC0 base</b> (OpenGameArt
  CC0, attribution not required). The 34 ORG-MODEL roles are grouped into
  <b>8 categories</b>; each is distinguished by an <b>accessory (hat/item) +
  token color</b>, not 34 distinct bodies. v3 is additive (v1/v2 preserved).
  Hover an agent for role &middot; status &middot; task.
</div>
<div class="cat-legend" aria-label="Category sprite legend">{cat_chips}</div>
<div class="spike-controls">
  <button id="themeBtn" type="button">Toggle dark / light</button>
</div>
<section class="office-map" aria-label="Office map (v3 demo)">
  <header class="office-map-header">
    <h2>Agent Runtime HQ</h2>
    <p class="office-map-summary">{total} agents &middot; 5 rooms &middot; v3 sprites &middot; sample data</p>
  </header>
  <div class="office-map-stage">
    <div class="office-map-grid">
{rooms_html}
{agents_html}
    </div>
  </div>
  <ul class="office-map-legend" aria-label="Status legend">
    {legend}
  </ul>
</section>
<script>
document.querySelectorAll('.office-agent').forEach(function (el) {{
  var role = el.getAttribute('data-role') || '';
  var cat = el.getAttribute('data-cat') || '';
  var status = el.getAttribute('data-status') || '';
  var task = el.getAttribute('data-task') || '';
  var tip = document.createElement('span');
  tip.className = 'tip';
  tip.innerHTML = '<b>' + role + '</b>' +
    '<div class="row">category: <span>' + cat + '</span></div>' +
    '<div class="row">status: <span>' + status + '</span></div>' +
    '<div class="row">task: <span>' + task + '</span></div>';
  el.appendChild(tip);
}});
document.getElementById('themeBtn').addEventListener('click', function () {{
  var h = document.documentElement;
  h.setAttribute('data-theme', h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}});
</script>
</body>
</html>
"""


def v3_inline_svg_for_cat(category_id: str, size: int = 24) -> str:
    """Render a category's representative sprite (for the legend chips)."""
    # Use any role that maps to this category, else render via the category accent.
    _disp, accent, accessory, _tok, _blurb = GEN.CATEGORY_BY_ID[category_id][1:]
    grid = GEN.compose_grid(accessory)
    pal = GEN._resolve_palette(accent)
    px = 8
    rects = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            var = pal[ch][0].split(",")[0].rstrip(") ") + ")"
            rects.append(
                f'<rect x="{c * px}" y="{r * px}" width="{px}" height="{px}" fill="{var}"/>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
        f'width="{size}" height="{size}" shape-rendering="crispEdges" aria-hidden="true">'
        + "".join(rects)
        + "</svg>"
    )


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
