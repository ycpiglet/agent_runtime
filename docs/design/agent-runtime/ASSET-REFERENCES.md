---
title: Agent Runtime Asset Reference Library
status: living
date: 2026-06-24
task_set_id: TASKSET-AR-VISUAL-IDENTITY
---

# Agent Runtime Asset Reference Library

## Purpose

Durable, re-accessible catalog of pixel/game character asset sources, generators,
licenses, and decisions for the agent-character visualization work. This is a
living reference so the Owner can re-access and reuse every asset source,
generator, and design decision at any time without re-running the research.

## Chosen direction (as of 2026-06-24)

- **Style / tone:** chibi (big-head, cute, 2-3 head proportions), Game-Boy-era
  pixel feel. (Owner-decided.)
- **Placement:** leaning **Office Map** (pending final confirm).
- **License path:** **PENDING Owner** decision between two paths:
  - **Path A (recommended):** CC0 packs (Kenney / OpenGameArt) - no attribution,
    no copyleft, lowest friction for a public repo.
  - **Path B:** LPC (Universal LPC Spritesheet Generator) - richest and fully
    animated, but art is CC-BY-SA 3.0 (copyleft, requires attribution +
    share-alike on the sprite assets).
- **Status badges:** glyph + label (not color-only), hover tooltip = role /
  status / task.

## Source & tool catalog

| Name | What it is | URL | License | Use for | Notes |
| --- | --- | --- | --- | --- | --- |
| **Kenney** | Pre-made pixel / game asset packs | https://kenney.nl/assets | **CC0** (no attribution) | PRIMARY candidate - colorful, detailed, some animated | Not a generator; curate + recolor |
| **OpenGameArt.org** | Community game-art repository | https://opengameart.org/content/cc0-2 | Mixed (filter **CC0**) | CC0 character / animation sources | Verify per-asset license |
| **itch.io (CC0)** | Indie asset marketplace | https://itch.io/game-assets/assets-cc0/tag-pixel-art | Per-pack (use **CC0** only) | Colorful animated packs (Ninja Adventure, Ansimuz, Mini World 16x16, Kenney All-in-1) | Some "free" packs forbid redistribution - CC0 only for a public repo |
| **LPC / Universal LPC Spritesheet Generator** | Modular animated character GENERATOR (web) | App: https://sanderfrenken.github.io/Universal-LPC-Spritesheet-Character-Generator/ - Repo: https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator | Code **GPL-3.0**, art mostly **CC-BY-SA 3.0** (copyleft, bounded to the committed sprite files; app code is NOT a derivative) | Path B - richest, fully animated, modular, auto role-gen | Attribution CREDITS + share-alike on the sprite assets |
| **sprite-gen / pixel-sprite-generator** | Procedural RANDOM pixel-sprite generators | https://github.com/zfedoran/pixel-sprite-generator (JS), https://github.com/tversteeg/sprite-gen (Rust), https://github.com/MaartenGr/Sprite-Generator (Py), https://github.com/soulfir/sprite-generator (CA-animated) | Mostly **MIT** | Secondary - ambient / decorative variety | Random creatures / robots; NOT role-distinct office characters |
| **DiceBear pixel-art** | Deterministic avatar generator | https://www.dicebear.com | **CC0** | Identity avatars (used by AR-587 `patternAgentAvatar`) | Static, not full game sprites |
| **PerfectPixel (WellDoneCode)** | Chrome extension: design-mockup overlay for pixel-perfect QA | https://www.welldonecode.com/perfectpixel/ | Free proprietary extension | **QA tool, NOT an asset source** - verify implemented Office Map matches the design mockup | Clarified 2026-06-24 |
| **awesome-cc0** | Curated CC0 asset index | https://github.com/madjin/awesome-cc0 | (Index) | Finding more CC0 sources | - |

## Chosen + shipped (2026-06-25)

Owner approved **Path A (CC0 / original-generated chibi)**, tone **chibi**,
placement **Office Map**, standard tier. v2 sprites are now **live** in the
console Office Map. v2 honoured the Owner note on v1 ("more colour, fill the
empty centre") with a warm skin-filled face, hair cap, and a solid colour torso.
All art is **original** (repo license); no external/CC0 asset is bundled, so no
new attribution entry is required.

## In-repo references

These live on `origin/main`; paths verified to exist (2026-06-24).

- **Shipped sprites (v2, live on Office Map):**
  `agents/project/assets/agent-characters/v2/`
  - 34 role SVGs (colourful, filled-centre chibi), `preview.html`, `README.md`,
    `generate_sprites.py` (deterministic; JS twin = `patternChibiSprite` in
    `src/agent_runtime/ui_design_assets.py`, parity-tested).
- **Draft sprites + interactive preview (v1, PRESERVED):**
  `agents/project/assets/agent-characters/v1/`
  - 34 role SVGs, 3 chibi / bighead / softline variant SVGs
    (`_variant-A-chibi-lead-engineer.svg`, `_variant-B-bighead-lead-engineer.svg`,
    `_variant-C-softline-lead-engineer.svg`)
  - `preview.html` (interactive preview)
  - `README.md`
  - `generate_sprites.py`
- **Research:** `reviews/RESEARCH-2026-06-24-oss-sprite-generators.md`
  (LPC deep-dive, PR #223)
- **RFCs:**
  - `reviews/RFC-2026-06-23-visual-identity-and-agent-characters.md`
  - `reviews/RFC-2026-06-23-character-design-exploration.md`

## Pixel-asset eval summary (2026-06-24)

The verdicts below are preserved here because the separate eval report was lost
to an API overload.

- **Kenney** - CC0 (ideal license), colorful (directly addresses the "empty
  center" problem), pre-made packs. Verdict: **PRIMARY**.
- **sprite-gen / pixel-sprite-generator** - MIT, procedural / random output.
  Verdict: **secondary** (ambient / decorative variety, not role-distinct office
  characters).
- **PerfectPixel** - a QA overlay extension for pixel-perfect comparison against
  a mockup. Verdict: **not an asset source** (QA tool only).

**Recommendation:**

- **Path A (CC0 - Kenney / OpenGameArt):** standard integration, lowest license
  friction. Recommended default.
- **Path B (LPC):** choose if richer automation / full animation is wanted and
  CC-BY-SA (attribution + share-alike on the sprite assets) is accepted.
