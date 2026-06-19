---
type: beta-tester-review
id: BETA-TEST-2026-06-19-tsaw-claim-empty-refinement
audience: owner
status: accepted
signal: pass
score: 91
priority: High
date: 2026-06-19
generated_at: 2026-06-19T23:16:42+09:00
task_set_id: TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT
task_id: TASK-AR-615
unit_id: UNIT-TASK-AR-615-001
claim_id: CLAIM-20260619-225813-task-ar-615-task-ar-615-tsaw-beta-ux
source_task_id: TASK-AR-614
participants:
  - beta-tester
  - ux-evaluator
tags: [ui, ux, beta-tester, evidence, taskset-board, attention-workspace]
---

# TSAW Claim And Empty State Refinement Beta Test

## Bottom Line

- Result: accepted. `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001` are closed in the refined Taskset Board attention workspace.
- Strongest pass: with live `TASK-AR-615` claimed, `/api/tasksets_board` reported `active_claims=1`, selected `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`, and the DOM rendered the active lane card as `claimed by ux_evaluator@work-01`.
- Recovery pass: zero-count `ready_next` rendered `No unclaimed ready-next tasksets are currently surfaced.` instead of the old contradictory non-empty reason copy.
- Boundary: this was evaluation-only. No UI source files were changed.

## Environment Notes

- OS: Windows local checkout.
- Browser automation: Python Playwright, Chromium headless.
- Browser skill note: in-app browser `iab` was unavailable in this session, so local Playwright was used as fallback.
- Root UI server: `http://127.0.0.1:8774`.
- UI server process: Python PID `44796`.
- Evaluation root: `C:\Users\ycpig\agent_runtime`.
- Evaluation worktree: `.worktrees/TASK-AR-615` on branch `codex/task-ar-615-work-01`.
- Claim under test: `CLAIM-20260619-225813-task-ar-615-task-ar-615-tsaw-beta-ux`.
- Data state: `/api/tasksets_board` returned `52` cards and derived the workspace from `task_claims[].task_set_id`.
- Attention lanes: `active_claims=1`, `guarded_recovery=5`, `evidence_gaps=49`, `recently_changed=3`, `ready_next=0`.
- Desktop viewport: `1440x900`.
- Mobile viewport: `390x844`.
- Reduced motion: Playwright `reduced_motion=reduce`; `matchMedia('(prefers-reduced-motion: reduce)')` returned `true`.
- Polling control: browser run disabled the 4s polling interval so repeated render swaps could not detach elements during click assertions.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Active claim freshness | pass | `work.py status` showed one active `TASK-AR-615` claim; `/api/tasksets_board` reported `active_claims=1` and selected `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`. |
| Active lane rendering | pass | Clicking `active_claims` rendered one lane card: `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT ... claimed by ux_evaluator@work-01`. |
| Empty lane recovery | pass | Clicking zero-count `ready_next` rendered no cards and the empty copy `No unclaimed ready-next tasksets are currently surfaced.` |
| Known-target retrieval | pass | Typed `TASK-AR-615` in the quick switcher and pressed `Enter`; selected detail remained the refinement taskset with active claim text. |
| Keyboard traversal | pass | Typed `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`, pressed `ArrowDown`, and focus moved to `.tsboard-switcher-result.is-selected`. |
| Fallback search | pass | Typed `TASKSET-AR-TSAW`; fallback board card count became `1` and the first card was the refinement taskset. |
| Desktop width | pass | `innerWidth=1440`, `documentElement.scrollWidth=1440`, `body.scrollWidth=1440`, no wide children in the desktop pass. |
| Mobile Taskset Board width | pass | `innerWidth=390`, `documentElement.scrollWidth=390`, `body.scrollWidth=390`, and scoped `#view-tsboard` wide-child scan returned `[]`. |
| Reduced motion | pass | Reduced-motion mobile path preserved active-claim state and `prefersReducedMotion=true`; no state depended on animation. |
| Console errors | pass | Playwright captured no browser console warnings or errors in the Taskset Board runs. |

## User-Like Actions

| ID | Viewport | Action path | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- | --- |
| TSAW-REFINE-BETA-001 | Root API | Create/hold `TASK-AR-615` claim -> request `/api/tasksets_board`. | Active claim lane includes the claimed taskset. | API returned `active_claims=1`, selected `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`, and included `task_claims[].task_set_id` in `derived_from`. | pass |
| TSAW-REFINE-BETA-002 | Desktop `1440x900` | Open Taskset Board -> click `active_claims`. | Claimed taskset appears as an attention card with textual claim reason. | One card rendered with `claimed by ux_evaluator@work-01`; selected detail showed `Claim path claimed by ux_evaluator@work-01`. | pass |
| TSAW-REFINE-BETA-003 | Desktop `1440x900` | Click zero-count `ready_next`. | Empty lane says no matching tasksets exist and gives recoverable context. | No cards rendered; empty copy read `No unclaimed ready-next tasksets are currently surfaced.` | pass |
| TSAW-REFINE-BETA-004 | Desktop `1440x900` | Type `TASK-AR-615` in quick switcher -> press `Enter`. | Known target retrieval selects the refinement taskset without scanning all tasksets. | Selected detail stayed on `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`; relation text preserved active claim, stale evidence, and command guard labels. | pass |
| TSAW-REFINE-BETA-005 | Desktop `1440x900` | Type full taskset id -> press `ArrowDown`. | Focus moves from switcher input to the selected result. | Active element was `BUTTON.tsboard-switcher-result.is-selected` with the refinement taskset text. | pass |
| TSAW-REFINE-BETA-006 | Desktop `1440x900` | Type `TASKSET-AR-TSAW` in the fallback board filter. | Full board fallback can still retrieve the target. | Visible fallback card count was `1`; first card was `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT`. | pass |
| TSAW-REFINE-BETA-007 | Mobile `390x844` | Click `active_claims`. | Active claim is readable without horizontal scroll. | Document/body scroll width stayed `390`; active card and selected detail remained visible. | pass |
| TSAW-REFINE-BETA-008 | Mobile `390x844` | Click zero-count `ready_next`. | Empty lane remains recoverable on mobile. | Document/body scroll width stayed `390`; empty copy matched the dedicated ready-next empty state. | pass |
| TSAW-REFINE-BETA-009 | Mobile `390x844` | Type `TASK-AR-615` -> press `Enter`. | Mobile known-target retrieval keeps selected state and readable labels. | Selected detail retained `Taskset active`, `Claim path claimed by ux_evaluator@work-01`, `Evidence freshness stale`, and `Command readiness claim guard`. | pass |
| TSAW-REFINE-BETA-010 | Mobile `390x844`, reduced motion | Enable reduced motion -> click `active_claims` -> type `TASK-AR-615` -> press `Enter`. | No meaning depends on motion. | `prefersReducedMotion=true`, document/body width stayed `390`, and active claim state remained textual. | pass |

## Recovery Attempts

| State | Attempt | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- |
| Active claim | Held the live `TASK-AR-615` claim while rendering Taskset Board. | Claim appears in `active_claims`. | Lane count `1`; card and relation panel named `claimed by ux_evaluator@work-01`. | closed |
| Zero ready-next lane | Clicked `ready_next` while count was `0`. | Empty copy communicates absence, not activity. | Dedicated empty copy displayed `No unclaimed ready-next tasksets are currently surfaced.` | closed |
| Guarded command | Inspected selected relation panel. | Command readiness remains textual. | Detail showed `Command readiness claim guard`. | pass |
| Stale evidence | Inspected selected relation panel. | Evidence status remains textual. | Detail showed `Evidence freshness stale` and `1/2 tasks complete; no recent activity`. | pass |
| Focus recovery | Pressed `ArrowDown` from switcher after a full taskset query. | Focus moves to the selected result. | Focus landed on `.tsboard-switcher-result.is-selected`. | pass |
| Mobile overflow | Repeated active and empty lane paths at `390x844`. | No document-level horizontal scroll and no Taskset Board wide child. | `docScrollWidth=390`, `bodyScrollWidth=390`, scoped `#view-tsboard` wide-child scan `[]`. | pass |

## Failure IDs

| BTC ID | Previous status | Current status | Evidence |
| --- | --- | --- | --- |
| BTC-TSAW-CLAIM-001 | open | closed | Live claim now drives `active_claims=1`, selected taskset fallback, lane card text, and relation detail. |
| BTC-TSAW-EMPTY-001 | open | closed | Zero-count lane now uses dedicated empty copy instead of the non-empty lane reason. |

## Watch Items

- The full-page mobile scan can still see inactive inbox card boxes wider than `390px`, but document/body scroll width remains `390` and the scoped active `#view-tsboard` scan returned no wide children. This is not routed as a Taskset Board defect.
- `/api/tasksets_board` response time varied from about `6.9s` to longer cold-path runs. It is usable for this evaluation, but future console performance work should treat state build latency as a separate UI operations concern.
- `evidence_gaps=49` remains high. This is not a regression from the refinement, but it is the best next design topic.

## Insight

- The Taskset Board attention workspace is now reliable enough to close the focused active-claim and empty-state refinement.
- The next UI cycle should not patch another small symptom first. The evidence points to a broader design seminar on evidence-gap overload, inactive-view/layout cost, and state-build latency.
- The beta tester role now has a useful loop: source fix -> live claim fixture -> desktop/mobile/reduced-motion evidence -> route or close BTC IDs.

## Decision

Accept `TASK-AR-615` beta evidence and close `TASKSET-AR-TSAW-CLAIM-EMPTY-REFINEMENT` after independent verification. Start the next UI/UX cycle with a lead-designer seminar focused on the next broad design direction rather than another active-claim patch.

## Action Board

| Action | Owner | State |
| --- | --- | --- |
| Preserve beta evidence for W4b verification | ux-evaluator | done |
| Close `BTC-TSAW-CLAIM-001` | beta-tester | done |
| Close `BTC-TSAW-EMPTY-001` | beta-tester | done |
| Register or run next lead-designer seminar for evidence-gap overload and performance-aware IA | lead-designer / planning | recommended |

