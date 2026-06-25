---
name: scaffold
version: 1.0.0
description: Use when the Owner wants starter asset files for a program planned with /grill and /enable — scaffolds skeleton README, manual, API reference, and a skill template under the blueprint folder so the Owner has a head start. Planning-strategy lane, slice D (scaffolding).
triggers:
  - scaffold
  - starter assets
  - skeleton
  - boilerplate
  - asset files
dependencies:
  - agents/project/blueprints/README.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
---

# Scaffold — starter enablement asset files

Generate tailored **skeleton starter files** for a program after `/grill` (blueprint)
and `/enable` (enablement manual): a README, an operator manual, an API reference,
and a skill template — under the blueprint's own folder, as drafts the Owner adapts.

## Safety boundary (read first)

Outputs are **draft skeletons under `agents/project/blueprints/<slug>/assets/`** —
NOT the live `skills/` or `scripts/` trees. This skill does **not promote** anything
into a live asset, does not run anything, and causes no external effect. Tailor the
structure from the blueprint; leave specifics the Owner has not decided as
`OWNER-DECIDES`. Inherit the `agents/project/BUSINESS-OPERATING-SYSTEM.md` safe-effect
boundary verbatim. Outputs are drafts in this repo.

## Input

Take a blueprint slug. Read `agents/project/blueprints/<slug>/BLUEPRINT.md`,
`VISION-DIRECTION.md`, and `ENABLEMENT.md` (if present) for context. If the slug is
missing, say so and stop (run `/grill` then `/enable` first to create the blueprint).

## Output — starter assets

Create `agents/project/blueprints/<slug>/assets/` with these skeleton files, tailored
from the blueprint (headings filled from context; unknown specifics `OWNER-DECIDES`):

- `README.md` — what the program is, who it is for, and how to run/use it.
- `MANUAL.md` — operator manual: setup, usage, configuration, troubleshooting.
- `API-REFERENCE.md` — endpoints/commands, inputs, outputs (or `OWNER-DECIDES: N/A`).
- `SKILL.skeleton.md` — a starter `SKILL.md` the Owner can adapt to wrap the program
  as an agent skill (frontmatter + sections).

Finish by telling the Owner these are drafts to adapt and — when ready — to promote
into the real `skills/` / `docs/` themselves. This skill never promotes them.

## Templates

### README.md
```
# <program>

What it is: ...
Who it is for: ...

## Run / use
1. ...
2. ...
```

### MANUAL.md
```
# <program> — Operator Manual

## Setup
...

## Usage
...

## Configuration
- OWNER-DECIDES: ...

## Troubleshooting
| Symptom | Likely cause | Fix |
| --- | --- | --- |
| ... | ... | ... |
```

### API-REFERENCE.md
```
# <program> — API / Command Reference

(OWNER-DECIDES: N/A if the program exposes no API.)

## <endpoint or command>
- Inputs: ...
- Outputs: ...
- Example: ...
```

### SKILL.skeleton.md
```
---
name: <program-skill>
version: 0.1.0
description: Use when ... (one-line trigger description) — OWNER-DECIDES.
triggers:
  - ...
---

# <Program> skill

## When to use
...

## Steps
1. ...
```
