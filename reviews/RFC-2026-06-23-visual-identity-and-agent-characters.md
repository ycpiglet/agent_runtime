---
type: rfc
id: RFC-2026-06-23-visual-identity-and-agent-characters
audience: owner
status: proposal
signal: decide
tags: [rfc, ui, visual-identity, agent-characters, office-map, insight-graph, avatars, design-tokens]
supersedes_context: HANDOFF-2026-06-15-ui-redesign-and-product-structure.md (sub-project #3)
---

# RFC — Visual Identity & Agent Characters

Proposal for the Owner to pick a direction. **Docs only — no code in this PR.**
Backs deferred sub-project **#3** from the 2026-06-15 UI handoff.

## Bottom Line

- Two of the three pieces flagged in 2026-06-15 have **already moved**: the typography
  drift is tokenized (`TASK-AR-581/583`, full `--all-ui` literal audit passes), and
  the radial 0-edge graph is **replaced** by token-driven Dagre layered layouts +
  d3-force agent maps with non-color-only status encoding (`TASK-AR-584/588`).
  Agents already have **deterministic self-hosted DiceBear Identicon avatars**
  with per-role accent (`TASK-AR-587`).
- The genuinely open piece is the **2.5D office-map characters**: the Office Map is
  still a **flat grid of sprite badges**, not the cute game-piece characters the
  Owner asked for. This RFC is mostly a decision about **how far to push character
  identity** without breaking the accepted Linear-like operator-console house style
  or taking on licensing/asset risk.
- **Recommendation: Option 2 (token-driven layered character system, experimental
  tier).** Extend the existing self-hosted, deterministic avatar approach into a
  small 2.5D office sprite set built from primitives (no licensed IP, no external
  art pipeline), gated behind the maturity-tier RFC path. Keep the dense operator
  console as the default; characters are an *opt-in delight layer*, not load-bearing.

## Problem

2026-06-15 called out three visual gaps. Current reality:

| 2026-06-15 gap | Status today |
| --- | --- |
| 309 hardcoded font-sizes / typography drift | **Closed.** Semantic type/spacing/radius scale in `ui_design_assets.UI_TOKEN_SCALE_CSS`; `design_system_gate --all-ui` findings=0 (AR-581/583). |
| Radial node-link graph, 226 nodes, 0 edges, no insight | **Largely closed.** `patternSvgLayeredDagreLayout` (Dagre 3.0.0, MIT, vendored) + `patternSvgForceAgentLayout` (d3-force 3.0.0, ISC, vendored); status via glyph/text + health/magnitude classes, never color-only; active-taskset subgraph rendered by default (AR-584/588). |
| 2.5D game-piece / Pokemon / Mario office characters | **Open.** Office Map is a flat `office-map-grid` of `office-agent-sprite` badges with presence border colors — functional, not the desired characters. |

So the remaining product question is **character identity for the office map** —
and how much *delight* to add to a console whose accepted identity (DESIGN.md) is
deliberately dense, calm, and "not a game".

Two real tensions:

1. **House-style consistency.** DESIGN.md: "do not make the UI feel like a chat
   app", density over decoration. Cute characters pull the other way.
2. **Asset / licensing risk.** Pokemon/Mario are illustrative references, **not
   usable IP**. Any character set must be original, licensing-safe, and (per the
   AR-587/588 precedent) **self-hosted with a recorded vendor boundary** — no CDN,
   no scraped sprites.

## Proposed direction

Treat character identity as an **extension of the existing avatar system**, entering
through the maturity-tier path so novelty is *labelled, not load-bearing*
(DESIGN-SYSTEM.md "experimental" tier + New Design Proposal path).

### Visual-identity principles (consistent with the accepted house style)

- **One identity, two densities.** The operator console stays the default dense
  surface; the Office Map is the *expressive* surface. Same tokens, different
  composition — not a second design language.
- **Deterministic + token-driven, like AR-587.** A character is derived
  deterministically from the agent seed (role + id), colored from the existing
  per-role accent tokens. Same agent = same character, every render, offline.
- **Functional personality, not demographic.** Character variation encodes *role
  and state* (planner / coder / reviewer / qa; working / waiting / blocked /
  reviewing), echoing the research guidance that persona diversity should be
  epistemic/functional, never demographic
  (`RESEARCH-2026-06-14-agent-org-design-references.md`).
- **Status never color-only.** Carry the AR-588 rule into characters: presence and
  action shown via glyph + label + pose, not hue alone (accessibility + theme
  parity).

### Asset approach (licensing-safe, token-driven)

- **Build from primitives, not licensed art.** A 2.5D sprite is composed from a
  small SVG part library (body silhouette + role hat/tool glyph + state badge),
  assembled deterministically — the same self-contained generator pattern as
  `patternAgentAvatar`. No external IP, no art pipeline, no runtime network.
- **Self-hosted vendor boundary if any lib is used.** If an isometric/sprite helper
  is wanted, vendor it locally with a recorded license row (the AR-588 `dagre`/
  `d3-force` precedent: MIT/ISC, served from `/vendor/...`, no CDN).
- **Office Map remains a one-off DOM placement layer** (already noted as a residual
  geometry debt in DESIGN-SYSTEM.md); the *character* becomes a reusable
  `pattern_component` (`patternAgentCharacter`) at `experimental` tier, promoted to
  `stable` only after two-view adoption + visual verification.

### Insight-driven graph (mostly done — finish, don't rebuild)

The graph replacement is shipped; remaining polish is incremental: surface
**critical-path / blocked-chain / swimlane** *views* on top of the existing Dagre
layout (e.g., highlight the longest blocked chain feeding a cockpit RISK item),
reusing `graphEdgeHealth`/`graphEdgeMagnitudeBucket`. No new vendor surface.

## Scope / phases (rough sizing)

| Phase | Scope | Size |
| --- | --- | --- |
| P1 - Design Exploration RFC acceptance | Run the formal New Design Proposal path: problem, 2-3 references, token delta, new pattern components, a11y/density/responsive criteria. Owner accepts/rejects character direction. | S (docs) |
| P2 - `patternAgentCharacter` (experimental) | Deterministic SVG part library + generator (body/role/state), token-driven, behind Office Map only. Reuses AR-587 generator pattern. | M |
| P3 - Office Map composition | Replace flat sprite badges with characters + presence/action poses; keep DOM placement as the one-off geometry layer. | M |
| P4 - Graph insight views | Critical-path / blocked-chain / swimlane overlays on existing Dagre layout, cross-linked from cockpit RISK/BLOCK items. | M |

P1 is a pure decision gate; nothing downstream proceeds without Owner acceptance of
the character direction.

## Risks / open questions

- **Tone clash with the operator console.** Cute characters risk undercutting the
  "control room, not toy" identity. Mitigation: characters are confined to the
  Office Map (opt-in expressive surface), never the dense work surfaces.
- **Effort vs. payoff.** Characters are delight, not decision-critical; sub-project
  #1 (cockpit) likely has higher operator ROI. This may be the lowest-priority of
  the three RFCs.
- **Asset scope creep.** A bespoke sprite system can balloon. Bound it to a tiny,
  deterministic primitive set; resist per-agent custom art.
- **Open:** is the Office Map worth keeping at all, or should agent presence fold
  into the (already-shipped) live d3-force agent map? The Owner may prefer one
  presence surface over two.

## Recommendation

Adopt **Option 2: token-driven layered character system at `experimental` tier**,
**but sequence it last** of the three RFCs. Greenlight **P1 (the Design Exploration
RFC)** only — make the character direction an explicit Owner accept/reject decision
before any sprite work. Typography and the insight graph are already done; the
remaining graph polish (P4) can proceed independently and cheaply since it reuses
the shipped Dagre/force layer with no new vendor surface.
