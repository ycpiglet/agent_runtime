---
title: UI/UX Visual Resources for the Operator Console — Research
status: synthesized (Strands 1-2 verified; 3-5 from fetched sources + established knowledge)
date: 2026-06-20
tags: [ui, design-system, graph, avatars, fonts, icons, color, research]
---

# RESEARCH — UI/UX Visual Resources (graph · character · fonts · icons · color)

- **For:** the Agent Runtime operator console (build-less vanilla JS + server-emitted
  HTML/CSS/SVG; Linear/Notion direction; existing token/component/pattern system with
  hand-rolled SVG graph patterns, calendar grid, state-machine panel).
- **Hard constraints:** open/permissive license ONLY (OFL fonts; MIT/ISC/Apache/CC0/CC-BY
  assets); **no-build first** (vanilla JS / inline SVG / `<script>`-tag drop-ins), flag
  anything build-required.
- **Method:** deep-research fan-out (5 angles → 25 sources → 123 claims). **Strands 1
  (Graph) + 2 (Character) = 25/25 claims 3-0 verified** against primary sources. The verify
  pass (capped at 25 claims) did not reach Strands 3-5; their resources below come from this
  run's *fetched* primary sources + established knowledge — **flagged, not 3-vote-verified.**

### Legend
- **✓ verified** — 3-0 adversarial vote this run (primary source).
- **○ fetched** — a primary source was fetched this run but the specific claim wasn't re-verified.
- **◆ known** — well-established stable fact (not from this run's verified set); verify license before adopting.

## Bottom Line

Two-track adoption. **Graph:** `Dagre` (MIT, layered/Sugiyama) + a hand-rolled SVG renderer
for dependency graphs / org charts / state machines, and `d3-force` (ISC, force-directed) +
tick-driven SVG for the live agent map — both are **layout-only** engines that emit plain
`{x,y}` and render nothing, which fits the build-less SVG console exactly. **Character:**
`DiceBear` in **seeded** mode (seed = agent id) using its **CC0** styles (Notionists / Open
Peeps / Pixel Art), self-hosted. Fonts/Icons/Color: strong permissive picks below (Geist+Geist
Mono / Lucide / Radix Colors + Carbon data-viz), to confirm before adoption.

---

## STRAND 1 — GRAPH VISUALIZATION  ✓ (verified)

Render model that fits the console: pick a **layout-only** engine (emits node `{x,y}` +
edge point arrays, renders nothing) and draw your own SVG. All top picks below do this.

| Library | License | No-build? | Role | Verdict |
|---|---|---|---|---|
| **Dagre** | **MIT** ✓ | ✓ `<script>` IIFE global `dagre` | Layered/Sugiyama DAG: dependency graph, org chart, state machine | **TOP PICK (structured)** ✓ |
| **d3-force** | ISC ◆ (layout-only ✓) | ✓ UMD (confirm artifact) | Force-directed **live agent map** | **TOP PICK (organic)** ✓ |
| **elkjs** | **EPL-2.0** ✗ (weak copyleft) | ✓ `elk.bundled.js` global `ELK` | Best layered algo (ELK Layered, ports, edge direction) | **FLAG — license fails allowlist** ✓ |
| **3d-force-graph** | MIT ✓ | ✓ one CDN tag | WebGL/Three.js | **WRONG TECH — not SVG-stylable; only if scale > ~3-5k elems** ✓ |
| cytoscape.js / sigma / vis-network | MIT/ISC ◆ | partial | full render frameworks | heavier; bring their own renderer — less seam-fit than Dagre+d3-force |

**Why Dagre + d3-force:** they are the only two that are simultaneously (a) permissive
[MIT/ISC], (b) genuinely no-build [`<script>`/UMD], and (c) layout-only emitting coordinates a
server-emitted-SVG renderer can consume. ✓ Dagre uses network-simplex ranking (Gansner et al.).
✓ d3-force is a velocity-Verlet integrator that mutates `node.x/.y` and fires `tick` for you to
render. **Caveat:** Dagre is maintenance-mode under `@dagrejs/dagre` (active scoped package);
it needs a renderer — hand-roll the SVG (avoid `dagre-d3`, which pulls in D3).

**Reference designs to emulate** ✓:
- **Datadog Request Flow Map** — edge **stroke-width = request volume**, **stroke color
  redder = higher error rate**. Trivially reproducible with SVG `<path>` stroke scaled to metrics.
- **GitHub Actions visualization graph** — node = job, edges = `needs:` dependencies, a
  **status icon beside each node**, framed real-time. The exact node-link DAG + per-node status
  pattern for the live agent map / dependency / state-machine views. (Emulate the *visual*; build
  your own genuine live-push — the Actions graph often needs manual refresh.)
- Also worth a look (fetched): **Obsidian graph view** (force-directed knowledge graph) for the
  free-form map's interaction feel.

---

## STRAND 2 — CHARACTER / AGENT IDENTITY  ✓ (verified)

**TOP PICK: DiceBear, seeded mode.** ✓ Same `seed` → byte-identical SVG across sessions →
perfect for "avatar keyed to agent id/role." Library code is **MIT**, but **each style has its
own license** — so the gate is *which style*:

- **Use (CC0 1.0, zero attribution)** ✓: **Notionists** (matches the Notion-leaning aesthetic),
  **Open Peeps**, **Pixel Art**, Lorelei / Lorelei Neutral, Identicon, Initials, Thumbs, Shapes,
  Rings, Glass, Disco, Stripes, Triangles, Shape Grid.
- **Avoid / must-attribute (CC BY 4.0)** ✓: Adventurer, Big Ears, Big Smile, Croodles, Fun Emoji,
  Micah, Personas, Glyphs.
- **Non-standard license** ✓: Avataaars, Bottts ("free for personal & commercial," not OSI/CC).

**Adoption caveats** ✓: the free HTTP API (`api.dicebear.com/10.x/<style>/svg`, no key, no build)
has rate limits (50 req/s) and is requested non-commercial + no availability guarantee → **don't
depend on it at runtime; pre-generate / self-host the SVGs or use `@dicebear/*` packages.**
Determinism + license hold **only within a major version** → pin the version.

**Lightweight alternatives** (fetched ○):
- **minidenticons** ○ — MIT, ~1 kB, pure vanilla, deterministic SVG identicons. Great no-build
  fallback / for entity glyphs (task/claim/gate) where a full avatar is overkill.
- **Boring Avatars** ○ — MIT, but the official package is **React (build-required)**; use a
  vanilla port or pre-generate.

**Role differentiation (recommended pattern):** keep the seeded avatar for *identity*, then add a
**deterministic per-role accent** (ring/background) you draw in your own SVG, mapped to the
existing status/role color tokens — so role reads at a glance and stays WCAG-safe in both themes.

**Entity glyphs (task/claim/gate/evidence):** no verified option surfaced; recommend hand-rolled
SVG glyphs from your icon set + a shape/color system (see Strand 4/5) over a generator.

---

## STRAND 3 — FONTS (open/OFL)  ○ / ◆ (fetched sources; confirm OFL before adopting)

| Font | License | Use | Notes |
|---|---|---|---|
| **Geist + Geist Mono** (Vercel) | OFL 1.1 ◆ | **UI + IDs/metrics** | Built for dev tools; matches the Vercel/Linear direction already in `DESIGN.md`. **TOP PICK pairing.** Source fetched: vercel.com/font ○ |
| **Inter** | OFL 1.1 ◆ | UI/body | The battle-tested dense-dashboard sans; variable. ○ |
| **IBM Plex Sans / Mono** | OFL 1.1 ◆ | UI + mono | Carbon's typeface; technical, neutral. ○ |
| **JetBrains Mono** | OFL 1.1 ◆ | code/IDs/metrics | Excellent mono, tall x-height, optional ligatures. ○ |
| **Commit Mono** | OFL 1.1 (confirm) ○ | mono | "Anonymous," neutral mono. commitmono.com ○ |
| **Space Grotesk** | OFL 1.1 ◆ | display/headers | floriankarsten/space-grotesk ○ |

**Recommendation:** **Geist (UI) + Geist Mono (IDs/metrics/code)** — coherent, OFL, dev-tool-native,
already the stated direction. Self-host `woff2` (variable), no CDN. Battle-tested alternative:
**Inter + JetBrains Mono.**

## STRAND 4 — ICONS & ILLUSTRATION (permissive)  ○ / ◆ (confirm license)

**Icons (inline SVG, no build):**
- **Lucide** — ISC ◆. Clean stroke (~1500), Feather successor; best match for the calm
  Linear/Notion look. Drop individual SVGs inline. **TOP PICK.**
- **Phosphor** — MIT ◆. 9000+, 6 weights.  ·  **Tabler** — MIT ◆. 5000+ stroke.
- **Radix Icons** — MIT ◆. 15×15 crisp, Vercel-adjacent.  ·  **Heroicons** — MIT ◆.
- **Material Symbols** — Apache-2.0 ◆. Variable.

**Illustration / spot-art (Empty / Error / Loading / onboarding):**
- **unDraw** ○ — custom open license (free, **no attribution**, single-color **recolorable** to
  your accent token). Source fetched: undraw.co/license ○. **TOP PICK for state screens** (recolor
  to the console accent for instant on-brand empty states).
- **Open Doodles** — CC0 ◆ · **Open Peeps** — CC0 ◆ (openpeeps.com ○) — warm hand-drawn, recolorable.
- **Humaaans** — CC BY 4.0 ◆ (attribution) · **Reshot** — free/CC0-like ◆ · **Pixeltrue / IRA Design /
  Glaze** — freemium/attribution ◆ (check per-asset).

## STRAND 5 — COLOR / DATA-VIZ & "AT-A-GLANCE" PATTERNS  ○ / ◆ (confirm license)

**Palettes:**
- **Radix Colors** — MIT ◆. 12-step scales with built-in dark mode, steps mapped to roles
  (bg/border/text), APCA-tuned. Source fetched ○. **TOP for UI surface + status colors**; aligns
  with the existing semantic token model.
- **IBM Carbon data-viz palettes** — Apache-2.0 ◆. Categorical (up to 14) + sequential + diverging,
  **dark & light variants, purpose-built for charts/graphs.** Source fetched ○. **TOP for the
  GRAPH node/edge categorical colors.**
- **ColorBrewer** — free ◆. Gold-standard sequential/diverging/qualitative, colorblind-safe sets.
- **Observable Plot / d3-scale-chromatic** — ISC ◆ (Tableau10, viridis…). · **Open Color** — MIT ◆.

**Intuitive at-a-glance (open, no-build):**
- **fnando/sparkline** ○ — MIT, tiny vanilla SVG sparklines, drop-in. Source fetched ○. **TOP for
  inline trends** (agent load, throughput, gate pass-rate).
- Status glyphs / badges / micro-heat: hand-rolled SVG + Lucide + status tokens. Keep the
  `DESIGN.md` rule — **shape + color + label, never color alone.**

---

## Consolidated shortlist

**ADOPT NOW (permissive, no-build, drop-in):**
- **Dagre** (MIT) + hand-rolled SVG renderer → dependency graph / org chart / state machine.
- **d3-force** (ISC) + tick-rendered SVG → live agent map.
- **DiceBear** seeded, **CC0 styles** (Notionists / Open Peeps / Pixel Art), self-hosted → agent avatars.
- **Lucide** (ISC) icons · **unDraw** (recolorable) empty/error states · **fnando/sparkline** (MIT) trends.
- **Geist + Geist Mono** (OFL) fonts · **Radix Colors** + **Carbon data-viz** palettes.

**BUILD-REQUIRED / LATER:**
- **elkjs** — best layered algorithm + drop-in bundle, but **EPL-2.0** (weak copyleft) → only if acceptable.
- **3d-force-graph** — MIT + CDN, but **WebGL not SVG** → only if graph scale outgrows the ~3-5k-element SVG sweet spot.
- **Boring Avatars** — MIT but React → vanilla-port or pre-generate.

## Starter recommendations
- **Agent avatars:** DiceBear **Notionists** (CC0), `seed = agent id`, + a deterministic per-role
  accent ring drawn in your SVG from the role/status tokens; pre-generate + self-host SVGs; pin the DiceBear major version.
- **Dependency / agent graph:** **Dagre** top-to-bottom (or L-R) layered DAG → your own SVG, with
  **Datadog edge encodings** (stroke-width = magnitude, color = health) + **GitHub-Actions per-node
  status icons**; reserve **d3-force** for the free-form live agent map.

## Open items (for a follow-up pass if wanted)
Strands 3-5 specifics weren't 3-vote-verified this run (search/fetch hit them; verify pass capped
at 25 and prioritized Graph+Character). A short follow-up could verify the exact OFL terms +
no-build artifacts for the font pairing, the icon/illustration licenses, and the palette licenses.
Also unresearched: entity-glyph systems for task/claim/gate/evidence, and `mermaid` as a
no-build state-machine option.

## Sources (primary, fetched this run)
Graph: github.com/dagrejs/dagre ✓ · d3js.org/d3-force/simulation ✓ · github.com/kieler/elkjs ✓ ·
eclipse.dev/elk/.../org-eclipse-elk-layered ✓ · github.com/vasturiano/3d-force-graph ✓ ·
datadoghq.com/blog/apm-request-flow-map-datadog ✓ · docs.github.com/actions/.../visualization-graph ✓ ·
deepwiki obsidian graph-view ○. Character: dicebear.com/licenses ✓ · dicebear.com/how-to-use/http-api ✓ ·
github.com/laurentpayot/minidenticons ○ · github.com/boringdesigners/boring-avatars ○. Fonts:
vercel.com/font ○ · jetbrains.com/lp/mono ○ · fonts.google IBM Plex Mono ○ · commitmono.com ○ ·
github floriankarsten/space-grotesk ○ · madegooddesigns inter ○. Icons/Color: radix-ui.com/colors ○ ·
carbondesignsystem.com/data-visualization/color-palettes ○ · undraw.co/license ○ · openpeeps.com ○ ·
github.com/fnando/sparkline ○ · pkgpulse lucide-vs-heroicons-vs-phosphor ○.
