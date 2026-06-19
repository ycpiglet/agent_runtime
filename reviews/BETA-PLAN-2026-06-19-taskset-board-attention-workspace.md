---
type: ui-beta-test-plan
id: BETA-PLAN-2026-06-19-taskset-board-attention-workspace
status: accepted
signal: pass
score: 86
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
task_id: TASK-AR-611
claim_id: CLAIM-20260619-182000-task-ar-611-task-ar-611-implementation-beta
source_rfc: RFC-2026-06-19-taskset-board-ia-design-direction
tags: [ui, ux, beta-tester, taskset-board, evaluation]
---

# Taskset Board Attention Workspace Beta Plan

## Bottom Line

- Summary: define the beta-tester and UX-evaluator evidence required after the
  first `taskset_attention_workspace` implementation lands.
- Result: beta evidence must record real actions, recovery attempts, viewports,
  keyboard traversal, reduced-motion behavior, and BTC-style defect routing.
- Boundary: this is an evidence plan only. Source fixes belong in later claimed
  implementation work.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| User-like path | pass | Unknown-target discovery and known-target retrieval are action paths, not screenshot checks. |
| Recovery coverage | pass | Empty lane, stale evidence, blocked command, interrupted claim, expired claim, and no active claim states are required. |
| Viewport coverage | pass | Desktop and 390x844 mobile notes are required. |
| Accessibility coverage | pass | Keyboard order, labels, focus visibility, reduced motion, and non-color-only state are required. |
| Defect routing | pass | Every visible defect gets a BTC-TSAW id and reproduction path. |

## Decision

The beta pass must be exploratory and action-based. Screenshot-only evidence is
not sufficient. The evaluator must prove that a user can discover important
tasksets from the first viewport, retrieve a known target through the switcher,
inspect relation detail, and return to the full board without losing quiet
work.

## Action

| Role | Required action | Evidence output |
| --- | --- | --- |
| beta-tester | execute user-like action paths | `reviews/BETA-TEST-2026-06-19-taskset-board-attention-workspace.md` |
| ux-evaluator | evaluate accessibility, responsive behavior, recovery clarity, and reduced motion | `reviews/UX-EVAL-2026-06-19-taskset-board-attention-workspace.md` |
| interface-designer | read defects only after evaluation is complete | follow-up task registration, not direct unclaimed fixes |
| design-system-steward | classify whether defects are token, component, pattern, or one-off issues | follow-up assetization notes |

## Required Flows

| Flow | Required actions | Expected observation |
| --- | --- | --- |
| Unknown-target discovery | Open Taskset Board, inspect first-viewport attention lanes, select one lane card by click or keyboard. | Card reason explains why the taskset is active, guarded, stale, recently changed, or ready. |
| Known-target retrieval | Type a taskset id, title fragment, alias, task id, or owner into the switcher and jump to the result. | Result count, selected state, and empty state are visible; focus does not require scanning all tasksets. |
| Relation detail | Open selected taskset detail and inspect claim path, evidence freshness, graph or child context, and command readiness. | Detail uses visible labels and preserves existing OAG relation semantics. |
| All-tasksets fallback | Move from attention workspace to the full board/searchable fallback. | Quiet tasksets remain discoverable and keyboard reachable. |
| Mobile path | Repeat unknown-target and known-target flows at 390x844. | Lanes, switcher, and detail stack without document-level horizontal overflow. |
| Reduced motion | Enable reduced-motion mode or emulate it if supported, then repeat lane selection and switcher jump. | No meaning depends on movement. |

## Recovery Matrix

| State | Required attempt | Failure ID rule |
| --- | --- | --- |
| empty lane | Navigate to or simulate a lane with no members. | `BTC-TSAW-EMPTY-###` |
| stale evidence | Inspect a stale or missing evidence lane/card. | `BTC-TSAW-STALE-###` |
| blocked command | Inspect a blocked command readiness state. | `BTC-TSAW-BLOCKED-###` |
| interrupted claim | Inspect a claim with interrupted or incomplete lifecycle state. | `BTC-TSAW-INTERRUPT-###` |
| expired claim | Inspect an expired or reaped claim path. | `BTC-TSAW-EXPIRED-###` |
| no active claim | Inspect a taskset with no current claim. | `BTC-TSAW-NOCLAIM-###` |
| focus recovery | Move focus into and out of lane controls, switcher, cards, detail, and fallback list. | `BTC-TSAW-FOCUS-###` |
| mobile overflow | Repeat primary flows at 390x844 and inspect horizontal scroll. | `BTC-TSAW-MOBILE-###` |

## Evidence Template

Each beta observation must include:

- environment: OS, browser or local UI mode, viewport, theme, data fixture or
  live repo state;
- action path: exact clicked, typed, or keyboard steps;
- expected result;
- observed result;
- pass/fail status;
- screenshot or trace reference when available;
- BTC-TSAW defect id for failures;
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

| Risk | Guardrail |
| --- | --- |
| Beta evidence becomes a checklist without real interaction. | Every row must include an action path. |
| Visible defects are fixed without a claim. | Defects become BTC-TSAW follow-up candidates first. |
| Accessibility is reduced to color contrast only. | Labels, keyboard order, focus visibility, reduced motion, and non-color-only state are all required. |
| Quiet work disappears behind attention lanes. | All Tasksets fallback must be tested as a required flow. |

## Next

- Register and run the source-mutating implementation task first.
- Run this beta/UX evaluation after implementation is merged or available in a
  claimed verification worktree.
- Feed defects and evaluator notes back into the next UI/UX cycle proposal.
