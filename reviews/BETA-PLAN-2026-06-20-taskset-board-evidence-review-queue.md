---
type: ui-beta-test-plan
id: BETA-PLAN-2026-06-20-taskset-board-evidence-review-queue
status: accepted
signal: pass
score: 89
priority: High
date: 2026-06-20
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
task_id: TASK-AR-618
claim_id: CLAIM-20260620-010012-task-ar-618-task-ar-618-evidence-perf-implementation-plan
source_rfc: RFC-2026-06-19-taskset-board-evidence-performance-ia
tags: [ui, ux, beta-tester, taskset-board, evidence-review-queue, evaluation]
---

# Taskset Board Evidence Review Queue Beta Plan

## Bottom Line

- Summary: define the beta-tester and UX-evaluator evidence required after the first evidence review queue implementation lands.
- Result: beta evidence must record real actions, recovery attempts, viewports, keyboard traversal, reduced-motion behavior, API latency observation, and BTC-style defect routing.
- Boundary: this is an evidence plan only. Source fixes belong in later claimed implementation work.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| User-like action path | pass | Unknown triage, known retrieval, capped drill-in, retry/defer, keyboard, and mobile paths are specified as actions. |
| Detail latency | pass | Summary age, detail loading, stale summary, timeout-watch, and retryable labels must be observed or simulated. |
| Accessibility | pass | Keyboard order, focus visibility, labels, count announcements, reduced motion, and non-color-only state are required. |
| Responsiveness | pass | Desktop and 390x844 evidence must distinguish active Taskset Board fit from inactive DOM scan noise. |
| Defect routing | pass | Every visible defect gets a BTC-TSERQ id, reproduction path, and assetization class. |

## Required Flows

| Flow | Required actions | Expected observation |
| --- | --- | --- |
| Unknown evidence triage | Open Taskset Board, inspect evidence review group summary, select highest priority group, then select a queue row. | Group label, count, hidden count, ordering reason, selected row, and detail state are visible without reading every stale item. |
| Known target retrieval | Type a taskset id/title fragment into the Taskset Board search or switcher, then open the matching queue/detail row. | Search narrows tasksets and selected evidence detail remains coherent. |
| Capped group drill-in | Open a group with more rows than the visible cap. | Visible count, hidden count, cap reason, and drill-in affordance are labelled. |
| Detail loading | Select a row while detail is loading or represented as summary-ready. | Summary controls remain usable and selected detail names its loading/freshness state. |
| Timeout/retry | Trigger, simulate, or fixture a timeout-watch/retryable state. | Retry control is keyboard reachable and text explains what failed. |
| Defer/action | Use or inspect retry/defer/action affordances. | Controls are labelled and do not imply unsafe write execution. |
| Empty group | Navigate to a group with no items, or fixture one. | Empty state distinguishes group purpose from current absence. |
| Claim recovery | Inspect blocked command, interrupted claim, expired claim, no active claim, and active claim states where available. | State is textual, non-color-only, and preserves claim/command readiness meaning. |
| Keyboard traversal | Move through group filters, cap disclosure, queue rows, selected detail, retry/defer controls, and fallback list. | Focus order is predictable and visible. |
| Mobile path | Repeat unknown triage and known retrieval at 390x844. | Summary, queue, and detail stack without document-level horizontal overflow. |
| Reduced motion | Enable or emulate reduced motion and repeat drill-in plus detail selection. | No meaning depends on animation. |

## Evidence Template

Each beta observation must include:

- environment: OS, browser or local UI mode, viewport, theme, data fixture or live repo state;
- action path: exact clicked, typed, or keyboard steps;
- expected result;
- observed result;
- pass/fail status;
- screenshot or trace reference when available;
- latency note for `/api/tasksets_board` and detail loading state;
- BTC-TSERQ defect id for failures;
- follow-up owner and assetization class when the failure is actionable.

## UX Evaluation Matrix

| Dimension | Review requirement |
| --- | --- |
| Typography | Group headings, queue rows, taskset ids, counts, latency labels, and detail text wrap or truncate predictably. |
| Size and spacing | Filters, caps, rows, badges, and controls keep stable dimensions and touch targets at desktop and 390x844. |
| Color | Freshness, severity, loading, and command readiness reuse semantic tokens and include text labels. |
| Motion | Drill-in, loading, retry, and selected states preserve meaning with reduced motion. |
| Effects | Focus, hover, selected, loading, timeout, and retry states are visible without decorative effects. |
| Schema | Required queue fields and summary/detail split are visible in API payload or fixture evidence. |
| Assets | Token, UI component, pattern component, and one-off classes are confirmed or defects are routed. |
| Accessibility | Labels, count announcements, empty states, retry states, focus order, and screen-reader-visible state are explicit. |
| Responsiveness | Active Taskset Board viewport fits; inactive DOM scan noise is noted separately. |
| Interaction | Unknown triage, known search, capped drill-in, slow loading, timeout/retry, stale/blocked/interrupted/empty states are exercised. |

## Failure ID Rules

| Failure class | ID prefix | Examples |
| --- | --- | --- |
| Evidence grouping or cap issue | `BTC-TSERQ-GROUP-###` | Hidden count wrong, ordering reason missing, group label vague. |
| Loading or latency issue | `BTC-TSERQ-LATENCY-###` | Blank detail, stale summary looks fresh, retry unreachable. |
| Keyboard or focus issue | `BTC-TSERQ-FOCUS-###` | Row focus lost, filter cannot be reached, focus hidden. |
| Mobile or responsive issue | `BTC-TSERQ-MOBILE-###` | Horizontal overflow, clipped row, button text overflow. |
| Accessibility or non-color issue | `BTC-TSERQ-A11Y-###` | State only conveyed by color, missing labels, count not announced. |
| Schema or data issue | `BTC-TSERQ-SCHEMA-###` | Required field missing, command readiness ambiguous, claim state wrong. |
| Assetization issue | `BTC-TSERQ-ASSET-###` | Repeated markup not promoted, token drift, one-off copy reused. |

## Verification

The evaluation task must run:

```bash
python scripts/design_system_gate.py --check --all-ui
python scripts/evidence_index_generator.py --check
python scripts/ui_ux_cycle.py --root . assess --json
```

The evaluator should also run any focused UI test command recorded by the implementation task.

## Risk

| Risk | Guardrail |
| --- | --- |
| Beta evidence becomes checklist-only. | Every observation needs a clicked, typed, or keyboard action path. |
| Slow state cannot be reproduced. | Record fixture/simulation limits and route missing instrumentation as BTC-TSERQ-LATENCY. |
| Defects are fixed without a claim. | Defects become BTC follow-up candidates first. |
| Accessibility is reduced to contrast only. | Labels, keyboard order, focus visibility, reduced motion, count announcements, and non-color-only state are all required. |
| The queue hides quiet work. | All Tasksets fallback remains a required verification path. |

## Next

- Register and run the source-mutating implementation task first.
- Run this beta/UX evaluation after the implementation is merged or available in a claimed verification worktree.
- Feed defects and evaluator notes back into the next UI/UX cycle proposal.
