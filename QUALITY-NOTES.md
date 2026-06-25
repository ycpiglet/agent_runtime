# Sprite Quality Notes — v2 procedural vs real CC0 pixel art

_Spike: `claude/sprite-quality-spike`. Companion artifacts: `office-map-demo.html`
(Office Map populated with our v2 sprites), `quality-compare.html` (v2 vs real CC0
side-by-side at small + 3x), and the fetched CC0 assets in
`agents/project/assets/agent-characters/_compare-cc0/` (+ `SOURCES.md`)._

## Bottom line

**Pivot the character *body* to real CC0 pixel art; keep our theming + animation
layer.** Our v2 procedural chibi fixed the v1 "empty" complaint (warm skin/hair
fill now shows), but it has a low quality ceiling because it is **axis-aligned 8px
rectangles** with no sub-pixel shaping, outline hierarchy, or shading ramp. The
Owner's read — "better but the design intent doesn't come across" — is exactly the
symptom of code-drawn rect art: role-defining detail collapses into noise at the
~26px on-map size. Real artist CC0 art stays legible and charming at that size.

## What I compared

- **Ours (left):** the v2 SVG chibi (e.g. `lead-engineer.svg`) — 16x16 logical grid
  of 8px `<rect>` cells, fills driven by CSS vars (`--office-skin`, `--primary`, etc).
- **Real CC0 (right):** 4 artist-drawn CC0 pixel characters fetched from
  OpenGameArt.org (all verified **CC0**, attribution **not required**):
  - 8-bit RPG knight — _devurandom_
  - Simple character base — _zaphgames_
  - Classic hero "Mr. Man" — _GrafxKid_
  - RPG character — _GrafxKid_

  (Two strong candidates — *Tiny 16* and *24x32 big pack* — were **discarded**
  because they are CC-BY, not CC0.)

## Assessment by dimension

| Dimension | v2 procedural (ours) | Real CC0 art |
|---|---|---|
| **Legibility @26px** | Reads as a soft blob; details merge | Clear, readable at map size |
| **Silhouette** | Rounded mass, weak head/body separation | Crisp dark outline, distinct head/torso/limbs |
| **Shading** | Mostly flat fills | 2–3 step light/mid/dark ramps → form & depth |
| **Role readability** | Role cues (tools/badges) blur at small size | Shape-encoded identity survives downscaling |
| **Charm** | Reads as an *icon* | Reads as a *character* |
| **Animation** | CSS idle-bob only (one transform) | Source sheets ship real walk/idle frames |
| **Theming** | ✅ recolors via CSS vars (dark mode, per-room) | ❌ fixed palette PNG |
| **Coverage** | ✅ all 34 roles already exist | ❌ packs rarely ship 34 distinct role chars |
| **Resolution** | ✅ SVG, resolution-independent | needs `image-rendering:pixelated` upscale |

### Where v2 genuinely still wins
Auto-theming (CSS-var fills follow light/dark + room accent), complete 34-role
coverage today, and resolution independence. A naive "drop in PNGs" pivot would
*lose* all three — so the pivot must be a **hybrid**, not a wholesale swap.

## Recommendation — hybrid pivot

Adopt one cohesive CC0 base for the **body silhouette + shading**, and keep our
existing **theming + animation** layer on top.

### Which packs
1. **Primary: LPC (Liberated Pixel Cup) base** — large CC0/CC-BY-SA universal
   character generator with a body base, hair, and modular clothing/accessory
   layers. Use the **CC0-licensed** subset (filter the generator/credits to CC0)
   so attribution stays optional. Modular layers map cleanly to role accessories.
2. **Fallback for a smaller/lighter look:** a single CC0 16x16 base (e.g.
   *Simple character base*, zaphgames, already fetched) + a hand-authored set of
   role accessory overlays (hardhat, magnifier, clipboard, headset…).
3. Keep **GrafxKid** CC0 characters as a secondary palette of pre-made bodies for
   roles that don't need a custom accessory.

### How to map 34 roles
- Group the 34 roles into ~6–8 **archetype bodies** (engineer, analyst, designer,
  auditor/QA, ops/steward, exec/partner, research, support) — one CC0 base body
  per archetype.
- Differentiate within an archetype with a small **accessory overlay** (1–2 layers:
  a tool + a color accent) so each of the 34 roles is distinct without 34 bespoke
  drawings. This mirrors how `OFFICE_ROOMS.role_markers` already buckets roles.
- Reuse the existing role→sprite filename convention (`v2/<role>.svg` → `v3/<role>.png`
  or a manifest) so `build_office_map` placement is unchanged.

### How to animate (keep what works)
- Keep the **CSS `office-idle-bob`** transform — it already works on any element,
  PNG or SVG, and respects `prefers-reduced-motion`.
- If we want real motion, the CC0 sheets ship **walk/idle frames**; drive a 2–4
  frame loop with a CSS steps() `background-position` animation on the sprite
  element. No JS, stays ASCII-safe for the served bundle.
- **Theming:** PNGs can't recolor via CSS vars. Two options: (a) accept fixed
  palettes per role (simplest), or (b) keep the body PNG neutral and tint via a
  CSS `filter` / a recolorable accent layer for the per-room/dark-mode accent.
  Recommend (a) for the body + keep the **presence ring + word badge** (already
  CSS-var-driven) as the theming/status signal — that's the a11y-primary cue anyway.

### Migration shape (additive, low risk)
1. Land a `v3/` asset dir with the CC0 base bodies + accessory overlays + a
   `SOURCES.md`/credits manifest (CC0-only).
2. Add an opt-in flag/asset-version switch so the office map can render `v3` while
   `v2` stays as fallback.
3. Swap the `.office-agent-sprite` inner from inline SVG to `<img>`/layered
   `<div>`s; the surrounding office CSS (rings, bob, badge, tooltip) is unchanged.

## Caveat on this spike
The CC0 comparison frames were cropped from larger sheets and background-keyed to
transparent for a fair character-vs-character view; the untouched source sheets are
viewable under "full source sheet" in `quality-compare.html` and downloadable at the
URLs in `_compare-cc0/SOURCES.md`. No assets were fabricated or hand-drawn.
