---
title: Design-System Governance & Design-Org Role Topology — Research
status: synthesized (partial verification)
date: 2026-06-18
task_set_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
task_id: TASK-AR-578
tags: [ui, design-system, governance, research, org-design]
---

# RESEARCH — Design-System Governance & Design-Org Role Topology

- **Date:** 2026-06-18
- **For:** TASK-AR-578 / `reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md`
- **Question:** (1) How do mature design systems decide token vs component vs pattern vs
  one-off, and what mechanical gates enforce it? (2) How do they keep producing *new*
  design without drift? (3) Single designer vs split roles, and how to map this onto a
  multi-agent Claude Code org.
- **Method:** deep-research fan-out (5 angles → 23 sources → 106 claims). Verification +
  synthesis were cut short by a session limit (resets 14:00 KST); **synthesis below was
  done by hand** from the gathered claims + sources + the prior org-design research
  (`RESEARCH-2026-06-14-agent-org-design-references.md`).

### Verification legend

- **✓ verified** — 3-0 adversarial vote (independently confirmed).
- **○ gathered** — extracted from a fetched source but verification *abstained* (hit the
  session limit). Source-attributed, plausible, **not independently re-checked**.
- **✗ corrected** — claim was refuted; the corrected version is stated.

## Bottom Line

The research **validates the TASK-AR-578 decision**: a four-tier asset taxonomy
(token → ui-component → pattern-component → one-off), a mechanical gate, an
RFC/exploration track for novelty, and a **role split** that includes a
lead/principal-designer-equivalent. Three load-bearing findings:

1. **Taxonomy is a solved problem** — DTCG (tokens) + Atomic Design (components/patterns)
   give a clean, citable rule for what goes where. The missing piece in this repo is not
   the model, it's the *gate*.
2. **Novelty without drift is an org mechanism, not a tool** — every mature system uses
   **maturity tiers + a promotion pipeline + a bidirectional loop** (product/exploration
   proposes → system absorbs only accepted deltas). The answer to "won't it always look
   the same?" is: a separate, *labelled*, gated exploration track — not freezing the system.
3. **Yes, split the role, but split for the right reason** — separate *system stewardship*
   (consistency), *execution* (cheap, system-only), *direction/exploration* (novelty), and
   *critique* (verification). Per the prior research, persona diversity pays off **only in
   the exploration/critique layer**, never in routine execution (cost ≈ 15×).

---

## STRAND 1 — Asset-ization taxonomy & mechanical gates

### The token model (DTCG)

- **✓** The W3C/DTCG **Design Tokens Format Module 2025.10** is the first *stable* version
  (Final Community Group Report, 28 Oct 2025). Tokens are portable, machine-readable design
  decisions — a cross-tool contract, not a CSS convenience.
  `https://www.designtokens.org/tr/2025.10/format/`
- **✓** DTCG separates **primitive types** (`color, dimension, fontFamily, fontWeight,
  duration, cubicBezier, number`) from **composite types** (`strokeStyle, border,
  transition, shadow, gradient, typography`) whose value is built from multiple named child
  values. → This is exactly how to model `--shadow`, `--border`, and `typography` as *one*
  composite token instead of scattered literals.
- **✗ corrected** — It is **not** true that every token must carry a `$type`. A token is an
  object carrying **`$value`**; `$type` *declares* the type and may be set on a group and
  inherited, or omitted. (The "$type mandatory on every token" framing was refuted 0-3.)
- **○** Token **tiers** (the canonical "global/alias/component" model): Material 3 uses
  **reference (primitive) → system (semantic/alias) → component** tokens.
  `https://m3.material.io/foundations/design-tokens/overview`

### The component/pattern model (Atomic Design)

- **✓** Atomic Design = five tiers: **atoms → molecules → organisms → templates → pages**.
  Atoms are foundational elements (label, input, button) that can't be decomposed further.
  `https://atomicdesign.bradfrost.com/chapter-2/`
- **✓** It is explicitly **compositional**: molecules are small groups acting as a unit;
  organisms are composed of molecules/atoms/other organisms. → This *is* the rule for
  "primitive component vs composed pattern": **atom/molecule = ui-component, organism =
  pattern-component.**

### "Does it go in the system?" — the decision rule

- **○** Nathan Curtis (EightShapes), *"I made this. Does it go in the system?"* — the
  canonical answer: **not everything you build belongs in the system.** Shared, reused,
  general things graduate in; product-specific one-offs stay in the product.
  `https://medium.com/eightshapes-llc/i-made-this-does-it-go-in-the-system-3b67b9894531`
  Companion: *Design System Tiers*
  `https://medium.com/eightshapes-llc/design-system-tiers-2c827b67eae1`

**Synthesized 4-tier taxonomy + decision rule (for our `DESIGN-SYSTEM.md`):**

| Tier | Is | Atomic/DTCG mapping | Promote when |
|------|----|---------------------|--------------|
| `design_token` | a named decision: color/space/radius/type/shadow | DTCG primitive + semantic + component tiers | used (or *will* be) in ≥2 places |
| `ui_component` | generic element w/ stable API: Button/Input/Card/Modal/Table | atoms + molecules | reused, or has variants/states |
| `pattern_component` | domain composite that repeats: task-lane, evidence-card, command-bar, list, empty/error/loading | organisms | the **rule of three** — 3rd occurrence |
| `one_off_for_now` | used once, no repetition signal | (stays in the page) | next reuse triggers re-classification |

### Mechanical gates (turn "intent" into "enforced")

All `○` (gathered, real tools, not re-verified):

- **Atlassian `@atlaskit/stylelint-design-system`** — CSS-side token gate. Named rules:
  `ensure-design-token-usage`, `no-deprecated-design-token-usage`,
  `no-unsafe-design-token-usage`. Build-time lint, not convention.
  `https://atlassian.design/components/stylelint-design-system`
- **MetaMask `@metamask/eslint-plugin-design-tokens`** — `color-no-hex` blocks hardcoded
  hex; enforces token usage. Proof that token governance can be a code-level gate.
  `https://github.com/MetaMask/eslint-plugin-design-tokens`
- **`stylelint-plugin-rhythmguard`** — enforces a spacing/radius/type **scale**, flags
  off-scale "magic numbers", `prefer-token` rule, autofix snaps `p-[13px] → p-[12px]`,
  reads Style Dictionary / DTCG token files.
  `https://github.com/PetriLahdelma/stylelint-plugin-rhythmguard`
- **`stylelint-magic-numbers`** — generic magic-number detector.
  `https://github.com/JuStTheDev/stylelint-magic-numbers`
- **Figma → Style Dictionary** pipeline — token source-of-truth sync design↔code.
  `https://medium.com/@gabrielrudy575/creating-a-design-tokens-automation-pipeline-with-figma-and-style-dictionary-304272d5465f`

> **Our wrinkle:** the UI is a single Python file (`ui_console.py`), not a JS/CSS project,
> so off-the-shelf stylelint won't drop in cleanly. The gate should be a **custom
> `scripts/design_system_gate.py`** that scans changed UI regions for raw color/px/radius
> literals outside the token blocks and for new bespoke classes — same *idea* as the tools
> above, repo-native (this is already the TASK-AR-578 decision).

### What belongs in `DESIGN-SYSTEM.md`

Synthesized from the contribution-model sources
(`…/defining-design-system-contributions-eb48e00e8898`,
`…/team-models-for-scaling-a-design-system-2cf9d03be6a0`):
token tiers + scales; the 4-tier taxonomy + decision rule above; the "use existing first"
rule; component/pattern API + variant/state conventions; the **maturity tiers** (below);
the **contribution/promotion checklist**; the **gate** definition; and role ownership.

---

## STRAND 2 — Consistency vs novelty (the core tension)

The recurring pattern across every mature/government system: **maturity tiers + an explicit
promotion pipeline + objective gates**. New design is *allowed* but *labelled* and not
load-bearing until it earns promotion.

- **○ USWDS** — 4-phase lifecycle (Proposal → Development → Released → Deprecated); released
  components are sub-tiered **Experimental / Stable / "Use with caution."** Promotion to
  Stable is gated by **passing tests + full docs + production history**. New components enter
  via a public GitHub discussion with a **45-day** comment period.
  `https://designsystem.digital.gov/components/lifecycle/`
- **○ VA.gov** — 6-stage maturity (Proposed, Candidate, Available, Deployed, Best Practice;
  Deprecated from any stage) bucketed into **Don't Use / Use with Caution / Use**. A Design
  System Team promotes on three checkable factors: **Stability, Research, Adoption**.
  `https://design.va.gov/about/maturity-scale`
- **○ GitHub Primer** — **Experimental → Ready → Deprecated**; "Ready" carries an LTS
  guarantee, breaking changes need a major bump + migration path.
  `https://primer.style/contribute/component-lifecycle/`
- **○ Salesforce (Lightning)** — adopts a **hybrid** team model (Curtis's *Centralized* +
  *Federated*). The stated novelty-without-drift mechanism is a **bidirectional feedback
  loop**: the system constrains product design, and product explorations feed *back* to
  evolve the system.
  `https://medium.com/salesforce-ux/the-salesforce-team-model-for-scaling-a-design-system-d89c2a2d404b`
- **○ Nathan Curtis — "Team Models for Scaling a Design System"** — **Centralized /
  Federated / Hybrid** (the source the Salesforce model builds on).
  `https://medium.com/eightshapes-llc/team-models-for-scaling-a-design-system-2cf9d03be6a0`
  Maturity spectrum overview:
  `https://www.designsystems.com/the-spectrum-of-maturity-for-design-systems/`

**The answer to "won't it always look the same?":** No — *if* you run two tracks:

1. **System track (default, cheap):** workers build features using only `stable` tokens +
   components + patterns. The gate enforces this.
2. **Exploration track (gated, infrequent):** a **Design Exploration RFC** proposes a new
   direction → builds it as an **`experimental`** asset (labelled, not load-bearing) →
   validates → **promotes only accepted deltas** into `stable`. Promotion is gated by
   objective criteria (tests/docs/usage/research/adoption) owned by the steward/lead.

That tiering is precisely what prevents *both* failure modes: frozen sameness (the
exploration track keeps proposing) **and** drift (only promoted, gated deltas reach stable).

---

## STRAND 3 — Role topology: single vs split, and the agent mapping

### Human practice

- **○** Lead vs Principal designer: a **Lead** owns people/process/delivery and consistency
  across a team's output; a **Principal** is a senior IC who sets **direction, taste, and
  standards through craft**, not management.
  `https://newsletter.uxdesign.cc/p/whats-the-difference-between-lead`
  → The "propose genuinely new design" owner maps to the **Principal/Lead-Designer**
  archetype (direction & taste), distinct from the steward (consistency) and the interface
  designer (execution).

Standard split in mature orgs: **System Steward/Maintainer** (owns tokens/components/gate/
promotion) · **Product/Interaction Designer** (builds features with the system) · **Design
Lead/Principal** (direction, taste, exploration) · **Design Critic / UX Evaluator**
(independent critique, a11y/usability) · **Design Ops** (tooling/process; foldable into the
steward at small scale).

### Mapping onto the agent org (Director→Lead→Worker+Reviewer + blind-Delphi)

This is **not greenfield** — the prior research (`RESEARCH-2026-06-14`) established gstack
(Garry Tan's 23-persona Claude Code toolkit) as the closest public analogue and confirmed
the repo already ships org machinery (`roles.yml`, orchestrator, seminar/council). Sources
re-confirmed here: `https://github.com/garrytan/gstack`, multi-agent design papers
`https://aclanthology.org/2025.coling-main.314.pdf`,
`https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/`.

**Recommended split of the single `uiux_designer` into 4 personas** (matches the TASK-AR-578
decision):

| Persona | Org tier | Owns | Diversity? | Cost posture |
|---------|----------|------|:---:|---|
| **lead-designer** (principal) | Lead | design direction, **Design Exploration RFCs**, taste/standards, final visual call | n/a (decision owner) | invoked for RFCs only |
| **design-system-steward** | Lead/Reviewer | `DESIGN-SYSTEM.md`, tokens/components/patterns, the **gate**, **promotion** decisions | no (gatekeeper) | always-on, cheap |
| **interface-designer** | Worker | feature implementation using **existing assets only**; keeps pages = layout + data binding | **no — single agent** | routine, cheapest |
| **ux-evaluator / critic** | Reviewer | independent critique, a11y/usability, drift detection | **yes — blind-Delphi** | review-gate only |

**How agents generate *new* design (not regurgitation):** spin up a **divergent exploration
panel** *only* for a Design Exploration RFC — N independent proposals along *substance* axes
(density-first · accessibility-first · information-hierarchy-first · brand-expressive),
**blind-Delphi** aggregation (independent drafts before agents see each other), an
adversarial skeptic, then the **lead-designer** synthesizes and the **steward** promotes the
accepted deltas. This is exactly where the prior research said diversity pays off
(deliberation/review), and **nowhere else** — routine execution stays a single
interface-designer using only stable assets.

**Cost discipline (binding):** multi-agent ≈ **15×** tokens; persona diversity only in the
exploration/critique layer. So the expensive divergent panel runs **infrequently and gated**
(per RFC), while 95% of UI work is one cheap interface-designer agent + the steward's gate.
This is the cost-respecting shape for a token-sensitive Owner.

---

## Consolidated recommendations

1. **Taxonomy + gate (Strand 1):** adopt the 4-tier taxonomy (token/ui-component/
   pattern-component/one-off) with the rule-of-three promotion. Ship
   `scripts/design_system_gate.py` (repo-native analogue of Atlassian/MetaMask/rhythmguard):
   fail on raw color/px/radius literals outside token blocks + new bespoke classes in
   changed UI. Add `--text-*`, `--space-*`, `--radius-sm/md/lg` scale tokens first
   (closes diagnostic categories 2/3/4).
2. **Novelty mechanism (Strand 2):** two tracks + **maturity tiers** (`experimental` →
   `stable`) + a **Design Exploration RFC** + objective promotion gates (tests/docs/usage).
   This keeps the look evolving without drift.
3. **Roles (Strand 3):** split `uiux_designer` → **lead-designer · design-system-steward ·
   interface-designer · ux-evaluator**. New design is *proposed* by the lead-designer via a
   gated, blind-Delphi exploration panel; *consistency* is owned by the steward + gate;
   *execution* stays single-agent and system-only. → **Yes, a lead/principal-designer-
   equivalent is warranted**, specifically to own the novelty track.

## Open items (need the 14:00 KST reset to finish properly)

- Only **4 / 25** claims got full 3-vote verification; ~20 are `○` gathered (abstained, not
  refuted). If you want full rigor, re-run **verification + synthesis only** after 14:00 KST
  (the costly search/fetch is already done — resume is cheap).
- Strand-3 source claims (gstack, multi-agent papers, lead/principal) were fetched but not
  among the verified-25; they're corroborated by `RESEARCH-2026-06-14` rather than freshly
  re-checked here.

## Sources (23 fetched; ✓ = a claim from it was 3-0 verified)

DTCG ✓ `designtokens.org/tr/2025.10/format` · W3C announce `w3.org/community/design-tokens` ·
Atomic Design ✓ `atomicdesign.bradfrost.com/chapter-2` · Material 3 tokens
`m3.material.io/foundations/design-tokens/overview` · EightShapes: "I made this…"
`/i-made-this-does-it-go-in-the-system-3b67b9894531`, Tiers `/design-system-tiers-2c827b67eae1`,
Team Models `/team-models-for-scaling-a-design-system-2cf9d03be6a0`, Contributions
`/defining-design-system-contributions-eb48e00e8898` · Primer
`primer.style/contribute/component-lifecycle` · USWDS
`designsystem.digital.gov/components/lifecycle` · VA `design.va.gov/about/maturity-scale` ·
Salesforce `medium.com/salesforce-ux/the-salesforce-team-model…` · Maturity spectrum
`designsystems.com/the-spectrum-of-maturity-for-design-systems` · Gates: Atlassian
`atlassian.design/components/stylelint-design-system`, MetaMask
`github.com/MetaMask/eslint-plugin-design-tokens`, rhythmguard
`github.com/PetriLahdelma/stylelint-plugin-rhythmguard`, magic-numbers
`github.com/JuStTheDev/stylelint-magic-numbers`, Figma+Style Dictionary pipeline ·
gstack `github.com/garrytan/gstack` · multi-agent `aclanthology.org/2025.coling-main.314.pdf`,
`d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad` · lead vs principal
`newsletter.uxdesign.cc/p/whats-the-difference-between-lead`
