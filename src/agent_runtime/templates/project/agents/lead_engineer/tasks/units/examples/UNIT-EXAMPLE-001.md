---
unit_id: UNIT-EXAMPLE-001
task_id: TASK-EXAMPLE
task_set_id: TASKSET-EXAMPLE
project_id: PROJECT-EXAMPLE
status: worker_ready
horizon: unit
model_tier: worker_low
escalation_triggers: [ambiguity, repeated_failure]
context: "Demonstrate the worker-ready unit shape for host projects."
inputs:
  - agents/project/PROJECT-CONTEXT.yml
target_files:
  - scripts/example.py
scope: "Replace this example with a real task-specific scope."
acceptance:
  - "The worker can execute without chat-only context."
verification:
  - "python scripts/task_unit_readiness_gate.py --task-id TASK-EXAMPLE --check"
handoff: "Report changed files, verification, and remaining blockers."
stop_condition: "Stop after this unit."
---

# UNIT-EXAMPLE-001 - Worker-Ready Unit Example

## Context

This example shows the fields a planner must fill before assigning a unit to a
worker model.

## Inputs

- `agents/project/PROJECT-CONTEXT.yml`

## Target Files

- `scripts/example.py`

## Scope

In scope: one precise, reversible implementation unit.

Out of scope: adjacent tasksets, unrelated refactors, and external mutation.

## Steps

1. Read the linked task and project context.
2. Edit only the target files.
3. Run the listed verification.
4. Stop and report.

## Acceptance Criteria

- The unit can be executed from this file alone.

## Verification

```powershell
python scripts/task_unit_readiness_gate.py --task-id TASK-EXAMPLE --check
```

## Handoff

Report changed files, verification output, and unresolved blockers.

## Stop Boundary

Stop after this unit. Do not continue into adjacent tasksets.
