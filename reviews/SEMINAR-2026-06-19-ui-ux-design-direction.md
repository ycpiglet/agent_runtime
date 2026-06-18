---
type: ui-ux-design-direction-seminar
id: SEMINAR-2026-06-19-ui-ux-design-direction
status: accepted
signal: pass
score: 86
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
task_id: TASK-AR-600
unit_id: UNIT-TASK-AR-600-001
tags: [ui, ux, design-system, seminar, design-direction]
---

# UI/UX Design Direction Seminar 2026-06-19

## Bottom Line

- Summary: choose a focused Design Exploration RFC before any UI source change.
- Result: the selected RFC direction is `operator_attention_graph`, aimed at
  turning the console's graph/wiki/evidence surfaces into one connected
  attention workflow.
- Boundary: this seminar authorizes planning only; implementation remains
  blocked until a later claimed unit updates `DESIGN.md`,
  `DESIGN-SYSTEM.md`, and then UI source files.

## Signal

| Dimension | Verdict | Evidence Expectation |
| --- | --- | --- |
| User problem | pass | operator must see what needs attention, why, and what evidence supports the next action |
| Target workflow | pass | backlog/taskset -> claim/evidence -> graph/wiki context -> safe command handoff |
| Current direction gap | watch | existing operator-console style is consistent but can repeat dense cards without stronger relationship cues |
| RFC readiness | pass | one direction selected, two alternatives rejected, evidence checklist defined |

## Action

| Role | Position | Required Follow-up |
| --- | --- | --- |
| lead-designer | pursue `operator_attention_graph` as the next RFC candidate | write `reviews/RFC-2026-06-19-ui-ux-design-direction.md` with references and token deltas |
| design-system-steward | allow novelty only as labelled experimental assets | classify every delta as token, UI component, pattern component, or one-off |
| interface-designer | do not edit UI source from this seminar | wait for accepted RFC and implementation claim |
| ux-evaluator | require user-like navigation evidence after implementation | beta pass must include desktop/mobile, recovery, empty, and interrupted states |

## Decision

Selected direction: `operator_attention_graph`.

The next visual exploration should make Agent Runtime feel less like separate
panes and more like a relationship-aware operating surface. The primary target
screen is the console workflow that moves from backlog or taskset status into
claim evidence, wiki context, graph context, and command readiness. The current
design is useful, dense, and evidence-first, but its repeated card/list language
does not yet make relationships between taskset ownership, evidence freshness,
graph nodes, and safe commands immediately visible.

The RFC should explore:

- topology-first context panels that connect tasksets, claims, evidence records,
  wiki pages, and graph nodes;
- stronger attention hierarchy for blocked, watch, and next-action states;
- compact relationship chips and graph-adjacent evidence previews;
- light-theme-first composition that preserves the accepted operator-console
  density and optional dark mode.

## Alternatives

| Option | Decision | Rationale |
| --- | --- | --- |
| `operator_attention_graph` | selected | best match for current wiki/graph/evidence goals and likely to create reusable pattern assets |
| `visual_refresh_only` | rejected | would change surface polish without improving operator decision flow |
| `dashboard_kpi_layer` | rejected | risks generic SaaS composition and pushes evidence/context behind summary metrics |

## Quality Checklist

| Quality Dimension | Evidence Required | Likely Assetization Class |
| --- | --- | --- |
| Typography | define hierarchy for graph node labels, evidence previews, and command readiness labels | `design_token` |
| Size / spacing | define compact but readable graph-adjacent panel spacing for desktop and mobile | `design_token` |
| Color | preserve semantic pass/watch/block/status meaning and add no raw colors outside tokens | `design_token` |
| Motion | use restrained focus/selection transitions only when they clarify relationship traversal | `design_token` |
| Effects | keep elevation shallow; use focus rings and link traces instead of decorative depth | `design_token` |
| Schema | define data fields needed for taskset/evidence/wiki/graph relationship previews | `pattern_component` |
| Assets | promote recurring relation chips, evidence preview rows, and graph-context panels | `ui_component`, `pattern_component` |
| Accessibility | require visible labels, keyboard traversal, focus order, and non-color-only state | `ui_component` |
| Responsiveness | verify a narrow viewport path where graph context becomes stacked relationship lists | `pattern_component` |
| Interaction | cover empty graph, stale evidence, blocked command, and interrupted claim recovery states | `pattern_component` |

## Risk

- Risk: a broad visual redesign could bypass the design-system gate if it starts
  directly in `ui_console_assets.py`.
- Risk: graph/wiki enthusiasm could produce decorative links instead of
  decision-useful relationships.
- Guardrail: the RFC must name exact source targets and keep implementation in
  a later W0-W6 claim.

## Next

- Draft `reviews/RFC-2026-06-19-ui-ux-design-direction.md`.
- Proposed RFC target files: `docs/design/agent-runtime/DESIGN.md`,
  `docs/design/agent-runtime/DESIGN-SYSTEM.md`, and the RFC record itself.
- Proposed later implementation targets, only after RFC acceptance:
  `src/agent_runtime/ui_design_assets.py`,
  `src/agent_runtime/ui_console_assets.py`, focused UI tests, and visual/beta
  evidence records.
