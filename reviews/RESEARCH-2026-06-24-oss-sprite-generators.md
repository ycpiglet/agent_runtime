---
title: OSS Game-Character-Sprite Generators for the Office Map — Research & Recommendation
status: synthesized (license + animation facts fetched from primary sources this run; integration sketch is design, not yet spiked)
date: 2026-06-24
tags: [research, ui, office-map, agent-characters, sprites, animation, licensing, oss, design-tokens]
parent_rfc: RFC-2026-06-23-character-design-exploration.md
relates_to: RESEARCH-2026-06-20-ui-ux-visual-resources.md (Character strand), TASK-AR-587 (DiceBear avatars)
---

# RESEARCH — OSS Sprite Generators for Cute, Role-Distinct, Animated Office-Map Characters

Decision-ready recommendation for which **open-source game-character-sprite generator
(with animation support)** to use to produce cute, role-distinct agent sprites for the
console Office Map, integrated at the **"standard"** maturity tier. **Docs only — no UI
code in this PR.** Reads as a follow-on to the parent Character-Design-Exploration RFC,
which deferred the *external generator vs. in-repo SVG primitives* question; the Owner has
since asked specifically for **animation support**, which reframes the choice toward real
spritesheet generators.

## Bottom Line

- **Recommendation: the Universal LPC Spritesheet Character Generator (LPC).** It is the
  only mature OSS option that is simultaneously a real **generator** (modular parts +
  palette/variant selection → role-distinct characters), genuinely **animated** with a
  dedicated **IDLE** animation plus walk/run/cast/slash/etc., and in the right cute,
  Game-Boy-era / classic-RPG **pixel idiom**. It outputs **64×64 PNG spritesheets** that
  self-host and animate in the console with **pure CSS `steps()`** — zero runtime deps,
  deterministic, accessible — fitting the build-less console exactly.
- **The catch is licensing (copyleft).** The generator *code* is **GPL-3.0**; its *art
  assets* are mostly **CC-BY-SA 3.0** (with a mix of CC0 / CC-BY / OGA-BY / GPL per asset).
  This imposes **bounded** obligations on the **committed sprite files** (attribution +
  share-alike on the PNG derivatives), but — per the LPC project's own FAQ — **using the
  sprites inside the console does NOT make the console a derivative**. The copyleft does
  not "infect" `ui_console.py` or the design system; it travels with the asset files only.
- **Fallback (pure CC0): DiceBear `pixel-art` (CC0, the AR-587 prior art) for identity +
  Kenney CC0 sprites for motion.** Fully permissive, no attribution, but **less rich**:
  DiceBear pixel-art is a *static* half-body avatar (no frame animation), and Kenney's
  packs are CC0 but not modular / not cutely role-distinct in the same RPG idiom — so
  role distinction must be hand-authored via palette swaps rather than generated.
- **Owner DECISION POINT (below):** accept **bounded CC-BY-SA attribution + share-alike on
  the sprite asset files** to get a true animated, role-distinct generator (LPC), **or**
  insist on **pure CC0** and accept a less rich, more hand-built character set. This is the
  one judgment only the Owner should make; everything else (integration, tiering, a11y) is
  settled below.

## Signal

| Metric | State | Evidence |
| --- | --- | --- |
| Candidates evaluated | 5 | LPC, DiceBear pixel-art (+CC0 sprite), Kenney CC0, Mana Seed, Cute Fantasy RPG |
| Meets ALL hard asks (cute/GB + role-distinct generation + IDLE/state animation) | 1 | **LPC** (the only true animated *generator*) |
| Redistribution-safe for a **public** repo commit | 3 of 5 | LPC ✓, DiceBear ✓, Kenney ✓ / Mana Seed ✗, Cute Fantasy free-tier ✗ |
| Pure CC0 (no attribution) AND animated | 0 | trade-off is real: CC0 picks are static or non-modular |
| Runtime cost of chosen integration | zero JS deps | CSS `steps()` + `background-position` on self-hosted PNG |

## Insight

### What the asks actually require

The Owner's bar has three hard requirements that together are surprisingly selective:

1. **Cute / Game-Boy-era / classic-RPG pixel feel ("아기자기").**
2. **Role-distinct via *generation*** — not 4 hand-drawn characters, but a modular/palette
   system that yields planner / coder / reviewer / qa variants from parts.
3. **IDLE / state ANIMATION** — the Owner explicitly wants animation, i.e. real
   multi-frame idle/walk/state frames, not a static portrait.

Requirement (3) is what rules out the repo's current trajectory. The parent RFC
(`RFC-2026-06-23-character-design-exploration.md`) recommended **in-repo SVG primitives**
(Option A, seated desk sprite). That is licensing-perfect and zero-dep, **but it is a
static composition** — it satisfies (1) and (2) but not (3) without us hand-authoring a
keyframe animation system from scratch. The animation ask is the reason to look at real
spritesheet generators at all.

### Candidate comparison

| Candidate | License (code / assets) | Animation (idle/walk/state) | Style fit (cute / GB) | Role-distinct generation | Web integration | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| **Universal LPC Spritesheet Generator** | Code **GPL-3.0**; assets **CC-BY-SA 3.0** mixed w/ CC0/CC-BY/OGA-BY/GPL | **Strong.** 64×64, 4-dir, dedicated **Idle** + Walk/Run/Jump/Sit/Cast/Slash/Thrust/Shoot/Hurt/Climb (LPC 3.0) | **Strong.** Canonical classic-RPG pixel look | **Strong.** Modular parts (body/hair/hat/tool/clothes) + variants → recolorable role kits | **PNG spritesheet → CSS `steps()`** self-host; zero runtime dep | **Copyleft + per-asset attribution on committed PNGs** (bounded; see decision) |
| **DiceBear `pixel-art` (+ a CC0 motion sprite)** | Lib **MIT**; `pixel-art` style **CC0** | **Weak.** Static half-body SVG — **no frame animation** | Good (8-bit pixel) but **portrait**, not a walking game piece | Seeded variation, but **identity only**, not role poses | Already vendored (AR-587); add CSS only if paired w/ a motion sprite | Low license risk; **misses the animation ask** alone |
| **Kenney CC0 packs** | **CC0** (no attribution) | Some packs animated (walk/idle) | Mixed; often chunkier / not the cute 16px RPG idiom | **Not a generator** — fixed sprites; role = manual palette swap | PNG → CSS `steps()` | Low license risk; **not modular, weaker style fit, manual role work** |
| **Mana Seed "Character Base" (Seliel)** | **Custom license** (NOT CC0) | **Strong** (rich modular animations) | **Excellent** cute RPG | Excellent modular system | Would be PNG → CSS | **DISQUALIFIED for public repo:** license **forbids redistributing raw assets** (can't commit to a public repo); also bans blockchain |
| **Cute Fantasy RPG (Kenmi)** | Custom (free non-commercial / $ premium) | **Strong** (~20 anims, has a Player Generator) | **Excellent** cute 16px | Good (generator + 8 NPCs) | Would be PNG → CSS | **DISQUALIFIED for public repo:** "can't be resold or **redistributed even if modified**" — can't commit assets |

Two attractive cute generators (**Mana Seed**, **Cute Fantasy RPG**) are eliminated not on
style but on **redistribution**: their licenses forbid committing the (even modified) asset
files to a public repo. For a workflow where derivative spritesheets live in the
repository and ship in an OSS console, that is a hard stop. LPC's CC-BY-SA, by contrast,
*permits* redistribution precisely *because* it requires share-alike + attribution.

### Why LPC clears the bar where others don't

- **It is a generator, not a pack.** Self-hostable (`npm run dev` / `npm run build`,
  Vite); pick body + hair + hat + tool + clothes + a palette, export a per-character PNG
  spritesheet. That is exactly the "modular parts + palette swap → role-distinct" mechanism
  the Owner asked for: a **planner** in a cloak with a clipboard, a **coder** with a
  laptop/wrench glyph and a teal palette, a **reviewer** with an eye/scroll, a **qa** with a
  checklist — all from the same base with different parts/palettes.
- **It has a real IDLE animation** (LPC 3.0), plus walk and a full action set, in 4
  directions, one animation per row at 64×64 — i.e. drop-in spritesheet rows we can map to
  console states.
- **It exports the attribution we'd owe** — the generator emits a **CSV/TXT credits file**
  (or the repo's `CREDITS.csv`) listing author + license + source per selected asset,
  which is exactly what CC-BY-SA requires. The obligation is mechanically satisfiable.

### The copyleft obligation, precisely (so the Owner can judge the real cost)

From the LPC project's own attribution guidance and the CC-BY-SA terms:

- **A derivative = the artwork itself.** A recolored / part-composed spritesheet we export
  *is* a derivative of the CC-BY-SA source assets, so each **committed PNG** (and its
  source/palette recipe) must be released **CC-BY-SA (4.0+)** and ship with **attribution**
  (author, license, source URL per contributing asset) and **no DRM/encryption** on it.
- **The console is NOT a derivative.** "Putting an SA asset into a program, game, or any
  other kind of application does NOT make that application a derivative." So `ui_console.py`,
  the design tokens, and the rest of the codebase keep their existing license; the copyleft
  is **scoped to the asset files**, not the app.
- **Concrete obligation if we adopt LPC:**
  1. Commit the generated spritesheets under a clearly-licensed asset path (e.g.
     `.../assets/characters/lpc/`) with a co-located `CREDITS.csv` + a `LICENSE` note
     stating the sprites are CC-BY-SA 3.0/4.0.
  2. Surface the credit in-product (e.g. an "Art credits" line in the Office Map about/help)
     and in the repo's NOTICE/attribution doc.
  3. Record the vendor boundary the same way AR-588 did for `dagre`/`d3-force`
     (self-hosted, no CDN, recorded license row) — here the row is **CC-BY-SA**, not MIT.
  4. Avoid mixing in any **GPL-only** LPC assets if we want to keep the asset license to
     CC-BY-SA (the generator marks per-asset licenses; prefer CC-BY-SA/CC-BY/CC0 assets so
     the GPL asset license doesn't attach to the PNGs).

This is real but **bounded and mechanical**: attribution files + an asset-license note +
the existing self-host discipline. It does not constrain how we build or license the
console itself.

### Animation & integration are settled regardless of pick

Whichever PNG-spritesheet option wins, the console drives animation with **pure CSS** — the
build-less, zero-runtime-dep path that matches the design system:

- `image-rendering: pixelated` (crisp-edges) to keep pixels sharp when scaled.
- `background-image: url(<self-hosted spritesheet>)`, sized to one 64×64 frame.
- `@keyframes` stepping `background-position` across a row with
  `animation: <row> <dur> steps(<frames>) infinite;` — one row = one state.
- **Idle** by default; switch the keyframe/row on **hover** (`:hover`) or on a state class
  (`.is-working` / `.is-waiting` / `.is-blocked` / `.is-reviewing`) toggled from the
  existing agent-state data. Use `steps(...) forwards` for one-shot transitions.
- **Accessible, not color-only** (carry the AR-588 rule): pair the animated pose with a
  glyph + text label + `<title>`/`aria-label`, so state never depends on hue or motion
  alone; respect `prefers-reduced-motion` by falling back to a single idle frame.
- **Deterministic:** the spritesheets are static committed files (no runtime generation),
  so every render is byte-identical and offline — same property AR-587 gave avatars.

## Decision

The integration, tiering, animation mechanism, and accessibility rules are settled above.
The **one** open question is licensing, and it is genuinely the Owner's call.

| Option | What accepting it commits to | What you get | What it costs |
| --- | --- | --- | --- |
| **ACCEPT LPC (recommended)** | Adopt the Universal LPC Spritesheet Generator; commit CC-BY-SA spritesheet derivatives + `CREDITS.csv` + an asset-license note; surface art credit in-product; record a CC-BY-SA vendor row. | A true **animated, modular, role-distinct, cute** classic-RPG character set with a dedicated **IDLE** animation — meets every hard ask. | **Bounded copyleft on the sprite files only:** attribution + share-alike on the committed PNGs (not on the console); a small standing maintenance duty to keep credits current. |
| ACCEPT CC0-only fallback | Use DiceBear `pixel-art` (CC0) for identity + Kenney CC0 sprites for motion; hand-author role distinction via palette swaps. | **Pure CC0**, no attribution, zero license maintenance. | **Less rich:** no real generator, weaker cute-RPG style fit, manual role authoring, and animation only as good as the chosen CC0 motion pack. |
| REJECT external generators | Stay with the parent RFC's in-repo SVG-primitive seated sprite (Option A). | Maximum license purity + zero new assets. | **Does not deliver frame animation** without us building a keyframe system by hand — i.e. does not meet the Owner's animation ask. |

**Default if no objection:** **ACCEPT LPC** at the **standard** tier, with the bounded
CC-BY-SA obligations applied to the committed sprite assets only. Choose the **CC0
fallback** only if the Owner wants zero attribution/share-alike obligations and accepts a
less rich, more hand-built result.

## Action Board

| # | Action | Owner | Gate |
| --- | --- | --- | --- |
| 1 | Owner picks **LPC** vs **CC0 fallback** (the decision table above). | Owner | This doc |
| 2 | If LPC: self-host the generator locally; author 4 role kits (planner/coder/reviewer/qa) via parts + house-palette swaps; export 64×64 spritesheets + `CREDITS.csv`. | sprite/asset agent | `design_system_gate` |
| 3 | Commit sprites under a clearly CC-BY-SA-licensed asset path with co-located credits + license note; record the vendor row (AR-588 pattern). | asset agent | owner_governance_gate |
| 4 | Wire CSS `steps()` idle/state animation into the Office Map at **standard** tier; map rows→states; add a11y (glyph+label+`<title>`, `prefers-reduced-motion`). | UI agent | `design_system_gate --check` findings=0; visual_verification (desktop+mobile) |
| 5 | Defer fine art polish (Owner said polish later); ship the role-distinct animated baseline first. | UI agent | — |

## Risks / Blockers

- **Copyleft maintenance drift.** If we add/swap LPC parts later, `CREDITS.csv` must be
  regenerated or attribution falls out of date. Mitigation: keep the generation recipe +
  credits export co-located with the PNGs; treat credits as part of the committed asset.
- **Accidental GPL-only assets.** Some LPC parts are GPL, not CC-BY-SA; selecting them
  would attach GPL to the PNG. Mitigation: prefer CC-BY-SA/CC-BY/CC0 parts; the generator
  labels per-asset licenses.
- **Tone clash with the operator console.** Same risk the parent RFC flagged: cute sprites
  vs "control room, not toy." Mitigation: confine characters to the Office Map expressive
  surface; never the dense work surfaces.
- **Style cohesion vs. the existing DiceBear identity.** LPC sprites and DiceBear identicon
  avatars are different idioms; decide whether LPC *replaces* the office sprite or the
  DiceBear avatar remains the "head"/profile identity while LPC is the office body.
- **Scope creep.** Bound the initial set to 4 role kits × {idle, one state pose}; resist
  per-agent bespoke art (Owner deferred polish).

## Next Steps

- Owner records the licensing decision on this doc (LPC vs CC0 fallback).
- On ACCEPT-LPC: open the asset-generation task (role kits + credits) and the standard-tier
  CSS-animation integration task, gated by `design_system_gate` + `visual_verification`.
- On ACCEPT-CC0: open a task to vet a specific Kenney/CC0 animated pack for cute-RPG fit
  and author palette-swap role variants.
- Either way: keep the parent RFC's in-repo SVG seated sprite as the no-new-asset
  fallback if neither external path is approved.

## Sources

- [Universal LPC Spritesheet Character Generator (GitHub, LiberatedPixelCup)](https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator)
- [LPC Generator (live)](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/)
- [LPC Spritesheet/Character Generator Attribution Project (OpenGameArt forum — derivative vs application, credits)](https://opengameart.org/forumtopic/lpc-spritesheetcharacter-generator-attribution-project)
- [LPC Expanded: Idle, Run, Jump (OpenGameArt)](https://opengameart.org/content/expanded-universal-lpc-spritesheet-idle-run-jump-lpc-revised-combat-and-assets)
- [DiceBear — Licenses (pixel-art = CC0; library = MIT)](https://www.dicebear.com/licenses/)
- [DiceBear — Pixel Art style](https://www.dicebear.com/styles/pixel-art/)
- [Kenney — CC0 game assets (itch.io CC0 listing)](https://itch.io/game-assets/assets-cc0)
- [Mana Seed "Character Base" by Seliel the Shaper (custom license — no redistribution)](https://seliel-the-shaper.itch.io/character-base)
- [Cute Fantasy RPG by Kenmi (free/premium — no redistribution)](https://kenmi-art.itch.io/cute-fantasy-rpg)
- [CSS sprite-sheet animation with `steps()` (Treehouse)](https://blog.teamtreehouse.com/css-sprite-sheet-animations-steps)
- [CSS sprite sheet animations (leanrada — pixelated rendering, background-position)](https://leanrada.com/notes/css-sprite-sheets/)
