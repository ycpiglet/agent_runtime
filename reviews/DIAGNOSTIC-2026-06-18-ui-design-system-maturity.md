---
title: UI Design System Maturity Diagnostic
status: accepted
date: 2026-06-18
task_set_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
task_id: TASK-AR-578
tags: [ui, design-system, governance, diagnostic]
---

# UI Design System Maturity Diagnostic

## Bottom line

Agent Runtime is at **2.0 / 5** design-system maturity. Color and theme tokens
are real assets; most other UI decisions are still made inside page-level
HTML/CSS/JS. The Owner concern is correct: without stronger assetization rules
and a gate, future UI work can keep producing one-off design.

This is not a reason to freeze the visual language. Mature systems separate
two tracks:

1. **System execution**: workers implement with existing tokens, UI components,
   and pattern components.
2. **Design exploration**: a lead designer proposes a new visual direction,
   validates it, and promotes only accepted deltas into the system.

## Current repo evidence

- Current W3 snapshot: `src/agent_runtime/ui_console.py` has **12,794 lines**.
- The console still carries the UI shell, CSS, and client behavior in one
  Python module; there is no durable `components/ui` layer.
- `docs/design/agent-runtime/DESIGN.md` captures visual direction and tokens,
  but it does not define enforceable assetization rules.
- The theme work created useful semantic color tokens, but typography, spacing,
  radius, layout, and pattern reuse remain mostly literal values in the console
  stylesheet.
- `ORG-MODEL.yml` had one broad `uiux` role, which is too coarse for design
  strategy, system stewardship, implementation, and independent UX evaluation.

Owner-provided maturity notes align with the local evidence:

- Color/theme assetization is the only strong layer.
- Button, card, modal, table, and pane patterns do not have a reusable API.
- Repeated UI structures are difficult to classify as token, UI component,
  pattern component, or one-off.
- Existing documentation states intent, but no gate prevents new literal CSS or
  page-level component duplication.

## Reference patterns

- **W3C Design Tokens Community Group** treats design tokens as portable,
  machine-readable design decisions. Agent Runtime should treat tokens as a
  contract, not just a CSS convenience. Source: https://www.designtokens.org/
- **Atomic Design** gives a useful hierarchy: atoms, molecules, organisms,
  templates, pages. For this repo the practical mapping is token -> UI component
  -> pattern component -> page assembly. Source:
  https://atomicdesign.bradfrost.com/chapter-2/
- **GOV.UK Design System** uses contribution criteria and a backlog for new
  components and patterns. The useful lesson is that new UI ideas need an
  explicit proposal path instead of ad hoc page code. Sources:
  https://design-system.service.gov.uk/community/contribution-criteria/ and
  https://github.com/alphagov/govuk-design-system-backlog
- **Shopify Polaris**, **IBM Carbon**, and **Salesforce Lightning Design System**
  separate guidance, tokens, components, patterns, and contribution rules.
  Their common operating model is reuse by default, contribution for extension.

## Maturity score

| Area | Score | Evidence |
| --- | ---: | --- |
| Color/theme tokens | 4 / 5 | Light/dark semantic tokens exist and are documented. |
| Typography/spacing/radius tokens | 1 / 5 | Many literal font-size, padding, margin, gap, and radius values remain in the console CSS. |
| UI components | 1 / 5 | Reusable button/card/modal/table APIs are absent. |
| Pattern components | 1 / 5 | Domain patterns such as task lanes, evidence panels, and claim cards are still page-bound. |
| Governance gates | 1 / 5 | Before this task, no design-system gate existed. |
| Design exploration | 2 / 5 | Research docs exist, but new directions do not have a formal RFC and promotion path. |

Weighted result: **2.0 / 5**.

## Root causes

- The accepted `DESIGN.md` is a visual direction record, not an operating
  contract.
- UI work has no required classification step before implementation.
- Page files are allowed to keep absorbing tokens, components, patterns, and
  workflow state together.
- The broad `uiux` role creates one overloaded queue for strategy, system
  stewardship, implementation, and evaluation.
- Verification focuses on rendered behavior and Python-side tests more than
  design-system drift.

## Recommended operating model

- Keep `DESIGN.md` as the accepted visual direction.
- Add `DESIGN-SYSTEM.md` as the enforceable contract.
- Require every UI refactor to classify reusable surface area as:
  `design_token`, `ui_component`, `pattern_component`, or `one_off_for_now`.
- Add a gate that checks required governance artifacts, role routing, and raw
  literals in changed UI files.
- Split UI/UX routing in metadata:
  `lead-designer`, `design-system-steward`, `interface-designer`, and
  `ux-evaluator`.
- Allow new design through a short Design Exploration RFC. Do not let workers
  invent new visual language directly in page code.

## Decision

Create `docs/design/agent-runtime/DESIGN-SYSTEM.md`, add
`scripts/design_system_gate.py`, wire it into Owner governance, and extend the
UI/UX role overlay without creating live per-role directories.

