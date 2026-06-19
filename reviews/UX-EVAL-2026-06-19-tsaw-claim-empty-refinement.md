---
type: ux-evaluation
id: UX-EVAL-2026-06-19-tsaw-claim-empty-refinement
audience: owner
status: accepted
signal: pass
score: 89
priority: High
date: 2026-06-19
generated_at: 2026-06-19T23:16:42+09:00
task_set_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
task_id: TASK-AR-615
unit_id: UNIT-TASK-AR-615-001
claim_id: CLAIM-20260619-225813-task-ar-615-task-ar-615-tsaw-beta-ux
source_task_id: TASK-AR-614
participants:
  - ux-evaluator
  - beta-tester
  - design-system-steward
tags: [ui, ux, evaluation, design-system, taskset-board, attention-workspace]
---

# TSAW Claim And Empty State Refinement UX Evaluation

## Bottom Line

- Result: UX accepted. The refinement closes the two user-visible failures from the previous beta pass.
- Active-claim trust is restored: the top-priority lane now surfaces live claimed work and the selected relation panel names the claiming agent.
- Empty-lane recovery is clearer: zero-count lanes no longer borrow copy that implies work exists.
- Next cycle: run a lead-designer seminar for the broader Taskset Board evidence-gap and performance-aware IA problem.

## Signal

| Dimension | Result | Evidence |
| --- | --- | --- |
| Typography | pass | Long taskset ids, task titles, claim labels, evidence labels, and command labels wrapped inside desktop and mobile Taskset Board containers. |
| Size and spacing | pass | Desktop width stayed `1440`; mobile active Taskset Board stayed within `390` document/body width with no scoped `#view-tsboard` wide children. |
| Color and non-color cues | pass | State remained textual: `Taskset active`, `Claim path claimed by ux_evaluator@work-01`, `Evidence freshness stale`, `Command readiness claim guard`. |
| Motion | pass | Reduced-motion run returned `prefersReducedMotion=true`; active claim state and selected detail stayed available without animation. |
| Effects | pass | Lane clicks, quick switcher input, `Enter`, `ArrowDown`, selected result focus, and fallback filtering all had recoverable state changes. |
| Schema | pass | Workspace derivation now includes `task_claims[].task_set_id`; API returned `active_claims=1` with selected taskset `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`. |
| Assets | pass | The fix is correctly expressed through Taskset Board state derivation plus `patternTasksetAttentionLane` empty copy; no page-local one-off was needed in this evaluation. |
| Accessibility | pass | Keyboard result focus lands on `.tsboard-switcher-result.is-selected`; active and empty states are conveyed through text, not only color. |
| Responsiveness | pass | Mobile `390x844` paths for active claim, zero-count ready-next, known-target retrieval, and reduced motion did not create Taskset Board horizontal overflow. |
| Interaction | pass | Unknown/current work discovery, known-target retrieval, empty recovery, fallback search, and claim-state reading work together. |

## UX Detail

### Interaction

- Active work path: click `active_claims` -> one card appears for `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT` -> selected relation says `Claim path claimed by ux_evaluator@work-01`.
- Empty recovery path: click `ready_next` with count `0` -> card list clears -> empty copy says `No unclaimed ready-next tasksets are currently surfaced.`
- Known target path: type `TASK-AR-615` -> press `Enter` -> selected detail remains the refinement taskset and shows the active claim state.
- Keyboard path: type `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT` -> press `ArrowDown` -> focus moves to the selected switcher result button.
- Fallback path: type `TASKSET-AR-TSAW` in the full-board filter -> one fallback card remains, the refinement taskset.

### Typography, Size, And Layout

- Desktop: `innerWidth=1440`, `docScrollWidth=1440`, `bodyScrollWidth=1440`.
- Mobile: `innerWidth=390`, `docScrollWidth=390`, `bodyScrollWidth=390`.
- Mobile active Taskset Board scoped scan: `#view-tsboard` wide children `[]`.
- Mobile primary panels measured `332px` wide in a `390px` viewport during active and empty lane runs.
- The selected detail panel is tall because it includes relation rows and child graph rows; that is vertical density, not overflow.

### Color, Effects, And State

- Claim state is not color-dependent. The label explicitly says `claimed by ux_evaluator@work-01`.
- Empty state is not icon-only. The lane-specific copy names the absent class of work.
- Stale evidence remains textual and visible as `Evidence freshness stale`.
- Command readiness remains textual and visible as `claim guard`.

### Motion

- Reduced-motion mobile run returned `prefersReducedMotion=true`.
- The same active-claim lane and selected detail remained readable.
- No meaning was encoded only in transition, animation, or visual movement.

### Schema And Data Contract

- `taskset_attention_workspace/v1` now selects the refinement taskset while its live task claim exists.
- API lane counts in the live claimed state: `active_claims=1`, `guarded_recovery=5`, `evidence_gaps=49`, `recently_changed=3`, `ready_next=0`.
- `derived_from` includes `claim_summary.state`, `claim_summary.label`, `claim_summary.command_state`, `claim_summary.command_label`, and `task_claims[].task_set_id`.
- The previous root mismatch is no longer reproduced.

### Accessibility

- The active claim and empty states are screen-reader friendly relative to the previous pass because their meaning is explicit text.
- The quick switcher can be operated from keyboard with `Enter` and `ArrowDown`.
- Focus recovery was observed on `.tsboard-switcher-result.is-selected`.
- Remaining accessibility follow-up should focus on the broader `evidence_gaps=49` overload and how many stale items are announced, not the fixed claim/empty states.

## Defect Routing

| BTC ID | UX impact | Current decision |
| --- | --- | --- |
| BTC-TSAW-CLAIM-001 | Operators could not trust active claim discovery. | Closed. Live claim data now appears in lane, selected detail, and relation text. |
| BTC-TSAW-EMPTY-001 | Zero-count lane copy implied non-empty activity. | Closed. Empty state now communicates absence and recovery context. |

## Next Design Candidate

| Candidate | Why now | Suggested first artifact |
| --- | --- | --- |
| Evidence-gap overload IA | `evidence_gaps=49` dominates the attention workspace and can bury higher-quality next actions. | Lead-designer seminar plus RFC for stale-evidence grouping, lane caps disclosure, and progressive drill-in. |
| Performance-aware UI state loading | `/api/tasksets_board` can be several seconds on current repo state; full `/api/state` is heavier. | Meeting with runtime + UI roles to split first-screen board data from slow secondary panels. |
| Inactive-view layout containment | Full-page scans can still report wide inactive inbox elements even when document width is safe. | Beta spike to distinguish user-visible overflow from inactive DOM measurement noise. |

## Insight

- The smaller refinement cycle is complete enough to move back up a level. Another tactical patch would be less valuable than a lead-designer pass on evidence overload and latency.
- The UI agent split is now working as intended: beta found the issue, interface implementation fixed it, and UX evaluation closed the loop with a next design direction.
- The next seminar should explicitly cover font density, lane count disclosure, state schema, data loading budget, reduced-motion behavior, and pattern asset ownership.

## Decision

Close the focused `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT` after W4b. Continue the larger UI refactor loop by registering a new seminar-led taskset for evidence-gap overload and performance-aware Taskset Board IA.

## Action Board

| Action | Owner | State |
| --- | --- | --- |
| Accept active-claim refinement | ux-evaluator | done |
| Accept empty-lane copy refinement | ux-evaluator | done |
| Preserve this evaluation for W4b | ux-evaluator | done |
| Start next lead-designer seminar on evidence overload and latency | lead-designer | recommended |

