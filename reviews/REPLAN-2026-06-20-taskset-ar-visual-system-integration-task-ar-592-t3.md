---
schema_version: agent-runtime-review/v1
id: REPLAN-2026-06-20-taskset-ar-visual-system-integration-task-ar-592-t3
kind: replan
status: accepted
taskset_id: TASKSET-AR-VISUAL-SYSTEM-INTEGRATION
task_id: TASK-AR-592
created_at: 2026-06-20T22:18:00+09:00
tags: [replan, plan-assumptions, ui, accessibility, responsive]
---

# TASKSET-AR-VISUAL-SYSTEM-INTEGRATION T3 Replan

## Reason

`plan_assumption_gate.py --check --taskset TASKSET-AR-VISUAL-SYSTEM-INTEGRATION`
reported drift before dispatch:

- `anchor-hash-changed:reviews/REVIEW-2026-06-20-taskset-ar-visual-system-integration-registration.md`
- `anchor-hash-changed:scripts/work.py`

The taskset remains valid. The current mainline already contains most
AR-587..591 visual-system code, and TASK-AR-592 should verify and close the
accessibility/responsive boundary rather than redesign the console.

## Updated Dispatch Scope

- Execute `TASK-AR-592`.
- Keep scope to ARIA semantics, contrast, reduced motion, keyboard operation,
  mobile layout, evidence, and work-item closeout.
- Do not add a new design direction in this unit. New design proposals belong
  to the next seminar/meeting/beta-tester cycle after this integration pass.

## Anchors

- This replan record.
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`

