---
name: enable
version: 1.1.0
description: Use when the Owner wants the enablement pack for a program they planned with /grill — reads a blueprint and drafts ENABLEMENT.md mapping the methodology to concrete agent_runtime assets (skills/scripts/docs) with references and next actions. Planning-strategy lane, slice D.
triggers:
  - enable
  - enablement
  - how to apply
  - asset pack
  - operator manual
dependencies:
  - agents/project/blueprints/README.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
---

# Enable — per-blueprint enablement pack

Turn a `/grill` blueprint into a tailored "how to apply your program" manual:
`ENABLEMENT.md`, mapping the blueprint's methodology to concrete agent_runtime
assets (skills, scripts, docs) with references and next actions. Slice D of the
Business Operating System; runs after `/grill`, or on any existing blueprint.

## Safety boundary (read first)

This skill RECOMMENDS assets and DRAFTS a manual. It does NOT execute any
recommended command, run any script, or auto-register a taskset — the Owner does
that. It recommends only assets that actually exist (see "Read live assets").
Unresolved choices are recorded as `OWNER-DECIDES`. Inherit the
`agents/project/BUSINESS-OPERATING-SYSTEM.md` safe-effect boundary verbatim: no
external writes; no contacting customers/leads/partners; no price/contract/invoice
mutation; no scraping, spam, fake engagement, or platform manipulation. Outputs are
**drafts in this repo**.

## Input

Take a blueprint slug. Read `agents/project/blueprints/<slug>/VISION-DIRECTION.md`
(its **Methodology** section) and `BLUEPRINT.md` for context. If the slug or those
files are missing, say so and stop — never fabricate a blueprint (run `/grill`
first to create one).

## Read live assets (no hardcoding)

Before mapping, read the live asset surfaces so recommendations never go stale, and
recommend ONLY assets found there:
- `skills/` — available skills. For an exact, machine-readable list (name +
  description + triggers), run `python scripts/enablement_index.py --json` and map
  from that, so recommendations are precise and never stale.
- key `scripts/` — for example `scripts/work.py` (register work) and
  `scripts/taskset_dispatcher.py` (plan/start tasksets).
- `agents/project/WORK-LANE-PLAYBOOKS.md` and
  `agents/project/BUSINESS-OPERATING-SYSTEM.md` — lane procedure + cycle contract.
- `agents/project/RUNTIME-ASSET-REGISTRY.json` — the asset registry.

## Output — ENABLEMENT.md

Write `agents/project/blueprints/<slug>/ENABLEMENT.md` using the template below. For
each methodology step/lane in `VISION-DIRECTION.md`, recommend the concrete asset(s)
to use, the reference to read, and the next action. Finish by pointing the Owner at
the Getting-started sequence. Do NOT run any recommended command.

### ENABLEMENT.md template

```
# Enablement — <asset>

## Getting started
1. ...
2. ...

## Methodology → Asset map
| Step / lane | Platform asset(s) | Reference | Next action |
| --- | --- | --- | --- |
| ... | skill/script/doc | path | command or step (do not run it) |

## Tailored asset index
- `<asset>` — when to use it for this program.

## Open choices
- OWNER-DECIDES: ...
```
