# Design: `/enable` skill — per-blueprint enablement pack (slice D)

- Date: 2026-06-24
- Status: approved (brainstorming) — pending spec review
- Slice D of the Business Operating System value flow (grill → blueprint → vision → **enablement**).

## Problem & purpose

`/grill` (slice A→C, merged in #222) produces, for a program the Owner is building,
a `BLUEPRINT.md` and a `VISION-DIRECTION.md` whose **Methodology** section names
which lanes/cycles to run. What is still missing is the bridge from that methodology
to **doing the work with the platform's actual assets**: which skills, scripts, and
docs to use for each step, with references and next actions.

`/enable` fills that gap. Given a blueprint, it produces a tailored `ENABLEMENT.md`
— a per-program operator's manual that maps the methodology to concrete agent_runtime
assets (skill/script/doc/hook/api/reference) so the Owner can apply their program.

## Users & scope

- **User:** the Owner / platform-developer (single-user, internal, dogfood-first).
- **In scope:** one skill, `/enable`, that reads an existing blueprint and writes one
  tailored `ENABLEMENT.md` draft, demoable on top of `/grill` output.
- **Out of scope (YAGNI, later):** a machine-readable asset-index generator script;
  scaffolding starter asset *files* for the user's program; any external effect;
  external-client/multi-tenant operation.

## Goals / non-goals

- **Goal:** `/enable <slug>` reads `agents/project/blueprints/<slug>/` and writes
  `ENABLEMENT.md` mapping each methodology item to concrete platform assets +
  references + next actions, plus a tailored asset index. Zero external effects.
- **Non-goal:** running/executing any recommended asset, inventing assets that do
  not exist, mutating external systems, or auto-registering tasksets. The skill
  *recommends* and *drafts* only; the Owner runs things.

## Architecture — one skill

`skills/enable/SKILL.md` (live-only; consistent with `/grill` and other live-only
skills — no template mirror, no host-lock regeneration).

### Input
`agents/project/blueprints/<slug>/` — primarily `VISION-DIRECTION.md` (its
**Methodology** section) and `BLUEPRINT.md` for context. If the slug or files are
missing, the skill says so and stops (it never fabricates a blueprint).

### Asset awareness (no hardcoding)
When building the map, the skill reads the **live** asset surfaces so its
recommendations never go stale:
- `skills/` (available skills),
- key `scripts/` (e.g. `scripts/work.py`, `scripts/taskset_dispatcher.py`),
- canonical docs `agents/project/WORK-LANE-PLAYBOOKS.md` and
  `agents/project/BUSINESS-OPERATING-SYSTEM.md`,
- `agents/project/RUNTIME-ASSET-REGISTRY.json` (the existing asset registry).

It recommends only assets that actually exist in those surfaces.

### Output — `ENABLEMENT.md`
Written to the same `blueprints/<slug>/` folder, with these sections:
1. **Getting started** — the first concrete sequence of actions.
2. **Methodology → Asset map** — a table: methodology step/lane | platform asset(s)
   (skill/script/doc) | reference | next action.
3. **Tailored asset index** — the subset of skills/scripts/docs relevant to this
   blueprint, each with one line on when to use it.
4. **Open choices** — decisions left to the Owner, marked `OWNER-DECIDES`.

## Data flow

`/enable <slug>` → read `BLUEPRINT.md` + `VISION-DIRECTION.md` → read live asset
surfaces → synthesize `ENABLEMENT.md` (methodology mapped to real assets) → point the
Owner at the Getting-started sequence. Every output is an in-repo draft; nothing is
run or sent.

## Safety boundary

- Inherits `BUSINESS-OPERATING-SYSTEM.md`'s safe-effect boundary verbatim: no
  external writes, no contacting anyone, no price/contract mutation, no
  scraping/spam/manipulation.
- Recommends assets and drafts a manual; it does **not execute** any recommended
  command, run any script, or auto-register a taskset — the Owner does that.
- Recommends only assets that exist; unresolved choices are `OWNER-DECIDES`.
- The skill states these rules explicitly in its body.

## Testing

`tests/test_enable_skill.py` (structural — the synthesis is conversational and not
unit-tested):
- `skills/enable/SKILL.md` exists with valid frontmatter (`name: enable`).
- Body declares the blueprint input (`blueprints/`, `VISION-DIRECTION.md`).
- Body lists the live asset surfaces to read (`skills/`, `scripts/`,
  `RUNTIME-ASSET-REGISTRY.json`, `WORK-LANE-PLAYBOOKS.md`,
  `BUSINESS-OPERATING-SYSTEM.md`).
- `ENABLEMENT.md` template includes its four sections (Getting started,
  Methodology → Asset map, Tailored asset index, Open choices).
- Body references the safe-effect boundary, `OWNER-DECIDES`, and "does not execute".

## Success criteria

`/enable <slug>` reads an existing blueprint and writes `ENABLEMENT.md` mapping the
methodology to concrete, real platform assets with references and next actions, with
zero external effects and passing structural tests — demoable directly on `/grill`
output.

## Delivery (collision-safe)

Built in an isolated git worktree off the latest `main`; landed via a single PR
(this session's established pattern). No shared-checkout or active-worktree contact.
CI auto-merges on green.
