---
title: "Design Exploration RFC: <short title>"
status: exploratory  # exploratory | accepted | rejected | promoted
date: <YYYY-MM-DD>
author: <role or agent id, e.g. lead-designer>
task_set_id: <TASKSET-... if applicable>
task_id: <TASK-... if applicable>
tags: [ui, design-system, rfc]
---

# Design Exploration RFC: <short title>

> File this RFC from `docs/design/agent-runtime/RFC-TEMPLATE.md` **before** any
> change to the visual language (new direction, new token semantics, new
> component or pattern visuals). Reuse existing tokens, UI components, and
> pattern components by default; this lane exists only for changes that the
> accepted visual direction cannot express. See `DESIGN-SYSTEM.md` ("New design
> direction RFC lane").

## Problem

State the user problem, the target screen(s), and the workflow that is poorly
served today. Explain why the existing visual direction is insufficient (do not
restate it as "I want something new").

## Proposed direction

Describe the proposed visual direction. Provide 2-3 reference systems or
screenshots. Cover desktop and mobile intent.

## Scope

- **Minimum token delta**: list new/changed `design_token`s and their initial
  maturity tier (`experimental` on entry).
- **New UI components / pattern components**: list each, its class, and tier.
- **Surfaces touched**: which views/routes adopt this, behind the originating
  view only until promoted.
- **Out of scope**: what this RFC explicitly does not change.

## Risks

Call out consistency-vs-novelty risk, accessibility (status color must never be
the only signal; visible text labels required), density, responsive behavior,
and any migration cost for existing surfaces. Note how the change stays
non-load-bearing until promotion.

## Decision

Record the outcome and update the `status` field above:

- `exploratory` — under consideration; not load-bearing.
- `accepted` — visual direction approved; update `DESIGN.md` and, for system
  rules, `DESIGN-SYSTEM.md`. Workers implement from the updated contract.
- `rejected` — not adopted; keep this record for context.
- `promoted` — an accepted asset reached `stable` per the maturity-tier criteria
  in `DESIGN-SYSTEM.md` (adoption, stability, evidence).

Decision owner: `lead-designer` (direction) / `design-system-steward` (tokens,
component/pattern promotion).
