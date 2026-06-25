#!/usr/bin/env python3
"""Deterministic generator for the v3 agent-character sprites (TASK-AR-592 v3).

v3 design pivot (Owner-approved):

  * Base body is informed by the **GrafxKid "RPG character" CC0 sprite**
    (`base/grafxkid-rpg-character_CC0.png`, OpenGameArt CC0 — attribution NOT
    required; provenance in `base/SOURCES.md`). The shipped art is rendered as
    token-driven pixel SVG (no bundled raster), so the served console stays
    self-hosted, hex-free and theme-aware -- the CC0 sheet is the *reference*.
  * We do **NOT** draw 34 unique characters. The 34 ORG-MODEL roles are grouped
    into **8 CATEGORIES**; a category is distinguished by an **accessory overlay
    (hat/item)** + a **category token color** (same body, optional minor tweak).

Run ``python generate_sprites.py`` to re-emit every catalog SVG byte-identically.
Edit the pixel grids / category maps HERE, never the SVGs by hand. The live
console renders the SAME art via a JS twin (`patternV3Sprite`) in
``src/agent_runtime/ui_design_assets.py``; the BASE / accessory / category maps
are identical and verified cell-for-cell by ``tests/test_v3_sprites.py``.

ASCII-only output (cp949 node-check guard). Maturity tier: standard.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Token palette. Every art cell resolves to a house CSS var (no raw hex in the
# served JS twin -> design_system_gate stays green). The on-disk catalog SVGs
# carry a ``var(--token, #hex)`` fallback so they also render standalone on
# GitHub; the hex lives ONLY in these on-disk SVGs, never in the JS bundle.
# ---------------------------------------------------------------------------

# Static (category-independent) art-key -> (css var, standalone hex fallback).
STATIC = {
    "K": ("var(--ink, #37352f)", "#37352f"),          # outline / ink
    "H": ("var(--office-skin, #f6caa6)", "#f6caa6"),   # skin (face fill)
    "h": ("var(--office-skin-shade, #e0a878)", "#e0a878"),  # skin shade (volume)
    "J": ("var(--office-hair, #5b4636)", "#5b4636"),   # hair
    "W": ("var(--paper, #ffffff)", "#ffffff"),         # eye white / highlight
    "F": ("var(--ink, #37352f)", "#37352f"),           # eye / mouth ink
    "B": ("var(--danger, #e03e3e)", "#e03e3e"),        # cheek blush
}

# Category accent key -> (solid var/hex, soft var/hex). Soft = clothing shade.
ACCENTS = {
    "primary": (("var(--primary, #2e6fdb)", "#2e6fdb"),
                ("var(--primary-soft, #dde8f9)", "#dde8f9")),
    "teal":    (("var(--teal, #0f9488)", "#0f9488"),
                ("var(--teal-soft, #d2efeb)", "#d2efeb")),
    "danger":  (("var(--danger, #e03e3e)", "#e03e3e"),
                ("var(--danger-soft, #fbdada)", "#fbdada")),
    "amber":   (("var(--amber, #cb7509)", "#cb7509"),
                ("var(--warning-soft, #f7e4c8)", "#f7e4c8")),
    "violet":  (("var(--violet, #6a48c9)", "#6a48c9"),
                ("var(--violet-soft, #e3dbf6)", "#e3dbf6")),
    "warning": (("var(--warning, #cb7509)", "#cb7509"),
                ("var(--warning-soft, #f7e4c8)", "#f7e4c8")),
    "success": (("var(--success, #0f7b55)", "#0f7b55"),
                ("var(--success-soft, #cfeadd)", "#cfeadd")),
    "muted":   (("var(--muted, #787774)", "#787774"),
                ("var(--raise-strong, #e6e6e3)", "#e6e6e3")),
}

# ---------------------------------------------------------------------------
# Base body: 16x16 art grid, front-facing chibi RPG character (GrafxKid-style
# proportions -- big rounded head, small sturdy torso, two little legs). Lower
# case 'a' = soft/clothing accent, 'A' = solid accent (filled in per category).
# Capital letters in an accessory overlay OVERRIDE the base cell.
# ---------------------------------------------------------------------------
BASE = [
    ".....KKKKKK.....",
    "....KJJJJJJK....",
    "...KJJJJJJJJK...",
    "...KJHHHHHHJK...",
    "...KHHHHHHHHK...",
    "...KHFHHHHFHK...",  # eyes
    "...KHWFHHFWHK...",  # eye shine
    "...KHHHHHHHHK...",
    "...KhBHFFHBhK...",  # blush + mouth + cheek shade
    "....KHHHHHHK....",  # jaw
    "....KaHHHHaK....",  # neck + collar wings
    "...KaAAAAAAaK...",  # shoulders (accent)
    "...KAAAWWAAAK...",  # torso + shirt placket
    "...KAAAWWAAAK...",  # torso
    "...KhAAAAAAhK...",  # belt line (shade edges)
    "....KK..KK.....",  # two legs
]

# ---------------------------------------------------------------------------
# Per-CATEGORY accessory overlay (hat/item). ONE accessory per category. The
# overlay is original art (license-trivial). '.' = transparent (keep base).
# Accessory uses the SAME art keys; 'A'/'a' pick up the category accent so the
# hat/item is also category-colored. 8 categories total.
# ---------------------------------------------------------------------------
ACCESSORIES = {
    # Engineering -- hard hat: bold accent dome + brim across the head top.
    "hardhat": [
        ".....AAAAAA.....",
        "....AAAAAAAA....",
        "...AAAAAAAAAA...",
        "..KAAAAAAAAAAK..",
        "...K........K...",
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
        "................",
    ],
    # Design -- beret (tilted) + a brush held at the side.
    "beret": [
        "....AAA.........",
        "...AAAAAA.W.....",
        "..AAAAAAAAWK....",
        "...aaaaaa..K....",
        "...........K....",
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
        "................",
    ],
    # Quality/Audit -- magnifier held up beside the head (clear lens + handle).
    "magnifier": [
        "................",
        "................",
        "..........KKK...",
        ".........KaaaK..",
        ".........KaWaK..",
        ".........KaaaK..",
        "..........KKK...",
        "...........KK...",
        "............KK..",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Research -- binoculars raised across the eyes (two accent barrels).
    "binoculars": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..KAAK..KAAK....",
        "..KAWK..KAWK....",
        "..KAAK..KAAK....",
        "...KK....KK.....",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Leadership/Council -- crown on the head (spiked, accent + jewel).
    "crown": [
        "...A.A.A.A.A....",
        "...AAAAAAAAA....",
        "...AWAKAWAKA....",
        "...KKKKKKKKK....",
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
        "................",
        "................",
    ],
    # Finance/Ops -- big coin held up beside the head ('$'-ish accent disc).
    "coin": [
        "................",
        "................",
        "..........KKK...",
        ".........KAAAK..",
        ".........KAWAK..",
        ".........KWAWK..",
        ".........KAWAK..",
        ".........KAAAK..",
        "..........KKK...",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Marketing/Sales -- megaphone raised beside the head (cone + sound waves).
    "megaphone": [
        "................",
        "................",
        "................",
        "...........KAK..",
        "..........KAAKW.",
        ".........KAAaKW.",
        ".........KAAaKW.",
        "..........KAAKW.",
        "...........KAK..",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Docs -- open book held up (two white pages + accent spine).
    "book": [
        "................",
        "................",
        "................",
        ".........KKKKKK.",
        ".........KWWAWWK",
        ".........KWWAWWK",
        ".........KWWAWWK",
        ".........KWWAWWK",
        ".........KKKKKK.",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
}

# ---------------------------------------------------------------------------
# The 8 CATEGORIES. id -> (display, accent key, accessory key, token, blurb).
# `token` is the human-facing token color name from the Owner brief.
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("engineering",     "Engineering",       "primary", "hardhat",    "blue",   "hard-hat (builds & implements)"),
    ("design",          "Design",            "teal",    "beret",      "teal",   "beret + brush (design & UX)"),
    ("quality-audit",   "Quality / Audit",   "danger",  "magnifier",  "red",    "magnifier + clipboard (verifies)"),
    ("research",        "Research",          "amber",   "binoculars", "amber",  "binoculars (scout / evidence)"),
    ("leadership",      "Leadership / Council", "violet", "crown",    "violet", "crown + gavel (direction)"),
    ("finance-ops",     "Finance / Ops",     "warning", "coin",       "yellow", "coin + ledger (finance & ops)"),
    ("marketing-sales", "Marketing / Sales", "success", "megaphone",  "green",  "megaphone + tag (go-to-market)"),
    ("docs",            "Docs",              "muted",   "book",       "gray",   "book (doc integrity)"),
]

CATEGORY_BY_ID = {c[0]: c for c in CATEGORIES}

# ---------------------------------------------------------------------------
# role -> category. EVERY canonical ORG-MODEL role (34) maps here, plus a few
# Owner-brief aliases / extra ids routed to the closest category so nothing
# renders blank. Mirrors the JS _V3_ROLE_CATEGORY map.
# ---------------------------------------------------------------------------
ROLE_CATEGORY = {
    # Engineering (blue, hard-hat)
    "lead-engineer": "engineering",
    "worker-engineer": "engineering",
    # Design (teal, beret/brush)
    "lead-designer": "design",
    "design-system-steward": "design",
    "interface-designer": "design",
    "ux-evaluator": "design",
    # Quality / Audit (red, magnifier/clipboard)
    "qa": "quality-audit",
    "independent-auditor": "quality-audit",
    "risk-controller": "quality-audit",
    "release-integrity": "quality-audit",
    # Research (amber, binoculars/glasses)
    "research-agent": "research",
    "progress-scout": "research",
    "business-analyst": "research",
    "growth-analyst": "research",
    # Leadership / Council (violet, crown/gavel)
    "managing-partner": "leadership",
    "council": "leadership",
    # Finance / Ops (yellow, coin/ledger)
    "finance-controller": "finance-ops",
    "accounting-operator": "finance-ops",
    "asset-steward": "finance-ops",
    "revenue-analyst": "finance-ops",
    "sales-ops": "finance-ops",
    # Marketing / Sales (green, megaphone/tag)
    "marketing-lead": "marketing-sales",
    "content-marketer": "marketing-sales",
    "brand-steward": "marketing-sales",
    "sales-lead": "marketing-sales",
    "crm-operator": "marketing-sales",
    "partnership-manager": "marketing-sales",
    # Docs (gray, book)
    "doc-steward": "docs",
    # --- Closest-category routing for the remaining canonical-34 roles that
    #     are not named in the Owner's 8-group brief (placed by discipline) ---
    "operations-lead": "finance-ops",       # ops
    "support-operator": "finance-ops",       # ops/support
    "customer-success-steward": "marketing-sales",  # customer-facing
    "process-steward": "docs",               # process/runbook docs
    "strategy-lead": "leadership",           # strategy = direction
    "planning-architect": "leadership",      # planning = direction
    "portfolio-steward": "leadership",       # portfolio = direction
}

# Canonical 34 ORG-MODEL roles (mirror of the v2 ROLES registry) -- the set the
# coverage test asserts is fully mapped.
CANONICAL_ROLES = [
    "managing-partner", "lead-engineer", "worker-engineer", "lead-designer",
    "design-system-steward", "interface-designer", "ux-evaluator",
    "research-agent", "qa", "independent-auditor", "doc-steward",
    "risk-controller", "release-integrity", "finance-controller",
    "accounting-operator", "asset-steward", "revenue-analyst", "marketing-lead",
    "content-marketer", "growth-analyst", "brand-steward", "sales-lead",
    "crm-operator", "partnership-manager", "sales-ops", "operations-lead",
    "support-operator", "customer-success-steward", "process-steward",
    "strategy-lead", "planning-architect", "business-analyst",
    "portfolio-steward", "council",
]


def category_for_role(role_id: str) -> str:
    """Return the category id for a role, defaulting to engineering if unknown."""
    return ROLE_CATEGORY.get(role_id, "engineering")


def compose_grid(accessory_key: str) -> list[str]:
    """Overlay an accessory on the base body (accessory cell wins over base)."""
    accessory = ACCESSORIES.get(accessory_key)
    grid = []
    for r, base_row in enumerate(BASE):
        acc_row = accessory[r] if accessory else None
        row = []
        for c, base_ch in enumerate(base_row):
            ach = acc_row[c] if acc_row else "."
            row.append(ach if ach != "." else base_ch)
        grid.append("".join(row))
    return grid


# Art key -> short CSS-class suffix used in the on-disk catalog SVGs.
_CLASS_TABLE = {
    "K": "K", "H": "H", "h": "h", "J": "J", "W": "W", "F": "F", "B": "B",
    "A": "A", "a": "a",
}


def _resolve_palette(accent_key: str):
    """Return {art_key: (css_var, hex)} with the category accent substituted."""
    (a_var, a_hex), (soft_var, soft_hex) = ACCENTS[accent_key]
    pal = {k: v for k, v in STATIC.items()}
    pal["A"] = (a_var, a_hex)
    pal["a"] = (soft_var, soft_hex)
    return pal


def render_svg(grid: list[str], accent_key: str, title: str) -> str:
    """Render a category grid to a token-driven catalog SVG (with hex fallback).

    Uses CSS classes (one per art key) so the standalone SVG is compact and the
    fills carry a ``var(--token, #hex)`` fallback (renders on GitHub + themes).
    """
    pal = _resolve_palette(accent_key)
    used = sorted({ch for row in grid for ch in row if ch != "."})
    style = "".join(
        f".p{_CLASS_TABLE[ch]}{{fill:{pal[ch][0]};}}" for ch in used
    )
    px = 8  # 16 art cells * 8 = 128 viewBox units
    rects = []
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            rects.append(
                f'<rect x="{c * px}" y="{r * px}" width="{px}" height="{px}" '
                f'class="p{_CLASS_TABLE[ch]}"/>'
            )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
        'width="128" height="128" role="img" shape-rendering="crispEdges" '
        'class="agent-character v3-sprite">'
        f"<title>{title}</title><style>{style}</style>" + "".join(rects) + "</svg>"
    )


def category_svg(category_id: str) -> str:
    display, accent, accessory, _token, _blurb = CATEGORY_BY_ID[category_id][1:]
    grid = compose_grid(accessory)
    return render_svg(grid, accent, f"{display} -- agent character (v3)")


def main() -> None:
    written = 0
    for cat_id, display, accent, accessory, token, _blurb in CATEGORIES:
        grid = compose_grid(accessory)
        svg = render_svg(grid, accent, f"{display} -- agent character (v3)")
        (HERE / f"{cat_id}.svg").write_text(svg + "\n", encoding="utf-8")
        written += 1
    print(f"wrote {written} v3 category SVGs to {HERE}")


if __name__ == "__main__":
    main()
