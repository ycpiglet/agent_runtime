#!/usr/bin/env python3
"""Deterministic cute pixel-art agent-character sprite generator (DRAFT, v1).

FIRST DRAFT for Owner review (RFC-2026-06-23 P1 spike, *experimental* tier).
This is a *show-and-iterate* design draft, NOT wired into the live console.

Design contract (mirrors the AR-587 ``patternAgentAvatar`` precedent):
- ORIGINAL pixel art authored here from a small primitive grid. No third-party
  IP, no scraped sprites (Pokemon/Game-Boy are *style references only*).
- Token-driven: every fill is a CSS custom property from the house palette
  (DESIGN-SYSTEM.md / ui_console_assets.py ``:root``). Role accent maps to the
  same semantic token as ``_AVATAR_ROLE_ACCENT_PY``. A ``<style>`` block embeds
  fallbacks so the SVGs *also* render standalone on GitHub.
- Deterministic + zero runtime deps: pure pixel grid -> ``<rect>`` elements.
  Same role -> byte-identical SVG. No network, no canvas, offline.
- Accessible: role/status are encoded by silhouette + prop + a state badge
  glyph, never hue alone (AR-588 non-color-only rule). ``<title>`` for SR.

The aesthetic is "아기자기" Game-Boy / early-Pokemon-era chibi: ~16x16 logical
pixel grid, chunky pixels, 2.5-head proportions, large eyes, soft palette,
one clear role prop/accessory per role.

Run: ``python generate_sprites.py`` -> writes one ``<role>.svg`` per role plus
sample style variants into this directory.
"""
from __future__ import annotations

import os

# --- Pixel scale -----------------------------------------------------------
# Logical grid is 16x16 "art" cells. Each art cell is PX device pixels so the
# sprite renders crisp and large enough to read in the office map.
GRID = 16
PX = 8  # 16 * 8 = 128px sprite

# --- Palette: logical key -> CSS var (house token) -------------------------
# The GitHub-viewable fallback hex are the LIGHT-theme token values from
# ui_console_assets.py :root so the same SVG renders with or without the
# console CSS variables.
PALETTE = {
    # structural / neutral
    ".": ("transparent", "transparent"),          # empty
    "K": ("var(--ink)", "#37352f"),                # outline / dark ink
    "S": ("var(--panel-strong)", "#f1f1ef"),       # skin / body light
    "s": ("var(--line-strong)", "#d3d1cb"),        # shade line
    "W": ("var(--paper)", "#ffffff"),              # eye white / highlight
    "F": ("var(--ink)", "#37352f"),                # face features (eyes)
    # blush — soft feminine accent (여성향 soft palette)
    "B": ("var(--danger-soft)", "#f8dcdc"),
    # ACCENT is substituted per-role (see ROLE_ACCENT_TOKEN). Two tints:
    "A": ("__ACCENT__", "__ACCENT_HEX__"),         # role accent (solid)
    "a": ("__ACCENT_SOFT__", "__ACCENT_SOFT_HEX__"),  # role accent (soft)
    # prop neutrals
    "M": ("var(--warning)", "#cb7509"),            # metal / wood / gold prop
    "G": ("var(--success)", "#0f7b55"),            # green prop / check
    "R": ("var(--danger)", "#e03e3e"),             # red prop / alert
}

# Role accent token + GitHub fallback hex (light theme), aligned with
# _AVATAR_ROLE_ACCENT_PY in ui_design_assets.py.
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
# Shared chibi base body (head + torso + eyes + blush) drawn at the bottom.
# Props/headgear are overlaid per role. The grid is read top (row 0) -> bottom.
# A capital art key wins over a lower-case neutral when overlaying.
# ---------------------------------------------------------------------------

# Base 16x16: a 2.5-head chibi standing figure, accent-tinted body.
BASE = [
    "................",
    "................",
    "....KKKKKK......",
    "...KSSSSSSK.....",
    "..KSSSSSSSSK....",
    "..KSFSSSSFSK....",   # eyes
    "..KSFSSSSFSK....",
    "..KSSBSSBSSK....",   # blush
    "..KSSSWWSSSK....",   # mouth highlight
    "...KSSSSSSK.....",
    "....KaaaaK......",   # collar (accent soft)
    "...KaAAAAaK.....",   # torso (accent)
    "..KaAAAAAAaK....",
    "..KaAAAAAAaK....",
    "..KKsKKKKsKK....",   # legs base
    "...KK....KK.....",
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
# Per-role prop/headgear overlays. Each conveys the role via a small, readable
# accessory + silhouette change (the Owner's "role distinction must be CLEAR").
# Empty cells ('.') leave the base showing through.
# ---------------------------------------------------------------------------

# Hard-hat + wrench (engineering lead)
HARDHAT = [
    "................",
    "....MMMMMM......",
    "...MMMMMMMM.....",
    "..M........M....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........MM....",  # wrench head
    "..........MMM...",
    ".........MM.....",
    "................",
    "................",
]

# Plain helmet, lighter (worker engineer) + small bolt
WORKER = [
    "................",
    "....MMMMMM......",
    "...MMMMMMMM.....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "...........M....",  # bolt
    "..........MMM...",
    "...........M....",
    "................",
    "................",
]

# Director: small crown/gavel (managing-partner)
CROWN = [
    "................",
    "...M.M.M.M.M....",  # crown points
    "...MMMMMMMMM....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........KK....",  # gavel
    "..........MM....",
    ".........MM.....",
    "................",
    "................",
]

# Designer: beret + paintbrush (lead-designer / interface-designer)
BERET = [
    "................",
    "....aaaaa.......",
    "...aaaaaaaA.....",  # tilted beret w/ nub
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........MK....",  # brush handle
    "..........MK....",
    ".........RR.....",  # brush tip (paint)
    "................",
    "................",
]

# Design-system steward: ruler/grid + beret hint (token steward)
RULER = [
    "................",
    "....aaaaa.......",
    "...aaaaaaa......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........MMMM...",  # ruler
    ".........M.M.M..",
    "................",
    "................",
    "................",
]

# UX evaluator: magnifier + checkmark
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
    "................",
    "..........KKK...",  # lens
    ".........K.aK...",
    ".........KaaK...",
    "..........KKK...",
    "...........KK...",  # handle
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
    "................",
    "................",
    ".........KKKK...",  # clipboard
    ".........KGGK...",
    ".........KGGK...",  # green check region
    ".........KKKK...",
    "................",
    "................",
]

# Independent auditor / skeptic: monocle + clipboard (red accent)
MONOCLE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........KK.....",  # monocle ring at eye
    ".........KK.....",
    "................",
    "................",
    "................",
    ".........KKKK...",  # clipboard
    ".........KRRK...",
    ".........KRRK...",
    ".........KKKK...",
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
    "................",
    "................",
    ".........RRR....",  # shield
    ".........RRR....",
    ".........RRR....",
    "..........R.....",
    "................",
    "................",
]

# Release-integrity (ci/cd): rocket / launch
ROCKET = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........G.....",  # nose
    ".........GGG....",
    ".........GGG....",
    ".........G.G....",
    ".........M.M....",  # flame base
    "................",
    "................",
]

# Doc-steward / scribe: book + quill
BOOK = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........KKKK...",  # book
    ".........KSSK...",
    ".........KSSK...",
    ".........KKKK...",
    "..........K.....",  # quill
    "................",
]

# Research-agent / progress-scout: binoculars + flag (amber)
BINOCULARS = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "..KK....KK......",  # binoculars over eyes
    "..KaK..KaK......",
    "..KK....KK......",
    "................",
    "................",
    "...........MM...",  # flag pole + flag
    "...........M.A..",
    "...........MAA..",
    "...........M....",
    "................",
    "................",
]

# Finance / accounting / asset / revenue: coin + ledger (warning/amber)
COIN = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........MM....",  # coin
    ".........MaaM...",
    ".........MaAM...",
    "..........MM....",
    "................",
    "................",
    "................",
]

# Marketing / content / growth / brand: megaphone (amber/violet)
MEGAPHONE = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "...........A....",  # sound
    "..........AKK...",
    ".........AaaKK..",  # megaphone cone
    ".........AaaKK..",
    "..........AKK...",
    "...........A....",
    "................",
]

# Sales / crm / partnership / sales-ops: handshake / deal tag (success)
TAG = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........GG.....",  # price tag
    "........GAAG....",
    "........GAAG....",
    ".........GG.....",
    "..........G.....",
    "................",
    "................",
]

# Operations / support / success / process: headset (ops)
HEADSET = [
    "................",
    "...aKKKKKKa.....",  # headset band
    "..aK......Ka....",
    "..K........K....",  # ear cups (overlay base ears)
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "..........KK....",  # mic boom
    "..........KaK...",
    "................",
    "................",
    "................",
    "................",
]

# Strategy / planning / business-analyst / portfolio: map + compass
COMPASS = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........KKKK...",  # compass
    ".........KaAK...",
    ".........KAaK...",
    ".........KKKK...",
    "................",
    "................",
]

# Council / diversity-council group prop: trio dots (group)
COUNCIL = [
    "................",
    "...M.M.M.M.M....",  # crown (director base)
    "...MMMMMMMMM....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    ".........A.A....",  # group of three
    "........A.A.A...",
    ".........A.A....",
    "................",
    "................",
    "................",
]


# ---------------------------------------------------------------------------
# Role registry: id -> (display, accent key, prop overlay, prop description)
# Accent keys align with _AVATAR_ROLE_ACCENT_PY. Props chosen for a CLEAR,
# readable role cue (silhouette + accessory), per the Owner's direction.
# ---------------------------------------------------------------------------
ROLES = [
    ("managing-partner",       "Managing Partner",       "violet",  CROWN,      "crown + gavel (director / final call)"),
    ("lead-engineer",          "Lead Engineer",          "primary", HARDHAT,    "hard-hat + wrench (builds & plans)"),
    ("worker-engineer",        "Worker Engineer",        "primary", WORKER,     "helmet + bolt (implements)"),
    ("lead-designer",          "Lead Designer",          "teal",    BERET,      "beret + paintbrush (design direction)"),
    ("design-system-steward",  "Design System Steward",  "teal",    RULER,      "beret + ruler/grid (tokens & patterns)"),
    ("interface-designer",     "Interface Designer",     "teal",    BERET,      "beret + paintbrush (screens)"),
    ("ux-evaluator",           "UX Evaluator",           "teal",    MAGNIFIER,  "magnifier + check (usability)"),
    ("research-agent",         "Research Agent",         "amber",   BINOCULARS, "binoculars + flag (scout / evidence)"),
    ("qa",                     "QA",                     "success", QA,         "clipboard + green check (verifies)"),
    ("independent-auditor",    "Independent Auditor",    "danger",  MONOCLE,    "monocle + clipboard (evidence audit)"),
    ("doc-steward",            "Doc Steward",            "muted",   BOOK,       "book + quill (doc integrity)"),
    ("risk-controller",        "Risk Controller",        "danger",  SHIELD,     "shield (risk & safety)"),
    ("release-integrity",      "Release Integrity",      "success", ROCKET,     "rocket (CI/CD & release)"),
    ("finance-controller",     "Finance Controller",     "warning", COIN,       "coin + ledger (finance)"),
    ("accounting-operator",    "Accounting Operator",    "warning", COIN,       "coin + ledger (bookkeeping)"),
    ("asset-steward",          "Asset Steward",          "warning", COIN,       "coin (assets & licenses)"),
    ("revenue-analyst",        "Revenue Analyst",        "warning", COIN,       "coin (unit economics)"),
    ("marketing-lead",         "Marketing Lead",         "amber",   MEGAPHONE,  "megaphone (go-to-market)"),
    ("content-marketer",       "Content Marketer",       "amber",   MEGAPHONE,  "megaphone (content / SEO)"),
    ("growth-analyst",         "Growth Analyst",         "amber",   MEGAPHONE,  "megaphone (channels)"),
    ("brand-steward",          "Brand Steward",          "violet",  MEGAPHONE,  "megaphone (positioning)"),
    ("sales-lead",             "Sales Lead",             "success", TAG,        "deal tag (bizdev)"),
    ("crm-operator",           "CRM Operator",           "success", TAG,        "deal tag (pipeline)"),
    ("partnership-manager",    "Partnership Manager",    "success", TAG,        "deal tag (partnerships)"),
    ("sales-ops",             "Sales Ops",               "success", TAG,        "deal tag (deal desk)"),
    ("operations-lead",        "Operations Lead",        "primary", HEADSET,    "headset (operations)"),
    ("support-operator",       "Support Operator",       "primary", HEADSET,    "headset (helpdesk)"),
    ("customer-success-steward", "Customer Success",     "teal",    HEADSET,    "headset (onboarding)"),
    ("process-steward",        "Process Steward",        "muted",   HEADSET,    "headset (runbooks)"),
    ("strategy-lead",          "Strategy Lead",          "violet",  COMPASS,    "compass + map (strategy)"),
    ("planning-architect",     "Planning Architect",     "violet",  COMPASS,    "compass + map (task design)"),
    ("business-analyst",       "Business Analyst",       "primary", COMPASS,    "compass (requirements)"),
    ("portfolio-steward",      "Portfolio Steward",      "violet",  COMPASS,    "compass (roadmap)"),
    ("council",                "Diversity Council",      "violet",  COUNCIL,    "crown + group (multi-perspective)"),
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


def render_svg(grid, accent_key, title):
    """Render a 16x16 art grid into a token-driven, GitHub-viewable SVG."""
    pal = _resolve_palette(accent_key)
    size = GRID * PX
    # Collect a class per distinct logical key so a <style> block can set both
    # the CSS-var fill (in-console) and a hex fallback (standalone on GitHub).
    used = sorted({ch for row in grid for ch in row if ch != "."})
    css = []
    for ch in used:
        var, hexv = pal[ch]
        # IMPORTANT: a bare ``var(--x)`` is syntactically valid but resolves to
        # the *initial* fill (black) when this SVG is loaded via <img src> (the
        # page CSS vars do NOT cascade into an externally-referenced SVG). So we
        # MUST give every var an inline hex fallback: ``var(--token, #hex)``.
        # The token still wins when the SVG is inlined into the console DOM
        # (where the house vars are defined); the hex applies standalone / on
        # GitHub. This keeps the sprites token-driven AND GitHub-viewable.
        if var.startswith("var("):
            inner = var[len("var("):-1]  # strip "var(" .. ")"
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


def _cls(ch):
    """Map an art key to a CSS-safe class suffix."""
    table = {
        ".": "_", "K": "K", "S": "S", "s": "s2", "W": "W", "F": "F",
        "B": "B", "A": "A", "a": "a2", "M": "M", "G": "G", "R": "R",
    }
    return table[ch]


def _esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    written = []
    for role_id, display, accent, prop, _desc in ROLES:
        grid = _overlay(BASE, prop)
        svg = render_svg(grid, accent, f"{display} — agent character (draft v1)")
        path = os.path.join(here, f"{role_id}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        written.append(os.path.basename(path))

    # --- Style variants of a sample role (lead-engineer) -------------------
    # So the Owner can choose a direction. Same role, three treatments.
    sample = _overlay(BASE, HARDHAT)
    variants = {
        # A) Standard chibi (the default above) — re-emit under explicit name.
        "_variant-A-chibi-lead-engineer.svg": (sample, "primary",
            "Variant A — Standard chibi (default look)"),
        # B) Big-head 2-head "아기자기" cuter proportion (head grows, body shrinks).
        "_variant-B-bighead-lead-engineer.svg": (_overlay(BASE_BIGHEAD, HARDHAT),
            "primary", "Variant B — Bighead (extra-cute, 2-head chibi)"),
        # C) Outline-only / soft pastel (lighter ink, accent-soft body fill).
        "_variant-C-softline-lead-engineer.svg": (_overlay(BASE_SOFT, HARDHAT_SOFT),
            "primary", "Variant C — Soft pastel outline (여성향 gentle palette)"),
    }
    for fname, (grid, accent, title) in variants.items():
        svg = render_svg(grid, accent, title)
        with open(os.path.join(here, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        written.append(fname)

    print(f"Wrote {len(written)} sprites to {here}")
    for name in written:
        print("  " + name)


# --- Variant base grids ----------------------------------------------------
# B) Bighead: larger head, tiny body — maximally "cute/아기자기".
BASE_BIGHEAD = [
    "................",
    "....KKKKKK......",
    "...KSSSSSSK.....",
    "..KSSSSSSSSK....",
    "..KSFSSSSFSK....",
    "..KSFSSSSFSK....",
    "..KSFSSSSFSK....",
    "..KSSBSSBSSK....",
    "..KSSSWWSSSK....",
    "..KSSSSSSSSK....",
    "...KSSSSSSK.....",
    "....KaAAaK......",   # tiny torso
    "...KaAAAAaK.....",
    "...KK....KK.....",   # stubby legs
    "................",
    "................",
]

# C) Soft pastel: ink outline replaced by accent-soft 'a' tone, body soft.
# We swap K->a and A->a in a copy so the figure reads gentle/pastel.
def _soften(grid):
    out = []
    for row in grid:
        out.append(
            row.replace("K", "s").replace("A", "a")
        )
    return out


BASE_SOFT = _soften(BASE)


def _soften_prop(grid):
    return [row.replace("K", "s") for row in grid]


HARDHAT_SOFT = _soften_prop(HARDHAT)


if __name__ == "__main__":
    main()
