---
status: draft
origin_type: planning_proposal
origin_ref: agents/planning/outbox/PROP-A6EFB00722C9.json
tags:
  - proposal-draft
  - work-split
---

# work split: TASK-AR-596

## Goal

Review and approve proposed unit specs for `TASK-AR-596` before creating canonical unit files.

## Proposed Units

### TASK-AR-596-PROPOSED-001 - TASK-AR-596 - Knowledge lint understands the new wiki/corpus kinds and rela...

- Scope: Knowledge lint understands the new wiki/corpus kinds and relationships.
- Target files:
- Acceptance:
  - Knowledge lint understands the new wiki/corpus kinds and relationships.
- Verification:
  - `python scripts/work.py split TASK-AR-596 --json`

### TASK-AR-596-PROPOSED-002 - TASK-AR-596 - Wiki/search/ask regressions pass together.

- Scope: Wiki/search/ask regressions pass together.
- Target files:
- Acceptance:
  - Wiki/search/ask regressions pass together.
- Verification:
  - `python scripts/work.py split TASK-AR-596 --json`

### TASK-AR-596-PROPOSED-003 - TASK-AR-596 - W4b verifier is independent from the implementer.

- Scope: W4b verifier is independent from the implementer.
- Target files:
- Acceptance:
  - W4b verifier is independent from the implementer.
- Verification:
  - `python scripts/work.py split TASK-AR-596 --json`

### TASK-AR-596-PROPOSED-004 - TASK-AR-596 - Taskset closeout updates owner-facing state without leaving s...

- Scope: Taskset closeout updates owner-facing state without leaving stale pointers.
- Target files:
- Acceptance:
  - Taskset closeout updates owner-facing state without leaving stale pointers.
- Verification:
  - `python scripts/work.py split TASK-AR-596 --json`

## Readiness Check

- TASK-AR-596-PROPOSED-001:split-readiness:missing:inputs
- TASK-AR-596-PROPOSED-001:split-readiness:missing:target_files
- TASK-AR-596-PROPOSED-002:split-readiness:missing:inputs
- TASK-AR-596-PROPOSED-002:split-readiness:missing:target_files
- TASK-AR-596-PROPOSED-003:split-readiness:missing:inputs
- TASK-AR-596-PROPOSED-003:split-readiness:missing:target_files
- TASK-AR-596-PROPOSED-004:split-readiness:missing:inputs
- TASK-AR-596-PROPOSED-004:split-readiness:missing:target_files

## Source Evidence

- TASK-AR-596 has no registered unit specs; propose 4 worker-ready unit draft(s).
- Internal split readiness status: watch.

## Verifier List

- `python scripts/work.py split TASK-AR-596 --json`
- `python scripts/task_unit_readiness_gate.py --task-id <approved-task-id> --require-ready --check`
- `python scripts/owner_governance_gate.py`

## Risk Boundary

B-mode split proposal only; do not create unit files, reserve IDs, or mutate canonical work items without approved apply.
