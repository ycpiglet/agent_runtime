#!/usr/bin/env python3
"""Generate org-chart-demo.html for the console Org Chart view.

Self-contained, standalone preview of the new Org Chart view: the REAL
ORG-MODEL.yml org rendered TOP-DOWN as managing-partner (director) -> the 11
teams -> each team's roles (planner/lead -> reviewer -> worker). Each role node
shows the v3 CATEGORY sprite (GrafxKid "RPG character" CC0 base; provenance in
v3/base/SOURCES.md), a tier badge (glyph + word, not color alone) and a team
color token. Clicking a team/role node highlights it (the live console drills
the Board to that team/role via the shared AR-337 wiring).

Reads NOTHING from the live console at runtime: the hierarchy comes from
``ui_state.build_org_chart`` over the real ORG-MODEL, and sprites are rendered
with INLINE fills from the deterministic v3 generator so the standalone page is
collision-free and matches the served patternV3Sprite cell-for-cell.
"""
from __future__ import annotations

import html
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
# .../agents/project/ui/spike/gen_org_chart_demo.py -> repo worktree root
ROOT = HERE.parents[4]
V3_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v3"
OUT = HERE.parent / "org-chart-demo.html"

# Import the live data builder + the deterministic v3 sprite generator.
sys.path.insert(0, str(ROOT / "src"))
from agent_runtime import ui_state  # noqa: E402


def _load_v3():
    spec = importlib.util.spec_from_file_location("v3_gen", V3_DIR / "generate_sprites.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_v3()

# team id -> color token (mirror of ui_state team/category tokens for teams).
TEAM_TOKEN = {
    "org": "violet",
    "engineering": "primary",
    "ui-ux": "teal",
    "research": "amber",
    "quality": "danger",
    "risk-release": "danger",
    "finance-accounting": "warning",
    "marketing-growth": "success",
    "sales-revenue": "success",
    "operations-support": "warning",
    "planning-strategy": "violet",
}


def v3_inline_svg(role: str, size: int = 36) -> str:
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
  --muted-strong:#5f5e5b;
  --primary-soft:#dde8f9; --teal-soft:#d2efeb; --danger-soft:#fbdada;
  --violet-soft:#e3dbf6; --warning-soft:#f7e4c8; --success-soft:#cfeadd;
  --amber-soft:#f7e4c8; --muted-soft:#ededeb;
  --raise-strong:#e6e6e3;
  --office-skin:#f6caa6; --office-skin-shade:#e0a878; --office-hair:#5b4636;
}
[data-theme="dark"] {
  color-scheme: dark;
  --canvas:#010102; --paper:#010102; --panel:#0f1011; --panel-strong:#15171a;
  --ink:#f7f8f8; --muted:#a2a8b3; --subtle:#62666d; --on-accent:#ffffff;
  --line:#23252a; --line-strong:#343844; --muted-strong:#c9ced6;
  --primary:#5e6ad2; --primary-hover:#7984e6; --success:#27a644;
  --warning:#d99a2b; --danger:#f04438;
  --blue:#57a0ff; --amber:#d99a2b; --violet:#5e6ad2; --teal:#2dd4bf;
  --primary-soft:#1c2740; --teal-soft:#0e3b37; --danger-soft:#3a1717;
  --violet-soft:#211c40; --warning-soft:#3a2c12; --success-soft:#10311f;
  --amber-soft:#3a2c12; --muted-soft:#1a1c1f;
  --raise-strong:#23252a;
  --office-skin:#f6caa6; --office-skin-shade:#cf9a64; --office-hair:#6b5240;
}
"""


def role_card(node: dict) -> str:
    role = node["id"]
    badge = node.get("tier_badge", {})
    glyph = badge.get("glyph", "-")
    tier = badge.get("label", node.get("tier", "role"))
    token = node.get("color_token", "muted")
    cat = GEN.category_for_role(role)
    sprite = v3_inline_svg(role, 36)
    tip = f"{role} | {tier} | category {cat} | team {node.get('team', '')}"
    return (
        f'<div class="role-card token-{token}" tabindex="0" role="button" '
        f'aria-label="{html.escape(tip)}" title="{html.escape(tip)}" '
        f'data-role="{html.escape(role)}" data-team="{html.escape(node.get("team", ""))}">'
        f'<span class="role-sprite">{sprite}</span>'
        f'<span class="role-text">'
        f'<b class="role-name">{html.escape(node.get("display_name", role))}</b>'
        f'<span class="role-tier"><span class="tier-glyph" aria-hidden="true">{html.escape(glyph)}</span> {html.escape(tier)}</span>'
        f'</span>'
        f'</div>'
    )


def team_column(team: dict) -> str:
    token = TEAM_TOKEN.get(team["id"], team.get("color_token", "violet"))
    roles = "".join(role_card(r) for r in team.get("children", []))
    if not roles:
        roles = '<div class="team-empty">org-wide (director)</div>'
    return (
        f'<div class="team-col token-{token}" data-team="{html.escape(team["id"])}" '
        f'tabindex="0" role="button" aria-label="Team {html.escape(team.get("display_name", team["id"]))}">'
        f'<div class="team-head"><span class="team-bar token-{token}"></span>'
        f'<b>{html.escape(team.get("display_name", team["id"]))}</b>'
        f'<span class="team-count">{team.get("role_count", 0)} roles</span></div>'
        f'<div class="team-roles">{roles}</div>'
        f'</div>'
    )


def build() -> str:
    chart = ui_state.build_org_chart(ROOT)
    root = chart["root"]
    teams = root["children"]
    totals = chart["totals"]
    director_sprite = v3_inline_svg(root["id"], 48)
    teams_html = "\n".join(team_column(t) for t in teams)
    # Category legend chips (8 v3 categories).
    cat_chips = "".join(
        f'<span class="chip">{v3_inline_svg(_first_role_for_cat(cid), 24)}'
        f'{html.escape(disp)} ({tok})</span>'
        for cid, disp, _acc, _accs, tok, _b in GEN.CATEGORIES
    )
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Org Chart Demo -- agent org (ORG-MODEL + v3 sprites)</title>
<style>
{TOKENS}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; padding: 24px; background: var(--canvas); color: var(--ink);
  font-family: var(--font-sans);
}}
.spike-banner {{
  max-width: 1180px; margin: 0 auto 16px; padding: 12px 16px;
  border: 1px solid var(--line-strong); border-left: 3px solid var(--primary);
  border-radius: 8px; background: var(--panel); font-size: 13px; color: var(--muted);
}}
.spike-banner b {{ color: var(--ink); }}
.spike-controls {{ max-width: 1180px; margin: 0 auto 14px; display:flex; gap:10px; }}
.spike-controls button {{
  font: inherit; font-size: 12px; padding: 6px 12px; cursor: pointer;
  border: 1px solid var(--line-strong); border-radius: 8px;
  background: var(--panel); color: var(--ink);
}}
.cat-legend {{ display:flex; flex-wrap:wrap; gap:12px; max-width:1180px; margin:0 auto 16px; }}
.cat-legend .chip {{ display:inline-flex; align-items:center; gap:6px;
  font-size:11px; color:var(--muted); border:1px solid var(--line-strong);
  border-radius:8px; padding:4px 8px; background:var(--panel); }}
.cat-legend .chip svg {{ width:24px; height:24px; image-rendering:pixelated; }}
.org-wrap {{ max-width: 1180px; margin: 0 auto; }}
.org-director {{
  display:flex; align-items:center; gap:12px; justify-content:center;
  margin: 0 auto 8px; padding: 12px 18px; width: max-content;
  border: 1px solid var(--violet); border-radius: 12px;
  background: var(--violet-soft); box-shadow: 0 6px 20px rgba(15,15,15,0.10);
}}
.org-director .v3-sprite {{ width:48px; height:48px; image-rendering:pixelated; }}
.org-director b {{ font-size: 16px; }}
.org-director small {{ display:block; color: var(--muted); font-size: 11px; }}
.org-trunk {{ height: 18px; width: 2px; background: var(--line-strong); margin: 0 auto; }}
.org-teams {{
  display:flex; flex-wrap:wrap; gap:14px; align-items:flex-start;
  justify-content:center;
}}
.team-col {{
  flex: 1 1 250px; min-width: 230px; max-width: 290px;
  border: 1px solid var(--line-strong); border-radius: 12px;
  background: var(--panel); padding: 10px; cursor: pointer;
}}
.team-col:focus-visible, .role-card:focus-visible {{
  outline: 2px solid var(--primary-hover); outline-offset: 2px;
}}
.team-head {{ display:flex; align-items:center; gap:8px; margin-bottom: 8px;
  font-size: 13px; }}
.team-head .team-count {{ margin-left:auto; color: var(--muted); font-size: 11px; }}
.team-bar {{ width: 10px; height: 16px; border-radius: 3px; background: var(--muted); }}
.team-roles {{ display:flex; flex-direction:column; gap:6px; }}
.team-empty {{ color: var(--subtle); font-size: 11px; padding: 6px; }}
.role-card {{
  display:flex; align-items:center; gap:10px; padding: 6px 8px;
  border: 1px solid var(--line); border-left: 3px solid var(--muted);
  border-radius: 8px; background: var(--paper); cursor: pointer;
}}
.role-card:hover {{ border-color: var(--line-strong); }}
.role-card .v3-sprite {{ width:36px; height:36px; image-rendering:pixelated; flex:0 0 auto; }}
.role-text {{ display:flex; flex-direction:column; min-width:0; }}
.role-name {{ font-size: 12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.role-tier {{ font-size: 10px; color: var(--muted); }}
.role-tier .tier-glyph {{ font-weight:700; color: var(--ink); }}
/* team color tokens (left bar + role-card accent) */
.token-primary .team-bar, .role-card.token-primary {{ border-left-color: var(--primary); background: var(--paper); }}
.token-primary .team-bar {{ background: var(--primary); }}
.token-teal .team-bar {{ background: var(--teal); }} .role-card.token-teal {{ border-left-color: var(--teal); }}
.token-danger .team-bar {{ background: var(--danger); }} .role-card.token-danger {{ border-left-color: var(--danger); }}
.token-amber .team-bar {{ background: var(--amber); }} .role-card.token-amber {{ border-left-color: var(--amber); }}
.token-violet .team-bar {{ background: var(--violet); }} .role-card.token-violet {{ border-left-color: var(--violet); }}
.token-warning .team-bar {{ background: var(--warning); }} .role-card.token-warning {{ border-left-color: var(--warning); }}
.token-success .team-bar {{ background: var(--success); }} .role-card.token-success {{ border-left-color: var(--success); }}
.token-muted .team-bar {{ background: var(--muted); }} .role-card.token-muted {{ border-left-color: var(--muted); }}
.is-selected {{ box-shadow: 0 0 0 2px var(--primary-hover) inset; }}
.drill-note {{ max-width:1180px; margin: 14px auto 0; font-size: 12px; color: var(--muted); }}
.drill-note span {{ color: var(--ink); }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
</head>
<body>
<div class="spike-banner">
  <b>SPIKE / DEMO (not the live console).</b> The agent organization rendered
  TOP-DOWN from the real <b>ORG-MODEL.yml</b>: <b>{html.escape(root["display_name"])}</b>
  (director) -&gt; <b>{totals["teams"]} teams</b> -&gt; <b>{totals["roles"]} roles</b>
  (ordered lead -&gt; reviewer -&gt; worker). Each role shows the <b>v3 category
  sprite</b> + a <b>tier badge</b> (glyph + word) + its team color token. In the
  live console, clicking a team/role node drills the Board to that team/role.
</div>
<div class="cat-legend" aria-label="Category sprite legend">{cat_chips}</div>
<div class="spike-controls">
  <button id="themeBtn" type="button">Toggle dark / light</button>
</div>
<section class="org-wrap" aria-label="Agent organization chart">
  <div class="org-director" role="img" aria-label="{html.escape(root["display_name"])} - Director">
    <span>{director_sprite}</span>
    <span><b>{html.escape(root["display_name"])}</b><small>* Director - org-wide</small></span>
  </div>
  <div class="org-trunk" aria-hidden="true"></div>
  <div class="org-teams">
{teams_html}
  </div>
</section>
<p class="drill-note" id="drillNote">Click a team or role to preview the drill-down: <span>nothing selected</span></p>
<script>
function selectNode(el, label) {{
  document.querySelectorAll('.is-selected').forEach(function (n) {{ n.classList.remove('is-selected'); }});
  el.classList.add('is-selected');
  var note = document.getElementById('drillNote').querySelector('span');
  note.textContent = label;
}}
document.querySelectorAll('.role-card').forEach(function (el) {{
  var role = el.getAttribute('data-role'); var team = el.getAttribute('data-team');
  var act = function (ev) {{ ev.stopPropagation(); selectNode(el, 'Board filter -> team ' + team + ' / role ' + role); }};
  el.addEventListener('click', act);
  el.addEventListener('keydown', function (ev) {{ if (ev.key === 'Enter' || ev.key === ' ') {{ ev.preventDefault(); act(ev); }} }});
}});
document.querySelectorAll('.team-col').forEach(function (el) {{
  var team = el.getAttribute('data-team');
  el.addEventListener('click', function () {{ selectNode(el, 'Board filter -> team ' + team); }});
  el.addEventListener('keydown', function (ev) {{ if (ev.key === 'Enter' || ev.key === ' ') {{ ev.preventDefault(); selectNode(el, 'Board filter -> team ' + team); }} }});
}});
document.getElementById('themeBtn').addEventListener('click', function () {{
  var h = document.documentElement;
  h.setAttribute('data-theme', h.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}});
</script>
</body>
</html>
"""


def _first_role_for_cat(category_id: str) -> str:
    for role, cat in GEN.ROLE_CATEGORY.items():
        if cat == category_id:
            return role
    return "lead-engineer"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
