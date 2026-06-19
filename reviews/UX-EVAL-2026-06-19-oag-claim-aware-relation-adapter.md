---
type: ux-evaluation
id: UX-EVAL-2026-06-19-oag-claim-aware-relation-adapter
audience: owner
status: accepted_with_findings
signal: watch
score: 84
priority: High
date: 2026-06-19
generated_at: 2026-06-19T13:40:00+09:00
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
task_id: TASK-AR-606
unit_id: UNIT-TASK-AR-606-001
claim_id: CLAIM-20260619-132600-task-ar-606-claim-aware-relation-beta
source_task_id: TASK-AR-605
participants:
  - ux-evaluator
  - beta-tester
  - design-system-steward
tags: [ui, ux, evaluation, design-system, claim-aware-relation-adapter]
---

# Claim-Aware Relation Adapter UX Evaluation

## Bottom Line

- Result: UX accepted with one responsive follow-up.
- Strongest pass: active, guarded, interrupted, and no-claim states now use explicit visible labels and command-readiness text.
- Strongest gap: mobile Taskset Board still overflows horizontally at `390px` after the target relation panel is visible.

## Signal

| Dimension | Result | Evidence |
| --- | --- | --- |
| Labels | pass | Relation chips expose `TASKSET`, `CLAIM PATH`, `EVIDENCE FRESHNESS`, `COMMAND READINESS`, task IDs, and actor labels. |
| Non-color-only state | pass | Active state says `claimed by codex-ux-evaluator-ar-606`; guarded state says `claim guard active` / `claim guard review`; interrupted fixture says `interruption recovery`. |
| Focus order | pass | Target panel has `aria-label` and `tabindex=0`; focused panel exits to `.tsboard-add-title` on `Tab`. |
| Reduced motion | pass | Browser reduced-motion media query returned true and state labels remained readable. |
| Desktop workflow | pass | `Skip -> More -> Taskset Board` opens `view-tsboard`; target panel is visible and semantic labels match active claim data. |
| Mobile workflow | watch | Mobile needs `Skip -> hamburger -> More -> Taskset Board`; this path works, but layout overflows horizontally. |
| Responsiveness | fail | At `390x844`, `documentElement.scrollWidth=641` while `window.innerWidth=390`. |
| Schema/data mapping | pass | `/api/tasksets_board` projects `claim_summary.state=claimed` for current TASK-AR-606 and `relation_state=claimed` for its child row; interrupted fixture maps to `interrupted`. |
| Assets | watch | Relation chip and attention panel assets are reusable; the next fix should stay in pattern/layout helpers and tokenized responsive constraints, not page-local CSS. |

## UX Detail

### Interaction

- Desktop navigation is recoverable after the first-run tour: `Skip`, then `More`, then `Taskset Board`.
- Mobile navigation works when using the hamburger first; direct hidden-sidebar clicks are not a valid path.
- Claim readiness no longer invites duplicate claim creation when a claim is active.
- Command readiness now tells the operator that the claim guard is active.

### Accessibility

- State meaning is visible as text, not only color.
- Target relation panel exposes `aria-label="Attention graph for TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER"`.
- Keyboard focus can be placed on the relation panel and exits to the add-title input.
- Focus order is functional, but the next refinement should verify the mobile focus path after the overflow fix.

### Responsive Behavior

- Desktop: `docWidth=1440`, `winWidth=1440`, no horizontal overflow.
- Mobile: `docWidth=641`, `winWidth=390`, horizontal overflow remains after the Taskset Board is visible.
- The overflow is likely caused by a fixed-width board/card/toolbar child rather than the relation-state semantics themselves.

### Motion And Effects

- Reduced-motion preference was active during the test.
- No new animation or transition issue was observed in the claim-aware relation panel.

### Schema And Assets

- `claim_summary` now carries the semantic state the UI needs: `claimed`, `guarded`, and `interrupted`.
- `componentRelationChip` and `patternAttentionRelationPanel` are the right asset layer for this UI; no page-level visual exception is needed.
- `BTC-OAG-CLAIM-MOBILE-001` should be handled as a responsive pattern/layout refinement, with stable dimensions and overflow constraints on Taskset Board containers.

## Defect Routing

| BTC ID | UX impact | Root cause hypothesis | Recommended next step |
| --- | --- | --- | --- |
| BTC-OAG-CLAIM-MOBILE-001 | Mobile operators may need horizontal scrolling to read or act on taskset relation state. | Taskset Board layout has at least one child wider than the 390px viewport, likely a toolbar/card/grid constraint. | Implementation refinement: constrain Taskset Board and relation-panel children at mobile widths, then rerun the same beta path. |

## Next Cycle Recommendation

Run another implementation-refactor cycle before a new visual-direction seminar. The semantic claim adapter is now good enough; the next cycle should target responsive polish:

1. Register a small implementation unit for `BTC-OAG-CLAIM-MOBILE-001`.
2. Keep the fix inside tokenized CSS/pattern layout helpers.
3. Add/adjust focused browser or CSS assertions for mobile overflow.
4. Repeat beta/UX evaluation on desktop and `390x844` mobile.

## Decision

Accepted with findings. `TASK-AR-606` validates the `TASK-AR-605` semantic fix, and routes the remaining issue to a mobile responsive implementation refinement.
