---
type: ui-beta-test-plan
id: BETA-PLAN-2026-06-19-operator-attention-graph
status: accepted
signal: pass
score: 84
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
task_id: TASK-AR-602
source_rfc: RFC-2026-06-19-ui-ux-design-direction
tags: [ui, ux, beta-tester, evaluation]
---

# Operator Attention Graph Beta Plan

## Bottom Line

- Summary: define the beta-tester and UX-evaluator evidence required after the
  first `operator_attention_graph` implementation lands.
- Result: beta evidence must record real actions, recovery attempts, viewports,
  accessibility checks, and BTC-style defect routing.
- Boundary: this is an evidence plan only; source fixes belong in later claimed
  implementation work.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| User-like path | pass | click or keyboard route from taskset attention to claim/evidence/context/command readiness is required |
| Recovery coverage | pass | empty graph, stale evidence, blocked command, and interrupted claim states are required |
| Viewport coverage | pass | desktop and mobile notes are required |
| Accessibility coverage | pass | labels, focus order, reduced motion, and non-color-only state are required |
| Defect routing | pass | every visible defect gets a BTC-style ID and reproduction path |

## Action

| Role | Required action | Evidence output |
| --- | --- | --- |
| beta-tester | execute user-like action paths | `reviews/BETA-TEST-2026-06-19-operator-attention-graph.md` |
| ux-evaluator | evaluate accessibility, responsive behavior, and recovery clarity | `reviews/UX-EVAL-2026-06-19-operator-attention-graph.md` |
| interface-designer | read defects only after evaluation is complete | follow-up task registration, not direct unclaimed fixes |
| design-system-steward | classify whether defects are token, component, pattern, or one-off issues | follow-up assetization notes |

## Decision

The beta pass must be exploratory and action-based. Screenshot-only evidence is
not sufficient.

Minimum flows:

| Flow | Required actions | Expected observation |
| --- | --- | --- |
| taskset attention to claim evidence | click or keyboard-select a taskset/attention item, open related claim/evidence preview, return to current item | current taskset remains anchored; relation state has visible labels |
| evidence to graph/wiki context | open related wiki or graph context from evidence preview | context is visible without hiding evidence freshness |
| command readiness | inspect safe, blocked, and interrupted command states | command state explains why action is safe or blocked |
| narrow viewport | repeat the main path under mobile width | graph context becomes a stacked relation list without losing evidence or command state |

## Recovery Matrix

| State | Required attempt | Failure ID rule |
| --- | --- | --- |
| empty graph | navigate to an item with no graph context or simulate empty graph data if supported | `BTC-OAG-EMPTY-###` |
| stale evidence | inspect a stale or missing evidence relation | `BTC-OAG-STALE-###` |
| blocked command | inspect a blocked command readiness state | `BTC-OAG-BLOCKED-###` |
| interrupted claim | inspect a claim with interrupted or incomplete lifecycle state | `BTC-OAG-INTERRUPT-###` |
| focus recovery | move focus into and out of relation chips/panels by keyboard | `BTC-OAG-FOCUS-###` |

## Evidence Template

Each beta observation must include:

- environment: OS, browser or local UI mode, viewport, theme, data fixture or
  live repo state;
- action path: exact clicked or typed steps;
- expected result;
- observed result;
- pass/fail status;
- screenshot or trace reference when available;
- BTC-style defect ID for failures;
- follow-up owner and assetization class when the failure is actionable.

## Verification

The evaluation task must run:

```bash
python scripts/design_system_gate.py --check --all-ui
python scripts/evidence_index_generator.py --check
python scripts/ui_ux_cycle.py --root . assess --json
```

The evaluator should also run any focused UI test command recorded by the
implementation task.

## Risk

- Risk: beta evidence becomes a checklist without real interaction. Guardrail:
  every row must include an action path.
- Risk: visible defects are fixed without a claim. Guardrail: defects become
  BTC-style follow-up candidates first.
- Risk: accessibility is reduced to color contrast only. Guardrail: labels,
  keyboard order, focus visibility, reduced motion, and non-color-only state are
  all required.

## Next

- Register and run the source-mutating implementation task first.
- Run this beta/UX evaluation after implementation is merged or available in a
  claimed verification worktree.
- Feed defects and evaluator notes back into the next UI/UX cycle proposal.
