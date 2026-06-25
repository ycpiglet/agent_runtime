#!/usr/bin/env python3
"""Generate office-map-demo.html (Deliverable 1) for the sprite-quality spike.

Self-contained: replicates the real Office Map (office CSS + OFFICE_ROOMS layout
+ v2 chibi sprites) populated with ~12 SAMPLE agents so the Owner can SEE what
the live map looks like FILLED. Reads the actual v2 SVGs and inlines them.

Reads NOTHING from the live console at runtime; it only copies the static CSS
rules / room rects we already extracted, so the live console is untouched.
"""
from __future__ import annotations

import html
from pathlib import Path

HERE = Path(__file__).resolve()
# .../agents/project/ui/spike/gen_office_demo.py -> repo worktree root
ROOT = HERE.parents[4]
SPRITE_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v2"
OUT = ROOT / "office-map-demo.html"

# --- Mirror of OFFICE_ROOMS (ui_state.py ~4504) + grid (12x8) ---------------
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

# Action -> glyph + label (mirror of OFFICE_ACTION_GLYPHS / _LABELS in ui_state).
ACTION_GLYPHS = {
    "working": "\U0001F4BB", "recording": "\U0001F4DD", "reviewing": "\U0001F50D",
    "meeting": "\U0001F465", "idle": "\U0001F4A4",
}
ACTION_LABELS = {
    "working": "working", "recording": "recording", "reviewing": "reviewing",
    "meeting": "in meeting", "idle": "idle",
}
# Presence -> ring class used by the office CSS.
# working/reviewing/in_meeting/online/offline

# --- 12 SAMPLE agents (realistic roles), placed in their mapped rooms --------
# (sprite = v2 filename stem; presence drives the ring; action drives glyph+word)
AGENTS = [
    # Planning Room (violet)
    {"name": "Planning Arch.", "role": "planning-architect", "sprite": "planning-architect",
     "room": "planning", "presence": "working", "action": "working",
     "task": "Sequencing TASK-AR-593 -> 596"},
    {"name": "Research", "role": "research-agent", "sprite": "research-agent",
     "room": "planning", "presence": "reviewing", "action": "reviewing",
     "task": "Scanning CC0 sprite sources"},
    {"name": "Council", "role": "council", "sprite": "council",
     "room": "planning", "presence": "online", "action": "idle",
     "task": "Awaiting escalation"},
    {"name": "Mng Partner", "role": "managing-partner", "sprite": "managing-partner",
     "room": "planning", "presence": "working", "action": "recording",
     "task": "Drafting weekly portfolio memo"},
    # Dev Room (blue)
    {"name": "Lead Eng.", "role": "lead-engineer", "sprite": "lead-engineer",
     "room": "dev", "presence": "working", "action": "working",
     "task": "Reviewing office-map data wiring"},
    {"name": "Worker Eng.", "role": "worker-engineer", "sprite": "worker-engineer",
     "room": "dev", "presence": "working", "action": "working",
     "task": "Implementing presence backfill"},
    # QA Room (amber)
    {"name": "QA", "role": "qa", "sprite": "qa",
     "room": "qa", "presence": "reviewing", "action": "reviewing",
     "task": "Running gate chain on PR #412"},
    {"name": "Auditor", "role": "independent-auditor", "sprite": "independent-auditor",
     "room": "qa", "presence": "reviewing", "action": "reviewing",
     "task": "Independent audit of release SHA"},
    # Release Room (success)
    {"name": "Release Int.", "role": "release-integrity", "sprite": "release-integrity",
     "room": "release", "presence": "working", "action": "recording",
     "task": "Stamping evidence bundle"},
    {"name": "Doc Steward", "role": "doc-steward", "sprite": "doc-steward",
     "room": "release", "presence": "online", "action": "recording",
     "task": "Updating CHANGELOG"},
    # Meeting Room (primary / fallback) -- pulled into a live meeting
    {"name": "Lead Design", "role": "lead-designer", "sprite": "lead-designer",
     "room": "meeting", "presence": "in_meeting", "action": "meeting",
     "task": "Design review: sprite quality pivot"},
    {"name": "UX Eval", "role": "ux-evaluator", "sprite": "ux-evaluator",
     "room": "meeting", "presence": "in_meeting", "action": "meeting",
     "task": "Design review: sprite quality pivot"},
]

# --- Office CSS (copied verbatim from ui_console_assets.py ~2769-2955) -------
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
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--font-size-ui-10); font-weight: 700; color: var(--ink);
  background: var(--office-avatar-bg); border: 2px solid var(--office-room-line);
  animation: office-idle-bob 3.2s ease-in-out infinite;
}
.office-agent-sprite .chibi-sprite {
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
.office-map-empty {
  grid-column: 1 / -1; grid-row: 1 / -1; display: flex;
  align-items: center; justify-content: center; color: var(--subtle);
  font-size: var(--font-size-ui-13);
}
.office-map-legend {
  display: flex; flex-wrap: wrap; gap: var(--space-3xl); margin: 0; padding: 0;
  list-style: none; font-size: var(--font-size-ui-11); color: var(--muted);
}
.office-map-legend li { display: inline-flex; align-items: center; gap: var(--space-md); }
.office-map-legend .legend-glyph { font-size: var(--font-size-ui-14); }
"""

# --- Token defaults so the demo is self-contained (light theme subset) -------
TOKENS = """
:root {
  color-scheme: light;
  --font-sans: "Geist", "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --canvas:#ffffff; --paper:#ffffff; --panel:#f7f7f5; --panel-strong:#f1f1ef;
  --ink:#37352f; --muted:#787774; --subtle:#9b9a97; --on-accent:#ffffff;
  --line:#e9e9e7; --line-strong:#d3d1cb;
  --primary:#2e6fdb; --primary-hover:#1f5bc0; --success:#0f7b55;
  --warning:#cb7509; --danger:#e03e3e; --teal:#0f7b55; --blue:#2e6fdb;
  --amber:#cb7509; --red:#e03e3e; --violet:#6a48c9; --info:#2e6fdb;
  --primary-soft: rgba(46,111,219,0.10); --violet-soft: rgba(106,72,201,0.14);
  --surface-grad: linear-gradient(180deg, var(--panel), var(--panel));
  --shadow-pop: 0 10px 30px rgba(15,15,15,0.16);
  /* office tokens */
  --office-floor: var(--surface-grad); --office-room-bg: var(--panel);
  --office-room-line: var(--line-strong); --office-avatar-bg: var(--panel-strong);
  /* chibi sprite art tokens */
  --office-skin:#f6caa6; --office-skin-shade:#e0a878; --office-hair:#5b4636;
  /* font + spacing + radius scale (subset) */
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
  --blue:#57a0ff; --amber:#d99a2b; --violet:#5e6ad2;
}
"""


def load_sprite(stem: str) -> str:
    p = SPRITE_DIR / f"{stem}.svg"
    svg = p.read_text(encoding="utf-8").strip()
    # tag it so CSS can size it as .chibi-sprite
    svg = svg.replace('class="agent-character"', 'class="agent-character chibi-sprite"', 1)
    return svg


def agent_cells():
    """Mirror build_office_map packing: near-square sub-grid per room (0..1)."""
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
    # absolute % within the whole 12x8 grid: room origin + cell offset
    left = (r["col"] + fx * r["cols"]) / OFFICE_MAP_COLS * 100
    top = (r["row"] + fy * r["rows"]) / OFFICE_MAP_ROWS * 100
    glyph = ACTION_GLYPHS[a["action"]]
    label = ACTION_LABELS[a["action"]]
    sprite = load_sprite(a["sprite"])
    role = a["role"]
    tip = f"{role} · {label} · {a['task']}"
    return (
        f'<div class="office-agent presence-{a["presence"]}" '
        f'style="left:{left:.2f}%; top:{top:.2f}%;" '
        f'title="{html.escape(tip)}" '
        f'data-role="{html.escape(role)}" data-status="{html.escape(label)}" '
        f'data-task="{html.escape(a["task"])}">'
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
    total = len(AGENTS)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Office Map Demo (populated) -- sprite quality spike</title>
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
/* richer hover tooltip (replicates a live-console-style popover for the demo) */
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
  <b>SPIKE / DEMO (not the live console).</b> This page replicates the real Office Map
  CSS + the 5-room 12&times;8 layout from <code>ui_state.py</code>, populated with
  {total} <b>sample</b> agents so you can see the map FILLED. Sprites are our current
  <b>v2 procedural chibi</b> art. The live map shows nothing today only because runtime
  has 0 active agents (a data gap, not a rendering bug). Hover an agent for role &middot;
  status &middot; task.
</div>
<div class="spike-controls">
  <button id="themeBtn" type="button">Toggle dark / light</button>
</div>
<section class="office-map" aria-label="Office map (demo)">
  <header class="office-map-header">
    <h2>Agent Runtime HQ</h2>
    <p class="office-map-summary">{total} agents &middot; 5 rooms &middot; sample data</p>
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
// Enrich each agent with a styled hover tooltip from its data-* attrs.
document.querySelectorAll('.office-agent').forEach(function (el) {{
  var role = el.getAttribute('data-role') || '';
  var status = el.getAttribute('data-status') || '';
  var task = el.getAttribute('data-task') || '';
  var tip = document.createElement('span');
  tip.className = 'tip';
  tip.innerHTML = '<b>' + role + '</b>' +
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


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
