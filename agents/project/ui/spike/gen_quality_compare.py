#!/usr/bin/env python3
"""Generate quality-compare.html (Deliverable 2) for the sprite-quality spike.

Side-by-side: OUR v2 procedural chibi sprite (left) vs a REAL CC0 artist-drawn
pixel character (right), each at small + 3x zoom (image-rendering: pixelated) so
the legibility / charm difference is obvious. Fully self-contained: v2 SVGs are
inlined; the CC0 PNGs are embedded as base64 data URIs. Source links + licenses
are embedded from SOURCES.md (all CC0, attribution not required).
"""
from __future__ import annotations

import base64
import html
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
SPRITE_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "v2"
CC0_DIR = ROOT / "agents" / "project" / "assets" / "agent-characters" / "_compare-cc0"
OUT = ROOT / "quality-compare.html"

# CC0 assets: cropped single-character frame + full sheet + provenance.
CC0 = [
    {"frame": "char1_8bit-rpg-set_frame.png", "sheet": "char1_8bit-rpg-set.png",
     "title": "8-bit RPG knight", "author": "devurandom",
     "page": "https://opengameart.org/content/16x16-8-bit-rpg-character-set",
     "license": "CC0", "dim": "16x16 (cropped from 256x128 sheet)"},
    {"frame": "char2_simple-base_frame.png", "sheet": "char2_simple-base.png",
     "title": "Simple character base", "author": "zaphgames",
     "page": "https://opengameart.org/content/simple-character-base-16x16",
     "license": "CC0", "dim": "16x16 (cropped from 64x64 sheet)"},
    {"frame": "char3_classic-hero_frame.png", "sheet": "char3_classic-hero.png",
     "title": "Classic hero (Mr. Man)", "author": "GrafxKid",
     "page": "https://opengameart.org/content/classic-hero",
     "license": "CC0", "dim": "16x16 (cropped from 128x112 sheet)"},
    {"frame": "char4_rpg-assets_frame.png", "sheet": "char4_rpg-assets.png",
     "title": "RPG character", "author": "GrafxKid",
     "page": "https://opengameart.org/content/rpg-character-sprites",
     "license": "CC0", "dim": "16x16 (cropped from 128x128 sheet)"},
]

# Pairings: our v2 role sprite <-> a CC0 character (thematic, not 1:1 art match).
PAIRS = [
    {"v2": "lead-engineer", "v2_label": "v2: Lead Engineer", "cc0": 0},
    {"v2": "qa", "v2_label": "v2: QA", "cc0": 2},
    {"v2": "research-agent", "v2_label": "v2: Research Agent", "cc0": 3},
    {"v2": "lead-designer", "v2_label": "v2: Lead Designer", "cc0": 1},
]

TOKENS = """
:root {
  color-scheme: light;
  --font-sans: "Geist","IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  --canvas:#ffffff; --panel:#f7f7f5; --panel-strong:#f1f1ef; --paper:#fff;
  --ink:#37352f; --muted:#787774; --subtle:#9b9a97;
  --line:#e9e9e7; --line-strong:#d3d1cb;
  --primary:#2e6fdb; --success:#0f7b55; --danger:#e03e3e; --violet:#6a48c9;
  --warning:#cb7509; --amber:#cb7509; --blue:#2e6fdb;
  --primary-soft: rgba(46,111,219,0.10); --violet-soft: rgba(106,72,201,0.14);
  --office-skin:#f6caa6; --office-skin-shade:#e0a878; --office-hair:#5b4636;
}
"""


def b64_png(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def load_sprite(stem: str) -> str:
    return (SPRITE_DIR / f"{stem}.svg").read_text(encoding="utf-8").strip()


def cell_ours(stem: str, label: str) -> str:
    svg = load_sprite(stem)
    return f"""
    <div class="col">
      <div class="col-head">OURS &mdash; v2 procedural (SVG, code-drawn rects)</div>
      <div class="sizes">
        <figure><div class="box small ours">{svg}</div><figcaption>~26px (map size)</figcaption></figure>
        <figure><div class="box big ours">{svg}</div><figcaption>3&times; zoom</figcaption></figure>
      </div>
      <div class="cap">{html.escape(label)}</div>
    </div>"""


def cell_cc0(idx: int) -> str:
    a = CC0[idx]
    frame_uri = "data:image/png;base64," + b64_png(CC0_DIR / a["frame"])
    sheet_uri = "data:image/png;base64," + b64_png(CC0_DIR / a["sheet"])
    return f"""
    <div class="col">
      <div class="col-head">REAL CC0 &mdash; artist-drawn pixel art (PNG)</div>
      <div class="sizes">
        <figure><div class="box small"><img class="px" src="{frame_uri}" alt="{html.escape(a['title'])}"></div><figcaption>~26px (map size)</figcaption></figure>
        <figure><div class="box big"><img class="px" src="{frame_uri}" alt="{html.escape(a['title'])}"></div><figcaption>3&times; zoom</figcaption></figure>
      </div>
      <div class="cap">{html.escape(a['title'])}
        <span class="lic">{a['license']} &middot; {html.escape(a['author'])}</span>
      </div>
      <details class="sheet">
        <summary>full source sheet ({a['dim']})</summary>
        <img class="px sheetimg" src="{sheet_uri}" alt="{html.escape(a['title'])} sheet">
        <a href="{a['page']}" target="_blank" rel="noopener">source page &middot; {a['license']}</a>
      </details>
    </div>"""


def pair_row(p: dict) -> str:
    return f"""
  <div class="pair">
    {cell_ours(p['v2'], p['v2_label'])}
    <div class="vs">vs</div>
    {cell_cc0(p['cc0'])}
  </div>"""


def sources_block() -> str:
    rows = "".join(
        f"<li><a href='{a['page']}' target='_blank' rel='noopener'>{html.escape(a['title'])}</a> "
        f"&mdash; <b>{a['license']}</b> by {html.escape(a['author'])} "
        f"&middot; attribution <b>not required</b> &middot; {a['dim']}</li>"
        for a in CC0
    )
    return f"<ul class='sources'>{rows}</ul>"


def build() -> str:
    pairs = "\n".join(pair_row(p) for p in PAIRS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprite quality: v2 procedural vs real CC0 pixel art</title>
<style>
{TOKENS}
* {{ box-sizing: border-box; }}
body {{ margin:0; padding:24px; background:var(--canvas); color:var(--ink);
  font-family:var(--font-sans); }}
.wrap {{ max-width: 1040px; margin: 0 auto; }}
h1 {{ font-size: 22px; margin: 0 0 6px; }}
.sub {{ color: var(--muted); font-size: 13px; margin: 0 0 4px; }}
.note {{ border:1px solid var(--line-strong); border-left:3px solid var(--success);
  border-radius:8px; background:var(--panel); padding:10px 14px; font-size:12.5px;
  color:var(--muted); margin: 14px 0 22px; }}
.note b {{ color: var(--ink); }}
.pair {{ display:grid; grid-template-columns: 1fr auto 1fr; align-items:start;
  gap: 14px; padding: 16px; border:1px solid var(--line-strong);
  border-radius:12px; background:var(--paper); margin-bottom:16px; }}
.col-head {{ font-size:11px; font-weight:700; letter-spacing:.02em;
  text-transform:uppercase; color:var(--muted); margin-bottom:10px; }}
.sizes {{ display:flex; align-items:flex-end; gap:18px; }}
figure {{ margin:0; text-align:center; }}
figcaption {{ font-size:10px; color:var(--subtle); margin-top:4px; }}
.box {{ display:flex; align-items:center; justify-content:center;
  background:
    linear-gradient(45deg,#eee 25%,transparent 25%,transparent 75%,#eee 75%) 0 0/16px 16px,
    linear-gradient(45deg,#eee 25%,#fff 25%,#fff 75%,#eee 75%) 8px 8px/16px 16px;
  border:1px solid var(--line); border-radius:8px; }}
.box.small {{ width:40px; height:40px; }}
.box.big {{ width:96px; height:96px; }}
.box.small .agent-character {{ width:26px; height:26px; }}
.box.big .agent-character {{ width:78px; height:78px; image-rendering:pixelated; }}
.px {{ image-rendering: pixelated; image-rendering: crisp-edges; }}
.box.small .px {{ width:26px; height:26px; }}
.box.big .px {{ width:78px; height:78px; }}
.vs {{ align-self:center; font-size:12px; font-weight:700; color:var(--subtle);
  padding-top:30px; }}
.cap {{ font-size:12px; font-weight:600; color:var(--ink); margin-top:10px; }}
.cap .lic {{ display:block; font-weight:400; font-size:10.5px; color:var(--subtle);
  margin-top:2px; }}
details.sheet {{ margin-top:8px; font-size:11px; color:var(--muted); }}
details.sheet summary {{ cursor:pointer; }}
.sheetimg {{ display:block; margin:8px 0 4px; width:auto; max-width:100%;
  transform-origin:left top; image-rendering:pixelated; border:1px solid var(--line);
  background:#cfcfcf; }}
details.sheet a {{ color:var(--primary); }}
.sources {{ font-size:12px; color:var(--muted); line-height:1.7; }}
.sources a {{ color:var(--primary); }}
.assess {{ border:1px solid var(--line-strong); border-radius:12px;
  background:var(--panel); padding:16px 18px; margin-top:8px; font-size:13px;
  line-height:1.6; }}
.assess h2 {{ font-size:15px; margin:0 0 8px; }}
.assess h3 {{ font-size:13px; margin:14px 0 4px; }}
.assess ul {{ margin:4px 0; padding-left:20px; }}
.verdict {{ border-left:3px solid var(--primary); background:var(--primary-soft);
  padding:10px 14px; border-radius:8px; margin-top:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Sprite quality: v2 procedural vs real CC0 pixel art</h1>
  <p class="sub">Left = our current v2 chibi (code-drawn rects, SVG). Right = a real,
  artist-drawn CC0 pixel character (PNG). Each shown at map size (~26px) and at 3&times; zoom.</p>
  <div class="note">
    <b>Real CC0 binaries were fetched successfully</b> (4 PNG sheets from OpenGameArt.org,
    all verified CC0 &mdash; attribution not required). A single front-facing frame was
    cropped from each sheet for a fair character-vs-character view; expand
    &ldquo;full source sheet&rdquo; under any CC0 sample to see the untouched download.
  </div>

{pairs}

  <div class="assess">
    <h2>Quality assessment (summary &mdash; full notes in QUALITY-NOTES.md)</h2>
    <p>At the actual on-map size (~26px) the v2 procedural chibi reads as a warm blob:
    skin + hair fill is visible (the v1 &ldquo;empty&rdquo; complaint is fixed) but the
    role-defining details (tools, badges, garments) collapse into noise because they are
    axis-aligned 8px rectangles with no sub-pixel shaping, outline hierarchy, or shading.
    The CC0 art stays legible at the same size: a clear dark outline, a readable silhouette,
    and 2&ndash;3 shading steps give it a defined head/body/limbs and an instantly readable
    pose.</p>
    <h3>Where v2 loses</h3>
    <ul>
      <li><b>Silhouette:</b> CC0 has a crisp outline + distinct head/torso/legs; v2 is a soft rounded mass.</li>
      <li><b>Shading:</b> CC0 uses light/mid/dark ramps; v2 is mostly flat fills.</li>
      <li><b>Role readability:</b> v2 role cues (the whole point) blur at 26px; artist art encodes role in shape, not just color.</li>
      <li><b>Charm:</b> hand-drawn proportions and tiny facial detail read as &ldquo;a character&rdquo;; the procedural grid reads as &ldquo;an icon.&rdquo;</li>
    </ul>
    <h3>Where v2 still wins</h3>
    <ul>
      <li><b>Theming:</b> v2 fills are CSS vars, so it auto-recolors for dark mode and per-room accents; raw PNGs are fixed-palette.</li>
      <li><b>Coverage:</b> we already have all 34 roles; a CC0 pack rarely ships 34 distinct, role-mapped characters.</li>
      <li><b>Crispness:</b> SVG is resolution-independent; PNGs need pixelated upscaling.</li>
    </ul>
    <div class="verdict">
      <b>Recommendation: pivot to real CC0 art for the character body</b>, keep our
      theming/animation layer. Adopt one cohesive CC0 base (e.g. LPC or a CC0 16x16 base)
      as the silhouette + shading, layer role accessories, and drive recolor/idle-bob with
      the existing CSS. This buys artist-grade legibility while preserving auto-theming and
      full 34-role coverage. See QUALITY-NOTES.md for the mapping + animation plan.
    </div>
  </div>

  <h3 style="margin-top:22px; font-size:14px;">CC0 sources (all attribution-not-required)</h3>
  {sources_block()}
  <p class="sub">Full provenance: <code>agents/project/assets/agent-characters/_compare-cc0/SOURCES.md</code></p>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
