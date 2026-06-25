---
name: grill
version: 1.1.0
description: Use when the Owner wants to turn a program/asset they are building with agent_runtime into a tailored plan — an intensive discovery interview ("grill") that drafts a blueprint and a fit vision/direction/methodology. Planning-strategy lane entry point.
triggers:
  - grill
  - blueprint
  - business plan
  - vision
  - discovery interview
dependencies:
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
---

# Grill — Discovery → Blueprint → Vision

Interview the Owner about a program/asset they are building with agent_runtime,
then draft a blueprint and a fit vision/direction/methodology. This is the
planning-strategy lane's entry point of the Business Operating System.

## Safety boundary (read first)

This skill ELICITS the Owner's own answers and decisions; it does NOT invent
business facts. Anything the Owner does not state is recorded literally as
`OWNER-DECIDES`. All outputs are **drafts in this repo**. Inherit the
`agents/project/BUSINESS-OPERATING-SYSTEM.md` safe-effect boundary verbatim: no
external writes; no contacting customers/leads/partners; no price/contract/invoice
mutation; no scraping, spam, fake engagement, or platform manipulation. The skill
never sends, publishes, charges, or auto-registers anything — it drafts only.

## Output location

Create `agents/project/blueprints/<slug>/` where `<slug>` is the kebab-cased asset
name plus the date (for example `my-cli-tool-2026-06-23`). Write `INTAKE.md`,
`BLUEPRINT.md`, and `VISION-DIRECTION.md` there.

## Phase A — Grill (discovery)

Ask ONE question at a time (never batch). Cover this six-part frame and record each
answer to `INTAKE.md` as you go. If the Owner declines or does not know, write
`OWNER-DECIDES` for that item and move on.

1. **Asset** — What program/asset are you building with agent_runtime? What does it
   do, and what is its current state?
2. **Problem & who** — What problem does it solve, and who has that problem (target
   user/segment)?
3. **Value & differentiation** — Why is it better or different? What proof do you
   already have?
4. **Constraints** — Time, money, skills, risk tolerance: what will you and won't
   you do?
5. **Goals** — What does success look like (revenue / users / learning), and over
   what timeframe?
6. **Monetization hypothesis** — How could this make money? (your hypothesis)

### Adaptive follow-ups
After an answer, ask a focused follow-up only when it materially sharpens the
blueprint (e.g. a vague customer → "who feels this most acutely first?"). Stop once
the answer is concrete; do not interrogate.

### Domain frame
Pick the closest domain and ask its 1–2 extra questions; record under the matching
INTAKE field and mark unknowns `OWNER-DECIDES`:
- **SaaS/tool** — pricing model (seat/usage/flat?), activation moment, churn risk.
- **Content/media** — distribution channel, cadence, what compounds over time.
- **Marketplace/network** — which side is harder to get, cold-start plan.
- **Services/agency** — delivery capacity, repeatability, productization path.

When the frame is covered, write `INTAKE.md` using the template below.

## Phase B — Blueprint

Synthesize the intake into `BLUEPRINT.md` using the template below. Fill each field
from the grill; mark gaps `OWNER-DECIDES`. Do not fabricate. Include the
unit-economics hypothesis, the assumptions register, and the risk register.

## Phase C — Vision · Direction · Methodology

Write `VISION-DIRECTION.md` using the template below:
- **Vision** — one paragraph derived from the blueprint; confirm it with the Owner.
- **Direction** — present 3–5 options scored on a decision matrix
  (Impact / Ease / Safety / Fit / Speed, each 1–5, higher is better), with a
  **recommended** option + rationale for the Owner to confirm.
- **Methodology** — map the work to lanes/cycles: reference
  `agents/project/WORK-LANE-PLAYBOOKS.md` for the per-lane procedure and
  `agents/project/BUSINESS-OPERATING-SYSTEM.md` for the cycle contract. Suggest a
  first taskset to register (suggest only; do not auto-create).

Finish by pointing the Owner to the relevant lane playbooks and the suggested first
taskset.

**Next:** suggest `/enable <slug>` to build the enablement pack from this blueprint.

## Templates

### INTAKE.md

```
# Intake — <asset>

- Asset: ...
- Problem & who: ...
- Value & differentiation: ...
- Constraints: ...
- Goals: ...
- Monetization hypothesis: ...
```

### BLUEPRINT.md

```
# Blueprint — <asset>

| Field | Notes |
| --- | --- |
| Problem | ... |
| Customer | ... |
| Value proposition | ... |
| The asset | ... |
| Channels | ... |
| Revenue hypothesis | ... |
| Cost notes | ... |
| Key risks | ... |
| Open questions | OWNER-DECIDES: ... |

## Unit economics (hypothesis — OWNER-DECIDES the numbers)
- Price / unit: ...
- CAC (cost to acquire): ...
- LTV (lifetime value): ...
- Gross margin: ...

## Assumptions register
| Assumption | Confidence (lo/med/hi) | How to validate |
| --- | --- | --- |
| ... | ... | ... |

## Risk register
| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| ... | ... | ... | ... |
```

### VISION-DIRECTION.md

```
# Vision · Direction · Methodology — <asset>

## Vision
<one paragraph>

## Direction options (scored)
| Option | Impact | Ease | Safety | Fit | Speed | Total |
| --- | --- | --- | --- | --- | --- | --- |
| A: ... | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | sum |
| B: ... | | | | | | |
| C: ... | | | | | | |

**Recommended:** <option> — <rationale> (Owner confirms).

## Methodology (lanes & cycles)
- Lane: <lane> — <what to draft> (see agents/project/WORK-LANE-PLAYBOOKS.md)
- Cycle contract: see agents/project/BUSINESS-OPERATING-SYSTEM.md
- Suggested first taskset: <name> (suggested; register via `scripts/work.py new` when the Owner approves)
```
