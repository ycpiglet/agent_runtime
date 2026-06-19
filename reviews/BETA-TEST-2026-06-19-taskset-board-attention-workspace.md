---
type: beta-tester-review
id: BETA-TEST-2026-06-19-taskset-board-attention-workspace
audience: owner
status: accepted-with-findings
signal: watch
score: 82
priority: High
date: 2026-06-19
generated_at: 2026-06-19T21:40:53+09:00
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
task_id: TASK-AR-613
unit_id: UNIT-TASK-AR-613-001
claim_id: CLAIM-20260619-205629-task-ar-613-task-ar-613-taskset-board-attention-beta
source_task_id: TASK-AR-612
participants:
  - beta-tester
  - ux-evaluator
tags: [ui, ux, beta-tester, evidence, taskset-board, attention-workspace]
---

# Taskset Board Attention Workspace Beta Test

## Bottom Line

- Result: accepted with routed findings. The attention workspace supports first-viewport discovery, known-target retrieval, relation detail inspection, fallback search, desktop/mobile fit, and reduced-motion state preservation.
- Strongest pass: the new quick switcher found `TASK-AR-613` and selected `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE` without scanning all `51` tasksets.
- Findings: active runtime claims do not yet appear in the attention workspace, and empty lane copy is misleading for zero-count lanes.
- Boundary: no UI source files were changed by this evaluation unit.

## Environment Notes

- OS: Windows local checkout.
- Browser automation: Python Playwright, Chromium headless.
- Evaluation mode: static served console assets with polling disabled, using the same `HTML`/`CSS`/`JS` render and event path. This avoided repeated slow `/api/state` rebuilds while preserving DOM, CSS, click, input, and keyboard behavior.
- Live API cross-check: root console `http://127.0.0.1:8765/api/tasksets_board`.
- Evaluation server: `http://127.0.0.1:8773`, launched from `.worktrees/TASK-AR-613-taskset-board-attention-beta`.
- Source HEAD: `4aa4271` plus the `TASK-AR-613` evidence-only worktree.
- Data state: `/api/tasksets_board` reported `51` tasksets, `272` tasks, `271` completed tasks.
- Attention lanes: `active_claims=0`, `guarded_recovery=5`, `evidence_gaps=51`, `recently_changed=0`, `ready_next=1`.
- Desktop viewport: `1440x900`.
- Mobile viewport: `390x844`.
- Reduced motion: Playwright `reduced_motion=reduce`; `matchMedia('(prefers-reduced-motion: reduce)')` returned `true`.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Unknown-target discovery | pass | Clicked `ready_next`, selected the first lane card, and reached `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE` with reason `1 open child tasks; claim path open`. |
| Known-target retrieval | pass | Typed `TASK-AR-613` into the quick switcher; result list returned the target taskset; `Enter` selected it. |
| Guarded recovery | pass | Clicked `guarded_recovery`; first card selected `TASKSET-AR-UI-UX-V2` and showed `Claim path 1 guarded` plus `Command readiness claim guard review`. |
| Stale evidence | pass | Clicked `evidence_gaps`; first card selected `TASKSET-AR-CONTEXT-KNOWLEDGE` and exposed stale evidence copy. |
| Empty lane recovery | pass with finding | Clicked `active_claims` and `recently_changed`; empty cards rendered, but the empty-state copy is contradictory. |
| All-tasksets fallback | pass | Typed `attention workspace` in the fallback filter; fallback list narrowed to one target card. |
| Desktop width | pass | `innerWidth=1440`, `documentElement.scrollWidth=1440`, `body.scrollWidth=1440`. |
| Mobile width | pass | `innerWidth=390`, `documentElement.scrollWidth=390`, `body.scrollWidth=390`, no wide children. |
| Reduced motion | pass | `prefersReducedMotion=true`, `docScrollWidth=390`, selected relation labels stayed visible. |
| Active claim freshness | fail | `python scripts/work.py status` reported one active `TASK-AR-613` claim, but the root Taskset Board API still returned `active_claims=0`. |

## User-Like Actions

| ID | Viewport | Action path | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- | --- |
| TSAW-BETA-001 | Desktop `1440x900` | Open Taskset Board asset path, click lane filter `ready_next`, click first attention card. | A user can discover the next useful taskset from the first viewport. | Selected `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE`; detail showed progress `1/2`, `Taskset active`, `Claim path released`, `Evidence freshness stale`, `Command readiness proposal ready`. | pass |
| TSAW-BETA-002 | Desktop `1440x900` | Click lane filter `guarded_recovery`, click first card. | Guarded tasksets remain discoverable with a reason. | Selected `TASKSET-AR-UI-UX-V2`; first card reason was `claim guard review`; relation detail showed guarded claim/command labels. | pass |
| TSAW-BETA-003 | Desktop `1440x900` | Click lane filter `evidence_gaps`, click first card. | Stale/missing evidence is visible and explains why it is prioritized. | Selected `TASKSET-AR-CONTEXT-KNOWLEDGE`; first card reason was `No recent activity evidence; progress 7/7`. | pass |
| TSAW-BETA-004 | Desktop `1440x900` | Click lane filters `active_claims` and `recently_changed`. | Empty lanes should be recoverable and clearly say that no matching tasksets exist. | Empty cards rendered, but copy read `Claim path currently owns work.` and `Recent runtime activity is available for inspection.` despite count `0`. | fail: `BTC-TSAW-EMPTY-001` |
| TSAW-BETA-005 | Desktop `1440x900` | Type `TASK-AR-613` in the quick switcher, press `Enter`. | Known target retrieval should not require scanning all tasksets. | Switcher returned `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE`; selected detail showed `Taskset active`, progress `1/2`, and target relation labels. | pass |
| TSAW-BETA-006 | Desktop `1440x900` | Focus switcher, type full target taskset id, press `ArrowDown`, press `Enter`, focus relation panel, press `Tab` twice. | Keyboard flow should move from switcher to result, then relation panel and lane controls. | Focus moved `#tsboard-switcher` -> `.tsboard-switcher-result.is-selected`; relation panel was focusable; `Tab` moved to lane filter buttons. | pass |
| TSAW-BETA-007 | Desktop `1440x900` | Type `attention workspace` in the full-board fallback filter. | Quiet tasksets remain discoverable outside attention lanes. | Fallback card count became `1`; first card was the target taskset. | pass |
| TSAW-BETA-008 | Mobile `390x844` | Repeat lane clicks for `ready_next`, `guarded_recovery`, `evidence_gaps`, `active_claims`, and `recently_changed`. | Lanes stack without document-level overflow. | `docScrollWidth=390`, `bodyScrollWidth=390`, `topColumns=332px`, `switcherWidth=332`, `detailWidth=332`, no wide children. | pass |
| TSAW-BETA-009 | Mobile `390x844` | Type `TASK-AR-613` in the switcher, press `Enter`. | Mobile known-target retrieval should select the target without horizontal scrolling. | Selected `TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE`; relation labels stayed visible. | pass |
| TSAW-BETA-010 | Mobile `390x844`, reduced motion | Enable reduced motion, click `ready_next`, click first card, type `TASK-AR-613`, press `Enter`. | No meaning should depend on motion. | `prefersReducedMotion=true`; document/body width stayed `390`; selected detail retained `Taskset active`, `Claim path released`, `Evidence freshness stale`, `Command readiness proposal ready`. | pass |
| TSAW-BETA-011 | Root live API | Compare `python scripts/work.py status` with root `/api/tasksets_board`. | Active claim lane should surface the current `TASK-AR-613` claim. | `work.py status` showed `active_claims=1`; root API returned `active_claims=0` and `selected_taskset_id=null`. | fail: `BTC-TSAW-CLAIM-001` |

## Recovery Attempts

| State | Attempt | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- |
| Empty lane | Clicked zero-count `active_claims` lane. | Empty state says no active claims are currently surfaced. | Empty state rendered, but used non-empty reason copy. | fail: `BTC-TSAW-EMPTY-001` |
| Stale evidence | Clicked `evidence_gaps` and selected first stale card. | Stale state is visible, textual, and selectable. | Card and detail exposed stale evidence copy. | pass |
| Blocked/guarded command | Clicked `guarded_recovery` and selected first guarded card. | Guarded command state is readable without relying on color. | Detail showed `Claim path 1 guarded` and `Command readiness claim guard review`. | pass |
| Interrupted claim | Searched current board data for interrupted lane behavior. | Interrupted states should route through guarded recovery when present. | No interrupted item was present in this data state; guarded recovery remained available. | not reproduced |
| Expired claim | Inspected board and root claim state for expired claim representation. | Expired state should be textual if present. | No expired item was present in this data state. | not reproduced |
| No active claim | Clicked `active_claims` while count was `0`. | User can recover from no active claim state. | Empty lane is reachable, but copy is misleading. | fail: `BTC-TSAW-EMPTY-001` |
| Focus recovery | Used switcher `ArrowDown`/`Enter`, focused relation panel, pressed `Tab`. | Focus moves through switcher, result, relation detail, and lane controls. | Focus order was recoverable. | pass |
| Mobile overflow | Repeated primary paths at `390x844`. | No document-level horizontal scroll. | `docScrollWidth=390`, `bodyScrollWidth=390`, no wide children. | pass |

## Failure IDs

| BTC ID | Current status | Reproduction path | Owner | Assetization class | Evidence |
| --- | --- | --- | --- | --- | --- |
| BTC-TSAW-CLAIM-001 | open | Create/hold `TASK-AR-613` claim -> run `python scripts/work.py status` -> root API `/api/tasksets_board`. | interface-designer + design-system-steward | schema / pattern_component | Runtime status shows active claim, but attention workspace `active_claims` lane remains `0`; selected taskset remains `null` on root API. |
| BTC-TSAW-EMPTY-001 | open | Taskset Board -> click `active_claims` or `recently_changed` zero-count lane. | interface-designer | pattern_component | Empty cards render with lane reason copy that implies work exists: `Claim path currently owns work.` / `Recent runtime activity is available for inspection.` |

## Insight

- The accepted `taskset_attention_workspace` direction works as a navigation layer: the switcher and attention lanes reduce whole-board scanning.
- The implementation is good enough for evaluation handoff, but the next source mutation should focus on data freshness and recovery copy, not a new visual direction.
- The data derivation currently treats classification snapshots as stronger than live claim state. That weakens the `active_claims` lane, which is the most operator-critical lane.

## Decision

Accept `TASK-AR-612` as beta-usable with findings. The next UI/UX cycle should register an implementation refinement for `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001` before starting a new design-direction seminar.

## Action Board

| Action | Owner | State |
| --- | --- | --- |
| Preserve this beta evidence for W4b verification | ux-evaluator | done |
| Register follow-up implementation refinement for active claim freshness | lead-engineer / interface-designer | recommended |
| Fix empty lane copy through the attention lane pattern component | interface-designer | recommended |
| Keep mobile and reduced-motion checks in the next beta pass | beta-tester | recommended |

## Risks / Blockers

- Risk: the browser test used static served assets with polling disabled to avoid slow full-state rebuilds. This proves render/event behavior, but the live root API mismatch is recorded separately as `BTC-TSAW-CLAIM-001`.
- Risk: interrupted and expired claims were not present in the current data state, so they remain not reproduced rather than pass.
- Risk: `evidence_gaps` reports `51` items but renders the first `8` lane cards for density; fallback search preserved discoverability.

## Next Steps

- Run the recorded W4a gates for `TASK-AR-613`.
- Run independent W4b verification against this evidence.
- After release, register the next implementation task for active claim freshness and empty lane copy.
