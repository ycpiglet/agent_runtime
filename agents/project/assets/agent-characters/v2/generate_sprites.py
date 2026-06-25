#!/usr/bin/env python3
"""Deterministic cute chibi pixel-art agent-character sprite generator (v2).

v2 evolves the v1 draft (``../v1/generate_sprites.py``) for the LIVE Office Map
integration. Owner feedback on v1: keep the dot/pixel **chibi** style but use
**MORE COLOR** and **FILL the empty center** (v1's head/torso read as a pale,
sparse blob). v2 fixes that:

- **Filled, warm face** -- a dedicated skin tone (``H``) fills the whole head
  instead of the near-white panel tint, so the center is never empty.
- **Hair cap** (``J``) crowns every head with a saturated block of color.
- **Bigger, fully-coloured torso** -- the accent body now spans more rows and
  carries a center clothing detail (collar + buttons in ``W``/accent-soft) so
  the chest is a filled, readable color block, not a hollow outline.
- **Cheeks + mouth + eye-shine** keep the cute "아기자기" read.
- **One-sided shading** column gives gentle volume without extra palette.

Design contract (unchanged from v1, the AR-587 ``patternAgentAvatar`` line):
- ORIGINAL pixel art authored here from a small primitive grid. No third-party
  IP; Game-Boy / early-Pokemon-era chibi are *style references only*. License
  is therefore trivial (original work, repo license).
- Token-driven: every fill is a house CSS custom property (DESIGN-SYSTEM.md /
  ``ui_console_assets.py`` ``:root``). Role accent maps to the same semantic
  token as ``_AVATAR_ROLE_ACCENT`` in ``ui_design_assets.py``. A ``var(--x,
  #hex)`` fallback keeps every SVG viewable standalone (GitHub) AND token-driven
  when inlined into the console DOM.
- Deterministic + zero runtime deps: pure pixel grid -> ``<rect>`` elements.
  Same role -> byte-identical SVG. No network, no canvas, offline.
- Accessible: role is encoded by silhouette + prop + accent, never hue alone
  (AR-588 non-color-only rule). ``<title>`` for screen readers.

The on-disk SVGs in this directory are the design artifact / catalog. The LIVE
Office Map renders the SAME chibi via a JS twin (``patternChibiSprite`` in
``ui_design_assets.py``) so the served bundle stays self-contained and the JS
output matches these grids cell-for-cell (verified by tests).

Run: ``python generate_sprites.py`` -> writes one ``<role>.svg`` per role into
this directory.
"""
from __future__ import annotations

import os

# --- Pixel scale -----------------------------------------------------------
GRID = 16
PX = 8  # 16 * 8 = 128px sprite

# --- Palette: logical key -> (CSS var, GitHub fallback hex) -----------------
# Fallback hex are the LIGHT-theme token values from ui_console_assets.py :root
# so the same SVG renders with or without the console CSS variables.
PALETTE = {
    ".": ("transparent", "transparent"),               # empty
    "K": ("var(--ink)", "#37352f"),                    # outline / dark ink
    "H": ("var(--office-skin)", "#f6caa6"),            # SKIN (fills the face!)
    "h": ("var(--office-skin-shade)", "#e0a878"),      # skin shade
    "J": ("var(--office-hair)", "#5b4636"),            # HAIR cap (saturated)
    "W": ("var(--paper)", "#ffffff"),                  # eye-white / highlight
    "F": ("var(--ink)", "#37352f"),                    # eyes / features
    "B": ("var(--danger)", "#e03e3e"),                 # cheeks / mouth (warm)
    # ACCENT substituted per-role (see ROLE_ACCENT). Two tints:
    "A": ("__ACCENT__", "__ACCENT_HEX__"),             # role accent (solid)
    "a": ("__ACCENT_SOFT__", "__ACCENT_SOFT_HEX__"),   # role accent (soft)
    # prop neutrals
    "M": ("var(--warning)", "#cb7509"),                # metal / wood / gold
    "G": ("var(--success)", "#0f7b55"),                # green prop / check
    "R": ("var(--danger)", "#e03e3e"),                 # red prop / alert
}

# Role accent token + GitHub fallback hex (light theme), aligned with
# _AVATAR_ROLE_ACCENT in ui_design_assets.py.
ACCENTS = {
    "primary": ("var(--primary)", "#2e6fdb", "var(--primary-soft)", "#dde8f9"),
    "violet": ("var(--violet)", "#6a48c9", "var(--violet-soft)", "#e6def5"),
    "teal": ("var(--teal)", "#0f7b55", "var(--teal-soft)", "#d6ece4"),
    "success": ("var(--success)", "#0f7b55", "var(--success-soft)", "#d6ece4"),
    "danger": ("var(--danger)", "#e03e3e", "var(--danger-soft)", "#f8dcdc"),
    "warning": ("var(--warning)", "#cb7509", "var(--warning-soft)", "#f4e3cc"),
    "amber": ("var(--amber)", "#cb7509", "var(--warning-soft)", "#f4e3cc"),
    "muted": ("var(--muted)", "#787774", "var(--raise-strong)", "#ededeb"),
}

# ---------------------------------------------------------------------------
# Shared chibi base: a FILLED head (hair + skin + face) over a FILLED torso.
# The grid reads top (row 0) -> bottom. Capital art keys win over lowercase
# neutrals when a prop is overlaid. Compared to v1 the whole head interior is
# skin (H) not pale panel, the crown is hair (J), and the torso is a solid
# accent block with a center collar/buttons so nothing reads as empty.
# ---------------------------------------------------------------------------
BASE = [
    "................",
    ".....KKKKKK.....",   # head outline top
    "....KJJJJJJK....",   # hair cap
    "...KJJJJJJJJK...",   # hair
    "...KJHHHHHHJK...",   # hair sides + skin forehead
    "...KHHHHHHHHK...",   # skin
    "...KHFHHHHFHK...",   # eyes
    "...KHFWHHWFHK...",   # eyes + shine
    "...KHBHHHHBHK...",   # cheeks (blush)
    "...KHHHBBHHHK...",   # mouth
    "...KhHHHHHHhK...",   # chin + skin shade sides
    "....KHHHHHHK....",   # jaw
    "....KaAAAAaK....",   # collar (accent soft) over shoulders
    "...KAAWAAWAAK...",   # torso w/ button highlights (filled center!)
    "...KAAAAAAAAK...",   # torso (solid accent)
    "....KK....KK....",   # legs
]


def _overlay(base, patch):
    """Return base grid with non-'.' cells of patch overlaid on top."""
    out = [list(row) for row in base]
    for r, row in enumerate(patch):
        for c, ch in enumerate(row):
            if ch != ".":
                out[r][c] = ch
    return ["".join(row) for row in out]


# ---------------------------------------------------------------------------
# Per-role prop / headgear overlays. Each conveys the role via a small readable
# accessory placed in the empty side gutters (cols 0-2 / 11-15) and the crown
# rows, so it never blots out the now-filled face/torso. Empty cells ('.')
# leave the base showing through.
# ---------------------------------------------------------------------------

# Hard-hat (engineering lead) + wrench
HARDHAT = [
    "................",
    ".....MMMMMM.....",
    "....MMMMMMMM....",
    "...M........M...",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".............MM.",
    ".............MM.",
    "............MM..",
    "................",
    "................",
]

# Plain helmet + bolt (worker engineer)
WORKER = [
    "................",
    ".....MMMMMM.....",
    "....MMMMMMMM....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".............M..",
    "............MMM.",
    ".............M..",
    "................",
    "................",
]

# Director: crown + gavel (managing-partner)
CROWN = [
    "....M.M.M.M.....",
    "....MMMMMMM.....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".............KK.",
    ".............MM.",
    "............MM..",
    "................",
    "................",
]

# Designer: beret + paintbrush (lead-designer / interface-designer)
BERET = [
    "................",
    "....aaaaaA.....",
    "...aaaaaaaa....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".............MK.",
    ".............MK.",
    "............RR..",
    "................",
    "................",
]

# Design-system steward: ruler/grid
RULER = [
    "................",
    "....aaaaaa.....",
    "...aaaaaaaa....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............MMMM",
    "............M.M.",
    "................",
    "................",
    "................",
    "................",
]

# UX evaluator: magnifier
MAGNIFIER = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............KKK.",
    "...........KaaK.",
    "...........KaaK.",
    "............KKK.",
    ".............KK.",
    "................",
    "................",
]

# QA: clipboard + green check
QA = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............KKKK",
    "............KGGK",
    "............KGGK",
    "............KKKK",
    "................",
    "................",
    "................",
    "................",
]

# Independent auditor: monocle + red clipboard
MONOCLE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "...........KK...",
    "...........KK...",
    "............KKKK",
    "............KRRK",
    "............KRRK",
    "............KKKK",
    "................",
    "................",
    "................",
]

# Risk-controller: shield
SHIELD = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............RRR.",
    "............RRR.",
    "............RRR.",
    ".............R..",
    "................",
    "................",
    "................",
    "................",
]

# Release-integrity (CI/CD): rocket
ROCKET = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............G...",
    "...........GGG..",
    "...........GGG..",
    "...........G.G..",
    "...........M.M..",
    "................",
    "................",
    "................",
    "................",
]

# Doc-steward: book + quill
BOOK = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............KKKK",
    "............KWWK",
    "............KWWK",
    "............KKKK",
    ".............K..",
    "................",
    "................",
    "................",
]

# Research-agent: binoculars + flag
BINOCULARS = [
    "................",
    "................",
    "................",
    "................",
    "...KK....KK.....",
    "...KaK..KaK.....",
    "...KK....KK.....",
    "................",
    "................",
    "................",
    "............MM..",
    "............M.A.",
    "............MAA.",
    "............M...",
    "................",
    "................",
]

# Finance / accounting / asset / revenue: coin + ledger
COIN = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............MM..",
    "...........MaaM.",
    "...........MaAM.",
    "............MM..",
    "................",
    "................",
    "................",
    "................",
]

# Marketing / content / growth / brand: megaphone
MEGAPHONE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............A...",
    "...........AKK..",
    "..........AaaKK.",
    "..........AaaKK.",
    "...........AKK..",
    "............A...",
    "................",
    "................",
]

# Sales / crm / partnership / sales-ops: deal tag
TAG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............GG..",
    "...........GAAG.",
    "...........GAAG.",
    "............GG..",
    ".............G..",
    "................",
    "................",
    "................",
]

# Operations / support / success / process: headset
HEADSET = [
    "................",
    "....aKKKKKKa....",
    "...aK......Ka...",
    "...K........K...",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............KK..",
    "............KaK.",
    "................",
    "................",
    "................",
    "................",
]

# Strategy / planning / business-analyst / portfolio: compass
COMPASS = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............KKKK",
    "............KaAK",
    "............KAaK",
    "............KKKK",
    "................",
    "................",
    "................",
    "................",
]

# Council: crown + group dots
COUNCIL = [
    "....M.M.M.M.....",
    "....MMMMMMM.....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "............A.A.",
    "...........A.A.A",
    "............A.A.",
    "................",
    "................",
    "................",
    "................",
]


# ---------------------------------------------------------------------------
# Role registry: id -> (display, accent key, prop overlay, prop description).
# Accent keys align with _AVATAR_ROLE_ACCENT. Props chosen for a CLEAR,
# readable role cue (silhouette + accessory), per the Owner's direction.
# ---------------------------------------------------------------------------
ROLES = [
    ("managing-partner",        "Managing Partner",       "violet",  CROWN,      "crown + gavel (director / final call)"),
    ("lead-engineer",           "Lead Engineer",          "primary", HARDHAT,    "hard-hat + wrench (builds & plans)"),
    ("worker-engineer",         "Worker Engineer",        "primary", WORKER,     "helmet + bolt (implements)"),
    ("lead-designer",           "Lead Designer",          "teal",    BERET,      "beret + paintbrush (design direction)"),
    ("design-system-steward",   "Design System Steward",  "teal",    RULER,      "beret + ruler/grid (tokens & patterns)"),
    ("interface-designer",      "Interface Designer",     "teal",    BERET,      "beret + paintbrush (screens)"),
    ("ux-evaluator",            "UX Evaluator",           "teal",    MAGNIFIER,  "magnifier + check (usability)"),
    ("research-agent",          "Research Agent",         "amber",   BINOCULARS, "binoculars + flag (scout / evidence)"),
    ("qa",                      "QA",                     "success", QA,         "clipboard + green check (verifies)"),
    ("independent-auditor",     "Independent Auditor",    "danger",  MONOCLE,    "monocle + clipboard (evidence audit)"),
    ("doc-steward",             "Doc Steward",            "muted",   BOOK,       "book + quill (doc integrity)"),
    ("risk-controller",         "Risk Controller",        "danger",  SHIELD,     "shield (risk & safety)"),
    ("release-integrity",       "Release Integrity",      "success", ROCKET,     "rocket (CI/CD & release)"),
    ("finance-controller",      "Finance Controller",     "warning", COIN,       "coin + ledger (finance)"),
    ("accounting-operator",     "Accounting Operator",    "warning", COIN,       "coin + ledger (bookkeeping)"),
    ("asset-steward",           "Asset Steward",          "warning", COIN,       "coin (assets & licenses)"),
    ("revenue-analyst",         "Revenue Analyst",        "warning", COIN,       "coin (unit economics)"),
    ("marketing-lead",          "Marketing Lead",         "amber",   MEGAPHONE,  "megaphone (go-to-market)"),
    ("content-marketer",        "Content Marketer",       "amber",   MEGAPHONE,  "megaphone (content / SEO)"),
    ("growth-analyst",          "Growth Analyst",         "amber",   MEGAPHONE,  "megaphone (channels)"),
    ("brand-steward",           "Brand Steward",          "violet",  MEGAPHONE,  "megaphone (positioning)"),
    ("sales-lead",              "Sales Lead",             "success", TAG,        "deal tag (bizdev)"),
    ("crm-operator",            "CRM Operator",           "success", TAG,        "deal tag (pipeline)"),
    ("partnership-manager",     "Partnership Manager",    "success", TAG,        "deal tag (partnerships)"),
    ("sales-ops",               "Sales Ops",              "success", TAG,        "deal tag (deal desk)"),
    ("operations-lead",         "Operations Lead",        "primary", HEADSET,    "headset (operations)"),
    ("support-operator",        "Support Operator",       "primary", HEADSET,    "headset (helpdesk)"),
    ("customer-success-steward","Customer Success",       "teal",    HEADSET,    "headset (onboarding)"),
    ("process-steward",         "Process Steward",        "muted",   HEADSET,    "headset (runbooks)"),
    ("strategy-lead",           "Strategy Lead",          "violet",  COMPASS,    "compass + map (strategy)"),
    ("planning-architect",      "Planning Architect",     "violet",  COMPASS,    "compass + map (task design)"),
    ("business-analyst",        "Business Analyst",       "primary", COMPASS,    "compass (requirements)"),
    ("portfolio-steward",       "Portfolio Steward",      "violet",  COMPASS,    "compass (roadmap)"),
    ("council",                 "Diversity Council",      "violet",  COUNCIL,    "crown + group (multi-perspective)"),
]


def _resolve_palette(accent_key):
    """Return a concrete palette dict with the role accent substituted in."""
    a_var, a_hex, soft_var, soft_hex = ACCENTS[accent_key]
    pal = {}
    for k, (var, hexv) in PALETTE.items():
        var = var.replace("__ACCENT_SOFT__", soft_var).replace("__ACCENT__", a_var)
        hexv = hexv.replace("__ACCENT_SOFT_HEX__", soft_hex).replace("__ACCENT_HEX__", a_hex)
        pal[k] = (var, hexv)
    return pal


_CLASS_TABLE = {
    ".": "_", "K": "K", "H": "H", "h": "h2", "J": "J", "W": "W",
    "F": "F", "B": "B", "A": "A", "a": "a2", "M": "M", "G": "G", "R": "R",
}


def _cls(ch):
    """Map an art key to a CSS-safe class suffix."""
    return _CLASS_TABLE[ch]


def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(grid, accent_key, title):
    """Render a 16x16 art grid into a token-driven, GitHub-viewable SVG."""
    pal = _resolve_palette(accent_key)
    size = GRID * PX
    used = sorted({ch for row in grid for ch in row if ch != "."})
    css = []
    for ch in used:
        var, hexv = pal[ch]
        # A bare ``var(--x)`` resolves to the initial fill (black) when the SVG
        # is loaded via <img src> (page vars do NOT cascade into an external
        # SVG), so every var carries an inline hex fallback ``var(--x, #hex)``.
        # The token still wins when the SVG is inlined into the console DOM.
        if var.startswith("var("):
            inner = var[len("var("):-1]
            fill = f"var({inner}, {hexv})"
        else:
            fill = hexv
        css.append(f".p{_cls(ch)}{{fill:{fill};}}")
    rects = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = c * PX, r * PX
            rects.append(
                f'<rect x="{x}" y="{y}" width="{PX}" height="{PX}" class="p{_cls(ch)}"/>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}"'
        f' width="{size}" height="{size}" role="img"'
        f' shape-rendering="crispEdges" class="agent-character">'
        f"<title>{_esc(title)}</title>"
        f"<style>{''.join(css)}</style>"
        f"{''.join(rects)}"
        f"</svg>\n"
    )


def role_grid(prop):
    """Public helper: the composed (base + prop) grid for a role's prop."""
    return _overlay(BASE, prop)


_PREVIEW_PALETTE = """  :root {
    color-scheme: light;
    --canvas:#ffffff; --paper:#ffffff; --panel:#f7f7f5; --panel-strong:#f1f1ef;
    --ink:#37352f; --muted:#787774; --subtle:#9b9a97; --line:#e9e9e7;
    --line-strong:#d3d1cb; --primary:#2e6fdb; --success:#0f7b55;
    --warning:#cb7509; --danger:#e03e3e; --teal:#0f7b55; --amber:#cb7509;
    --violet:#6a48c9; --primary-soft:#dde8f9; --success-soft:#d6ece4;
    --warning-soft:#f4e3cc; --danger-soft:#f8dcdc; --teal-soft:#d6ece4;
    --violet-soft:#e6def5; --raise-strong:#ededeb;
    --office-room-bg:var(--panel); --office-room-line:var(--line-strong);
    --office-skin:#f6caa6; --office-skin-shade:#e0a878; --office-hair:#5b4636;
  }
  [data-theme="dark"] {
    color-scheme: dark;
    --canvas:#010102; --paper:#010102; --panel:#0f1011; --panel-strong:#15171a;
    --ink:#f7f8f8; --muted:#a2a8b3; --subtle:#62666d; --line:#23252a;
    --line-strong:#343844; --primary:#5e6ad2; --success:#27a644;
    --warning:#d99a2b; --danger:#f04438; --teal:#31d0aa; --amber:#d99a2b;
    --violet:#5e6ad2; --primary-soft:#1f2433; --success-soft:#163322;
    --warning-soft:#3a2c12; --danger-soft:#3a1614; --teal-soft:#10332b;
    --violet-soft:#1f2433; --raise-strong:#1a1c20;
    --office-skin:#e7b489; --office-skin-shade:#c9925f; --office-hair:#4a3a2c;
  }"""


def _build_preview():
    """Return a standalone, no-build, no-network preview HTML for the v2 sprites.

    Renders all role sprites in an Office-Map-like gallery with a hover/focus
    tooltip (role . status . task), mirroring how the live console presents them.
    The console palette is mirrored inline so the token-driven SVGs show their
    in-console colors here too.
    """
    cards = []
    for role_id, display, accent, _prop, desc in ROLES:
        cards.append(
            f'<figure class="card token-{accent}" tabindex="0" '
            f'title="{_esc(display)} . online . TASK-AR-592">'
            f'<div class="sprite"><img src="{role_id}.svg" alt="{_esc(display)} chibi sprite" '
            f'width="56" height="56"></div>'
            f'<figcaption><b>{_esc(display)}</b><span class="prop">{_esc(desc)}</span>'
            f'<span class="status">online</span></figcaption></figure>'
        )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en" data-theme="light">\n<head>\n<meta charset="utf-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "<title>Agent Characters -- v2 Preview (Office Map)</title>\n"
        "<!-- STANDALONE preview (no build, no network). Open directly. Sprites are\n"
        "     the original .svg files in this directory; the house palette is mirrored\n"
        "     below so they render in in-console colors. -->\n"
        "<style>\n" + _PREVIEW_PALETTE + "\n"
        "  *{box-sizing:border-box;} body{margin:0;background:var(--canvas);"
        "color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Helvetica,Arial,sans-serif;line-height:1.5;}\n"
        "  header{padding:20px 24px;border-bottom:1px solid var(--line);display:flex;"
        "align-items:center;justify-content:space-between;gap:16px;}\n"
        "  header h1{font-size:18px;margin:0;} header p{margin:4px 0 0;color:var(--muted);font-size:13px;}\n"
        "  button{font:inherit;padding:6px 12px;border:1px solid var(--line-strong);"
        "border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer;}\n"
        "  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));"
        "gap:14px;padding:24px;}\n"
        "  .card{margin:0;display:flex;gap:12px;align-items:center;padding:12px;"
        "border:1px solid var(--line);border-top:3px solid var(--line-strong);"
        "border-radius:12px;background:var(--office-room-bg);}\n"
        "  .card.token-violet{border-top-color:var(--violet);} .card.token-primary{border-top-color:var(--primary);}\n"
        "  .card.token-teal{border-top-color:var(--teal);} .card.token-success{border-top-color:var(--success);}\n"
        "  .card.token-warning{border-top-color:var(--warning);} .card.token-amber{border-top-color:var(--amber);}\n"
        "  .card.token-danger{border-top-color:var(--danger);} .card.token-muted{border-top-color:var(--muted);}\n"
        "  .card:hover,.card:focus{outline:2px solid var(--primary);outline-offset:2px;}\n"
        "  .sprite{flex:0 0 auto;width:56px;height:56px;display:flex;align-items:center;"
        "justify-content:center;border-radius:50%;background:var(--panel-strong);"
        "border:2px solid var(--line-strong);}\n"
        "  .sprite img{image-rendering:pixelated;width:48px;height:48px;}\n"
        "  figcaption{display:flex;flex-direction:column;min-width:0;} figcaption b{font-size:13px;}\n"
        "  .prop{font-size:11px;color:var(--muted);} .status{font-size:11px;color:var(--success);font-weight:600;}\n"
        "</style>\n</head>\n<body>\n"
        "<header><div><h1>Agent Characters -- v2 (chibi, filled + colourful)</h1>"
        "<p>Original pixel art. Hover/focus a card for the role . status . task tooltip.</p></div>"
        "<button onclick=\"document.documentElement.dataset.theme="
        "document.documentElement.dataset.theme==='dark'?'light':'dark'\">Toggle theme</button>"
        "</header>\n<main class=\"grid\">\n" + "\n".join(cards) + "\n</main>\n</body>\n</html>\n"
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    written = []
    for role_id, display, accent, prop, _desc in ROLES:
        grid = _overlay(BASE, prop)
        svg = render_svg(grid, accent, f"{display} -- agent character (chibi v2)")
        path = os.path.join(here, f"{role_id}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        written.append(os.path.basename(path))

    preview_path = os.path.join(here, "preview.html")
    with open(preview_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(_build_preview())
    written.append("preview.html")

    print(f"Wrote {len(written)} files to {here}")
    for name in written:
        print("  " + name)


if __name__ == "__main__":
    main()
