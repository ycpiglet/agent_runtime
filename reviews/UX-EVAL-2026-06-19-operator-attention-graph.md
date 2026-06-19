---
type: ux-evaluation
id: UX-EVAL-2026-06-19-operator-attention-graph
audience: owner
status: accepted_with_findings
signal: watch
score: 76
priority: High
date: 2026-06-19
generated_at: 2026-06-19T10:06:00+09:00
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
task_id: TASK-AR-604
claim_id: CLAIM-20260619-120404-task-ar-604-task-ar-604-beta-resume
original_claim_id: CLAIM-20260619-095200-task-ar-604-operator-attention-graph-beta
source_task_id: TASK-AR-603
participants:
  - ux-evaluator
  - design-system-steward
tags: [ui, ux, evaluation, design-system, operator-attention-graph]
---

# Operator Attention Graph UX Evaluation

## Bottom Line

- Result: UX evaluation accepts the relation panel direction with follow-up required.
- Strongest pass: state is not color-only; labels, focusability, mobile stacking, and reduced-motion behavior are present.
- Strongest gap: relation summary is not claim-aware enough, so active and interrupted claim states can be mislabeled as ready/stale.

## Signal

| Dimension | Result | Evidence |
| --- | --- | --- |
| Labels | pass | Relation chips expose visible labels: `TASKSET`, `CLAIM PATH`, `EVIDENCE FRESHNESS`, `COMMAND READINESS`. |
| Non-color-only state | pass | State appears as text (`active`, `stale`, `task.create ready`, `done`, `plan`) inside chips and evidence rows. |
| Focus order | pass | `.attention-relation-panel` receives focus; `Tab` exits to the add-title input instead of trapping focus. |
| Reduced motion | pass | Under reduced motion, root `data-motion=off`; panel transition duration was near-zero. |
| Desktop workflow | watch | Expand/select flow works, but active claim is not reflected in relation summary. |
| Mobile/responsive | pass | Relation body collapsed to one column and panel did not overflow the reported layout viewport. |
| Recovery clarity | watch | Empty, stale, missing, and blocked fixture states are clear; interrupted state collapses to `stale`. |
| Schema/data mapping | fail | `tasksetRelationSummary` derives claim readiness from child phase only and does not consume active claim data. |
| Assetization | watch | Component/pattern split is healthy; `tasksetRelationSummary` remains `one_off_for_now` but now has enough evidence to justify promotion or replacement. |

## UX Detail

### Interaction

- The relation panel is reachable on `/#work/board`.
- The first-run tour interrupts the first click path but gives a clear `Skip` recovery.
- Expanding Operator Attention Graph reveals `TASK-AR-603` and `TASK-AR-604`.
- Clicking `TASK-AR-604` opens a task detail panel with status, owner, priority, and controls.

### Accessibility

- The relation panel has an accessible label and can receive focus.
- State labels are represented as visible text, so the design is not relying on color only.
- Focus is not trapped in the panel.
- The next focus target after the panel is an input, which is predictable but may deserve a later review because it jumps directly into task creation controls.

### Responsive Behavior

- On mobile, the relation body computed as a single-column layout.
- The tested panel did not overflow the reported layout viewport.
- The page's mobile layout viewport reported wider than the requested viewport, so a later visual pass should include a screenshot-backed mobile check before calling mobile polish complete.

### Motion And Effects

- Reduced-motion preference is honored by the app bootstrap.
- The panel keeps the existing tokenized focus/effect approach; no new motion risk was observed in this evaluation unit.

### Schema And Assets

- `componentRelationChip`, `componentEvidencePreviewRow`, `patternAttentionRelationPanel`, and `patternGraphContextStack` are correctly shaped as reusable UI/pattern assets.
- `tasksetRelationSummary` is still a view-local adapter, but it now controls user-facing claim readiness and command readiness. That responsibility is no longer purely local display glue.
- Resume retest on `http://127.0.0.1:8767/#work/board` confirmed `/api/state` includes `task_claims` with both the resumed TASK-AR-604 claim and the expired predecessor, while the relation panel still reads as ready to claim/create. This narrows the gap to the relation-summary adapter, not the state API.
- Follow-up should either promote a claim-aware relation adapter or feed active claim records into the existing adapter.

## Defect Routing

| BTC ID | UX impact | Root cause hypothesis | Recommended next step |
| --- | --- | --- | --- |
| BTC-OAG-BLOCKED-001 | Operator may believe a claimed evaluation task is ready to claim/create when a claim is already active. | `tasksetRelationSummary` checks child phases and recent activity, but not active claim records. | Implementation refinement: merge active claim data into relation summary and command readiness. |
| BTC-OAG-INTERRUPT-001 | Interrupted or incomplete claim states lose urgency by appearing as stale. | `tasksetChildRelationState` only maps blocked/work/review/done and sends unknown phases to `stale`. | Add an interrupted/recovery state or map interrupted lifecycle to blocked/recovery wording. |

## Next Cycle Recommendation

Run an implementation-refactor cycle before proposing a new visual direction. The design direction is viable; the next problem is data semantics:

1. Promote or replace `tasksetRelationSummary` with a claim-aware pattern adapter.
2. Add explicit relation states for `claimed`, `interrupted`, and `guarded`.
3. Add tests proving active claims change claim-path and command-readiness labels.
4. Repeat beta/UX evaluation after the adapter fix.

## Decision

Accepted with findings. This evaluation satisfies `TASK-AR-604` evidence requirements and should generate the next source-mutating UI refinement task.
