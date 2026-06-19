---
type: ux-evaluation
id: UX-EVAL-2026-06-19-taskset-board-attention-workspace
audience: owner
status: accepted-with-findings
signal: watch
score: 80
priority: High
date: 2026-06-19
generated_at: 2026-06-19T21:40:53+09:00
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
task_id: TASK-AR-613
unit_id: UNIT-TASK-AR-613-001
claim_id: CLAIM-20260619-205629-task-ar-613-task-ar-613-taskset-board-attention-beta
source_task_id: TASK-AR-612
participants:
  - ux-evaluator
  - beta-tester
  - design-system-steward
tags: [ui, ux, evaluation, design-system, taskset-board, attention-workspace]
---

# Taskset Board Attention Workspace UX Evaluation

## Bottom Line

- Result: UX accepted with findings. The attention workspace creates a real first-screen taskset-navigation surface, but the active-claim data contract and empty-lane recovery copy need a follow-up implementation task.
- Strongest pass: known-target retrieval through the quick switcher works on desktop and mobile and avoids scanning `51` tasksets.
- Strongest issue: `active_claims` is the highest-value lane, but live runtime status can report an active claim while the lane still shows `0`.

## Signal

| Dimension | Result | Evidence |
| --- | --- | --- |
| Typography | pass | Long taskset ids, task titles, relation labels, and chips wrap inside desktop and mobile containers. Mobile target width stayed `332px` in a `390px` viewport. |
| Size and spacing | pass | Mobile `.tsboard-workspace-top` collapsed to one `332px` column; switcher and detail both measured `332px`; no document-level overflow. |
| Color and non-color cues | pass | State is textual: `Taskset active`, `Claim path released`, `Evidence freshness stale`, `Command readiness proposal ready`, `Claim path 1 guarded`. |
| Motion | pass | Reduced motion returned `true`; selected taskset labels and widths were preserved with no movement-dependent meaning. |
| Effects | pass with watch | Focus visibility and hover/focus affordances exist for switcher results, lane buttons, and relation panels. Dense lane-card counts may still benefit from a clearer selected-card affordance in a future cycle. |
| Schema | fail | `work.py status` showed active `TASK-AR-613`; root `/api/tasksets_board` still returned `active_claims=0`. |
| Assets | pass with findings | `componentTasksetQuickSwitcher`, `componentAttentionLaneFilter`, and `patternTasksetAttentionLane` are the right asset layers. `BTC-TSAW-EMPTY-001` belongs in the lane pattern, not a page-local one-off. |
| Accessibility | pass with watch | Switcher supports `combobox`, `ArrowDown`, `Enter`, focusable result, focusable relation panel, and lane tab buttons. Empty lanes need clearer text for screen-reader users. |
| Responsiveness | pass | Desktop and mobile widths matched viewport widths; mobile had no wide children. |
| Interaction | pass with findings | Unknown-target discovery, known-target retrieval, guarded/stale inspection, empty lane recovery, and fallback search all functioned. Active claim discovery is blocked by stale derivation. |

## UX Detail

### Interaction

- Unknown-target path: click `ready_next` -> click first attention card -> selected detail becomes `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE`.
- Known-target path: type `TASK-AR-613` -> result list returns the target taskset -> press `Enter` -> selected detail shows the target.
- Recovery path: click `guarded_recovery` and `evidence_gaps`; both lanes expose textual reasons and relation detail.
- Empty path: click `active_claims` and `recently_changed`; recovery works structurally, but the empty copy implies non-empty activity.
- Fallback path: type `attention workspace` in the full-board filter; fallback card count becomes `1`.

### Typography, Size, And Layout

- Desktop: `innerWidth=1440`, `docScrollWidth=1440`, `bodyScrollWidth=1440`.
- Mobile: `innerWidth=390`, `docScrollWidth=390`, `bodyScrollWidth=390`.
- Mobile top workspace: `topColumns=332px`, `topWidth=332`, `switcherWidth=332`, `detailWidth=332`.
- Mobile wide-child scan returned an empty list.
- Desktop wide-child scan found only expected input text scroll behavior after a long query, not document overflow.

### Color, Effects, And State

- The relation chips do not require color interpretation: labels name Taskset, Claim path, Evidence freshness, and Command readiness.
- Guarded state is visible as text: `1 guarded` and `claim guard review`.
- Empty lane states are visually reachable and use a missing/empty chip, but their reason copy should be state-specific.

### Motion

- Reduced-motion mode returned `prefersReducedMotion=true`.
- Reduced-motion mobile path preserved `docScrollWidth=390`, `bodyScrollWidth=390`, and the selected target relation labels.
- `.tsboard-workspace` transition duration was effectively zero (`1e-06s`) in the reduced-motion run.

### Schema And Data Contract

- The attention workspace schema is present as `taskset_attention_workspace/v1`.
- Data derivation reports lanes from `claim_summary`, `recent_activity`, child phase/relation state, progress, status bucket, and assigned agents.
- Runtime cross-check failed: root `work.py status` reported `active_claims=1` for `CLAIM-20260619-205629-task-ar-613-task-ar-613-taskset-board-attention-beta`, while root `/api/tasksets_board` reported `active_claims=0` and `selected_taskset_id=null`.
- This is a schema/data freshness problem, not a visual styling problem.

### Accessibility

- The switcher exposes a search input with `role=combobox`, result list, result count, and selected chip.
- Keyboard path proved focus moves from `#tsboard-switcher` to `.tsboard-switcher-result.is-selected`.
- The relation panel is focusable (`section.attention-relation-panel`), and `Tab` moves onward to lane filter buttons.
- Empty state copy must be improved because screen-reader users get the same contradictory message as visual users.

## Defect Routing

| BTC ID | UX impact | Assetization class | Decision |
| --- | --- | --- | --- |
| BTC-TSAW-CLAIM-001 | Operators cannot trust the `active_claims` lane as the top-priority work surface when live claims exist. | schema / pattern_component | Register implementation refinement; merge live task_claims into board derivation or refresh classification before render. |
| BTC-TSAW-EMPTY-001 | Zero-count lanes communicate stale/non-empty reasons and can mislead users during recovery. | pattern_component | Fix `patternTasksetAttentionLane` empty-state copy so zero-count lanes say no matching tasksets exist and preserve lane purpose separately. |

## Insight

- The UI/UX role split is now doing useful work: implementation produced reusable assets, beta found user-visible behavior, and UX evaluation isolated schema vs pattern follow-ups.
- This is not the moment for a new lead-designer seminar. The next best step is a focused implementation refinement, then another beta pass.
- After those two defects close, a lead-designer seminar should revisit the next broader design direction: reducing evidence-gap overload and deciding whether lane caps need disclosure or pagination.

## Decision

Accept the attention workspace as the current Taskset Board navigation direction, but do not mark the taskset mature. The next cycle should implement `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001`, then rerun beta/UX evidence before proposing another visual or IA direction.

## Action Board

| Action | Owner | State |
| --- | --- | --- |
| Treat quick switcher, lane filter, selected relation detail, and fallback as UX-accepted patterns | ux-evaluator | done |
| Register active-claim freshness refinement | lead-engineer / interface-designer | recommended |
| Register empty-lane copy refinement | interface-designer / design-system-steward | recommended |
| Preserve mobile and reduced-motion checks for the next beta pass | beta-tester | recommended |

## Risks / Blockers

- Risk: live `/api/state` and `/api/tasksets_board` are slow enough that browser verification needed static asset injection for render/event testing.
- Risk: interrupted and expired claim states were not present in the current board data, so the next implementation task should include a fixture or derived test for those states.
- Risk: `evidence_gaps=51` with only `8` rendered lane cards may be acceptable density management, but it needs explicit disclosure if users interpret count as all visible cards.

## Next Steps

- Run W4a gates and independent W4b verification for `TASK-AR-613`.
- Close `TASK-AR-613` only after W4b passes.
- Register the next source-mutating implementation cycle for `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001`.
