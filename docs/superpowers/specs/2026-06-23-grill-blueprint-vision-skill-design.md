# Design: `/grill` skill — grill → blueprint → vision (thin slice)

- Date: 2026-06-23
- Status: approved (brainstorming) — pending spec review
- Owner-facing capability for the planning-strategy lane of the Business Operating System.

## Problem & purpose

`agent_runtime` is a development platform (harness + guardrails + sandbox). On top
of it, the business agent team should help the **Owner/platform-developer** turn a
program or asset they are building into a tailored plan: intensively interview them
("grill"), draw a blueprint, and present a fit vision + direction + methodology.

Today that value flow does not exist as a tool. The org foundation
(`BUSINESS-OPERATING-SYSTEM.md`) and per-lane operating procedure
(`WORK-LANE-PLAYBOOKS.md`) are in place, but there is no interactive entry point
that produces a per-situation blueprint and vision.

This spec defines the **thin end-to-end slice**: a single conversational skill,
`/grill`, that runs grill → blueprint → vision and writes draft artifacts.

## Users & scope

- **User:** the Owner / platform-developer using this instance (single-user,
  internal, dogfood-first). **Not** external clients — no multi-tenancy, no
  external-effect surface beyond in-repo drafts.
- **In scope:** one skill that conducts the interview and synthesizes two draft
  artifacts, mapped to the existing lane playbooks, demoable on its own.
- **Out of scope (YAGNI, later slices):** the enablement-asset package (skills/
  hooks/APIs/docs catalog), deepening each phase (rich canvas, scored vision
  options), external-client/multi-tenant operation.

## Goals / non-goals

- **Goal:** a short interview yields `BLUEPRINT.md` + `VISION-DIRECTION.md` drafts
  under `agents/project/blueprints/<slug>/`, with a methodology section that maps
  to `WORK-LANE-PLAYBOOKS.md` and proposes a first taskset. Zero external effects.
- **Non-goal:** inventing business facts, contacting anyone, writing to external
  systems, or auto-registering/executing tasksets. The skill *elicits* and
  *drafts* only.

## Architecture — one skill, three phases

`skills/grill/SKILL.md` (live-only; the template ships a curated subset and other
live-only skills like `rsi-planning-loop` set the precedent — no template mirror,
so no host-lock regeneration).

### Phase A — Grill (discovery)
Conduct a structured interview **one question at a time** (brainstorming-style
discipline), over a fixed six-part frame:
1. **Asset** — what program/asset you built or are building with agent_runtime; current state.
2. **Problem & who** — the problem it solves; the target user/segment.
3. **Value & differentiation** — why it is better/different; proof you already have.
4. **Constraints** — time, money, skills, risk tolerance; what you will and won't do.
5. **Goals** — what success looks like (revenue / users / learning) and the timeframe.
6. **Monetization hypothesis** — how it could make money (stated by the Owner).

Answers are captured to `INTAKE.md` as they are given. Unknown/declined items are
recorded as `OWNER-DECIDES`, never guessed.

### Phase B — Blueprint
Synthesize the intake into `BLUEPRINT.md`, a lean-canvas-style one-pager:
Problem · Customer · Value proposition · The asset · Channels · Revenue hypothesis ·
Cost notes · Key risks · Open questions (`OWNER-DECIDES`). Each field is filled from
the grill; gaps are explicit, not fabricated.

### Phase C — Vision · Direction · Methodology
Synthesize `VISION-DIRECTION.md`:
- **Vision:** a one-paragraph fit vision derived from the blueprint, confirmed with
  the Owner (not imposed).
- **Direction:** 3–5 roadmap themes / next bets presented as options for the Owner to choose.
- **Methodology:** which lanes/cycles to run to execute, mapped explicitly to
  `WORK-LANE-PLAYBOOKS.md` and the `BUSINESS-OPERATING-SYSTEM.md` cycle contract,
  plus a suggested first taskset to register (suggested, not auto-created).

## Components & file manifest

- `skills/grill/SKILL.md` — frontmatter (`name: grill`, `version`, `description`,
  `triggers`, `dependencies` on the packet + playbooks), the six-part frame, the
  three-phase instructions, the safety rules, and the two artifact templates
  (BLUEPRINT, VISION-DIRECTION) inline.
- `agents/project/blueprints/README.md` — explains the output directory and that
  contents are Owner drafts.
- Output (created at run time, not shipped): `agents/project/blueprints/<slug>/`
  containing `INTAKE.md`, `BLUEPRINT.md`, `VISION-DIRECTION.md`. `<slug>` =
  kebab asset name + date.
- `tests/test_grill_skill.py` — structural guards.
- No new scripts or hooks (YAGNI for this slice).

## Data flow

`/grill` → interview (A, one Q at a time) → write `INTAKE.md` → synthesize
`BLUEPRINT.md` (B) → synthesize `VISION-DIRECTION.md` (C) → point the Owner at the
relevant lane playbooks and the suggested first taskset. Every output is an in-repo
draft; nothing is sent or executed.

## Safety boundary

- Inherits `BUSINESS-OPERATING-SYSTEM.md`'s safe-effect boundary verbatim: no
  external writes, no contacting customers/leads/partners, no price/contract
  mutation, no scraping/spam/manipulation.
- The grill **elicits** the Owner's own answers and decisions; it does not invent
  business facts. Anything not stated is `OWNER-DECIDES`.
- Outputs are drafts; the Owner approves direction and any later external action.
- The skill states these rules explicitly in its body.

## Testing

`tests/test_grill_skill.py` (structural — the interview itself is conversational and
not unit-tested):
- `skills/grill/SKILL.md` exists with valid frontmatter (`name: grill`).
- Body contains all six discovery-frame items and the three phase headings.
- Body references the safe-effect boundary and `OWNER-DECIDES`.
- Body links to `WORK-LANE-PLAYBOOKS.md` and `BUSINESS-OPERATING-SYSTEM.md`.
- BLUEPRINT and VISION-DIRECTION templates include their required sections.
- `agents/project/blueprints/README.md` exists.

## Success criteria

Running `/grill` through a short interview produces a `BLUEPRINT.md` +
`VISION-DIRECTION.md` draft under `agents/project/blueprints/<slug>/`, whose
methodology section maps to existing lane playbooks and proposes a first taskset,
with zero external effects and passing structural tests. Demoable end-to-end.

## Delivery (collision-safe)

Built in an isolated git worktree off the latest `main`; landed via a single PR
(per this session's established pattern). No shared-checkout or active-worktree
contact. CI auto-merges on green.
