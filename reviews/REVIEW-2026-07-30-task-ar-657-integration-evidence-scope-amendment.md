---
id: REVIEW-2026-07-30-task-ar-657-integration-evidence-scope-amendment
title: TASK-AR-657 integration and closeout-evidence scope amendment
kind: replan
status: approved
signal: pass
date: 2026-07-30
task_id: TASK-AR-657
unit_id: UNIT-TASK-AR-657-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
priority: P1
---

# TASK-AR-657 Integration and Closeout-Evidence Scope Amendment

## Decision

Amend TASK-AR-657 before dispatch so the reusable adoption procedure also
closes two deterministic gaps observed during TASK-AR-652 W5/W6:

1. local `merge_queue.py` cannot check out a branch that remains attached to a
   worker worktree, while the documented order says integration precedes
   cleanup; and
2. independently approved reports are not closeout evidence unless their
   frontmatter carries the canonical `task_id` and applicable `unit_id`.

This is a bounded extension of the existing consumer-adoption and
failure-to-regression skill task. It does not change task order: TASK-AR-657
still waits for TASK-AR-654 and TASK-AR-656.

## Added Scope

- Add an attached-worktree preflight or a worktree-aware local integration
  path to `merge_queue.py`.
- Make dry-run and merge-integrator instructions state the same executable
  cleanup/integration order.
- Require independent-verification and runtime-adoption report templates to
  emit closeout-consumable canonical work identifiers.
- Add regression coverage in `tests/test_merge_queue.py` and
  `tests/test_closure_gate.py`.

## Evidence-to-Proposal Route

This amendment follows
`agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`:

- source evidence:
  `reviews/RETRO-2026-07-30-task-ar-652-economic-routing-integrity.md`;
- casebook entries:
  `merge-queue-checked-out-worktree-ordering` and
  `closeout-review-canonical-linkage`;
- canonical Compound records:
  the TASK-AR-652 merge-worktree and closeout-linkage records; and
- destination:
  executable regression plus shipped operating-skill changes in TASK-AR-657.

## Boundaries

- Local SCM and report-schema behavior only.
- No worktree is removed unless it is clean, its claim is independently
  released, and its branch tip is durably preserved.
- No force push, remote mutation, PR, tag, version bump, package publication,
  deployment, provider call, credential access, or consumer-primary mutation.
