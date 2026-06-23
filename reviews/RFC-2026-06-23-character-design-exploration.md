---
type: rfc
id: RFC-2026-06-23-character-design-exploration
audience: owner
status: proposal
signal: decide
tags: [rfc, ui, design-exploration, agent-characters, office-map, avatars, design-tokens, experimental-tier]
parent_rfc: RFC-2026-06-23-visual-identity-and-agent-characters.md (P1)
supersedes_context: HANDOFF-2026-06-15-ui-redesign-and-product-structure.md (sub-project #3)
---

# RFC — Character Design Exploration (P1 decision gate)

Formal **Design Exploration RFC** for agent-character / visual-identity direction.
This is the greenlit **P1** of `RFC-2026-06-23-visual-identity-and-agent-characters.md`:
an explicit **accept/reject artifact BEFORE any sprite implementation**. It runs the
New Design Proposal path from `DESIGN-SYSTEM.md` so novelty enters *labelled, not
load-bearing*. **Docs only — no code in this PR.**

## Bottom Line

- The Office Map is the one **open** visual surface (typography and the insight
  graph are already shipped — AR-581/583/584/588). The product question is narrow:
  **how far to push agent-character identity** on the Office Map without breaking the
  accepted "control room, not toy" house style (`DESIGN.md`) or taking licensing/asset risk.
- This RFC offers **three concrete, decision-ready options** — A: a seated "desk"
  sprite extending the AR-587 avatar; B: flat geometric 2.5D isometric pieces; C: role-silhouette
  badges — each built **only from SVG primitives** (no third-party IP), **token-driven**
  (house palette/accents), **zero runtime deps**, **accessible** (not color-only), and
  **deterministic per agent**, mirroring `patternAgentAvatar`.
- **Recommendation: Option A** (seated desk sprite that *wraps* the existing avatar) at
  the **`experimental` tier**, scoped behind the Office Map only, via the phased path
  exploration → spike → adopt, gated by `design_system_gate` + this Design Exploration
  RFC's acceptance before any sprite code lands.

## Problem

`DESIGN.md` is deliberately dense and calm: "do not make the UI feel like a chat app",
density over decoration. The 2026-06-15 handoff (sub-project #3) asked for cute
2.5D "game-piece / Pokemon / Mario" office characters. The Office Map today is a
**flat grid of `office-agent-sprite` badges** with presence-border colors — functional,
not characterful. The parent RFC closed the typography and graph gaps and landed on the
Office Map as the only remaining surface, but it deferred the actual *visual* decision to
this exploration. Two standing constraints frame every option below:

1. **House-style consistency.** Characters must read as an *opt-in delight layer* on one
   expressive surface, not a second design language bleeding into the dense work surfaces.
2. **Asset / licensing risk.** Pokemon/Mario are illustrative references, **not usable IP**.
   Any set must be original and self-hosted, following the AR-587/588 precedent.

## Goal & constraints

The character system must satisfy all of the following (non-negotiable; carried from
`patternAgentAvatar` / AR-587 and the AR-588 vendor boundary):

| Constraint | Requirement |
| --- | --- |
| Licensing-safe | Built from SVG primitives in-repo (rects/circles/polygons/paths), like AR-587. **No third-party IP**, no scraped sprites, no external art pipeline. Any helper lib vendored locally with a recorded license row (AR-588 precedent: MIT/ISC, `/vendor/...`, no CDN). |
| Token-driven | Color comes only from the house palette + per-role accent tokens (`--primary/--teal/--violet/--success/--warning`, `_AVATAR_ROLE_ACCENT`). No raw literals outside the token layer (`design_system_gate --all-ui` must stay findings=0). |
| Zero runtime deps | Self-contained generator emitting a static SVG string; no runtime network, no canvas/WebGL, offline-deterministic. |
| Accessible | Status/role/presence shown via **glyph + label + shape/pose**, never hue alone (AR-588 non-color-only rule); `<title>` for SR; AA non-text contrast in both themes. |
| Deterministic per agent | Same agent seed (role + id) → byte-identical SVG every render (the AR-587 FNV-1a + xorshift32 seed pattern). |

## Direction OPTIONS

Three concrete directions, lowest-novelty first. Each reuses the AR-587 generator
shape (seed → deterministic parts → token fills) so the *engine* is shared even where
the silhouette differs.

### Option A — Seated "desk" sprite (extend the AR-587 identicon-avatar)

The existing circular identicon avatar becomes the **head/identity token** of a small
seated figure at a desk. Body, desk, and a role tool-glyph are added as primitive layers
*around* the unchanged avatar; a state badge rides the corner.

```
   .--.        <- existing patternAgentAvatar (identicon disc), unchanged
  ( ## )       <- role accent ring (per-role token)
   |  |        <- shoulders/torso: 1 rounded-rect, accent-tinted
  /----\       <- desk: 1 rect + top edge line (--line-strong)
 [::] [o]      <- role tool glyph (laptop/wrench/clipboard) + state badge (•/||/!/eye)
```

- **Generated from primitives:** `patternAgentCharacter(seed, role, state)` calls
  `patternAgentAvatar` for the disc, then appends ~4–6 primitive shapes (torso rounded-rect,
  desk rect + edge line, role glyph from a tiny dict like the Lucide subset already in the
  module, corner state badge). All fills are existing tokens; pose/glyph encode state.
- **Pros:** Maximum reuse — head is literally the shipped avatar, so identity is already
  deterministic, licensing-safe, and theme-correct. Reads as "an agent at a workstation"
  (the Office Map metaphor) without inventing a new art language. Smallest token delta (likely zero).
- **Cons:** Less overtly "cute/game-piece" than the Owner's Pokemon/Mario framing — it's a
  tasteful operator-console character, not a mascot.
- **Effort tier:** experimental → low-M (one generator wrapping an existing one).
- **DESIGN.md fit:** Strong. Stays "control room" in tone; delight is structural (workstation
  metaphor), not decorative. Confined to the Office Map expressive surface.

### Option B — Geometric 2.5D isometric pieces

Each agent is a small isometric token (think a labelled board-game piece / desk pod), drawn
as flat-shaded isometric primitives — no figure, just a stylized place at a desk.

```
      ___
     /   \      <- iso top face (accent-tinted, --*-soft)
    / ID  \     <- agent disc/initials on the top face
    \_____/
    |     |     <- two side faces (panel + panel-strong) for the 2.5D illusion
    |__·__|     <- state dot + label slot
```

- **Generated from primitives:** three polygons per piece (top + two sides) for the iso solid,
  plus the avatar disc on the top face and a glyph/label for state. A fixed iso projection
  (2:1) computed in-generator; deterministic placement and tint per seed.
- **Pros:** Cleanly "2.5D office" and visually distinct from the dense work surfaces; scales to
  a crowded map (small, uniform footprint); flat-shaded so it stays calm.
- **Cons:** Larger new-pattern surface (iso math + faces) than A; introduces a *new* visual idiom
  (isometric) not present elsewhere in the console, so higher house-style drift risk; may need a
  small token delta for the two side-face shades.
- **Effort tier:** experimental → M.
- **DESIGN.md fit:** Moderate. Attractive but adds an idiom; needs care to not read as a generic
  SaaS dashboard widget. Acceptable only if firewalled to the Office Map.

### Option C — Role-silhouette badges

Keep today's flat badge layout but replace the plain border-color sprite with a **role silhouette**
(planner / coder / reviewer / qa) inside the badge — a single primitive path per role plus the
state encoding. No figure, no desk, no isometry.

```
 ( ◐ planner )   ( ▣ coder )   ( ✓ reviewer )   ( ◎ qa )
   • working       || waiting      ! blocked        eye reviewing
```

- **Generated from primitives:** one silhouette path per role from a tiny dict; reuse the avatar
  disc as backdrop; state via glyph + label. Essentially today's badge + a role glyph + the
  non-color-only state rule.
- **Pros:** Lowest effort and lowest risk; almost entirely a glyph/label upgrade to the existing
  sprite; trivially accessible; zero token delta.
- **Cons:** Least "character" of the three — closest to the current state, so it may not satisfy the
  Owner's ask for actual office characters. Limited delight payoff.
- **Effort tier:** experimental → S.
- **DESIGN.md fit:** Strong but minimal — arguably *too* conservative to count as "characters".

## Recommendation

**Adopt Option A (seated desk sprite wrapping the AR-587 avatar) at the `experimental` tier.**
It is the best balance of the Owner's character ask against the accepted house style and the
reuse-by-default contract: the head is the *already-shipped* deterministic avatar, so identity,
licensing-safety, theme-correctness, and determinism come for free; the added delight is the
workstation metaphor, which is on-message for an operator console rather than a toy. Option C is the
fallback if the Owner wants near-zero risk; Option B only if the Owner explicitly wants a distinct
isometric idiom and accepts the larger surface.

Enter via the maturity-tier path as a new `pattern_component` `patternAgentCharacter`, **scoped behind
the Office Map only** (never a load-bearing shared dependency), promoted to `stable` only after
two-view adoption + `visual_verification` (desktop + mobile), per `DESIGN-SYSTEM.md`.

### Phased path (exploration → spike → adopt) with gate

| Phase | Scope | Gate to advance |
| --- | --- | --- |
| Exploration | **This RFC.** Options, constraints, recommendation. | **Owner ACCEPT/REJECT of a direction** (the decision block below). |
| Spike | Build `patternAgentCharacter` (experimental) for Option A only; render behind the Office Map; capture desktop+mobile `visual_verification`. | `design_system_gate --check` findings=0; assetization_classification recorded; visual evidence attached. |
| Adopt | Replace flat sprite badges on the Office Map; keep DOM placement as the one-off geometry layer (existing residual debt). Consider promotion to `stable` after a second view adopts the pattern. | Two-view adoption + stable-API + visual-regression clean (the steward's promotion criteria). |

**Gate summary:** no sprite code lands without (1) Owner acceptance of this RFC and (2) a green
`design_system_gate`. Promotion past `experimental` additionally requires the steward's adoption +
stability + evidence criteria.

## Risks / open questions

- **Tone clash** with the operator console. Mitigation: characters confined to the Office Map;
  dense work surfaces untouched.
- **Asset scope creep.** Bound to a tiny deterministic primitive set (one role-glyph dict, one
  state-badge dict); resist per-agent bespoke art.
- **Effort vs. payoff.** Characters are delight, not decision-critical; per the parent RFC this is
  the lowest-priority of the three sub-projects and should sequence last.
- **Open:** Is the Office Map worth keeping at all, or should agent presence fold into the
  already-shipped live d3-force agent map? If the Owner prefers a single presence surface, REJECT and
  retarget the character pattern onto that map instead.

## Decision

The Owner is asked to **ACCEPT or REJECT** exactly one outcome:

| Option | What accepting it commits to | What it does NOT commit to |
| --- | --- | --- |
| **ACCEPT Option A (recommended)** | Authorize a Spike of `patternAgentCharacter` (experimental, Office-Map-only) wrapping the AR-587 avatar into a seated desk sprite, gated by `design_system_gate`. | Any promotion to `stable`; any change to dense work surfaces; any new vendor/CDN dependency. |
| ACCEPT Option B | Same as A but for the isometric piece system (larger surface; possible small side-face token delta). | Same exclusions as above. |
| ACCEPT Option C | Same as A but for the role-silhouette badge upgrade (smallest scope). | Same exclusions as above. |
| **REJECT all** | No sprite work proceeds; Office Map stays as-is, or agent presence folds into the existing d3-force agent map (open question above). | — |

Default if no objection: **ACCEPT Option A**, experimental tier, sequenced last of the three
visual-identity sub-projects.
