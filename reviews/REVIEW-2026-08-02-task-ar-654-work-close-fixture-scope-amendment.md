---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-work-close-fixture-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-02T14:23:38+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/REVIEW-2026-08-02-task-ar-654-claim-store-components-t3-replan.md
tags: [task-ar-654, scope-amendment, fixture, work-close, claim-store]
---

# TASK-AR-654 work-close fixture scope amendment

## Trigger

Exact implementation candidate `2f4ec606ad460efd556780c905240b26571c1986`
(tree `5dc072f194adedc024e98eb2259bbc0a1459931f`) passed the new component
regressions, both complete closure/Compound test files, the `1158`-test
registered suite, and all registered gates. The full Runtime suite then
reported `3995 passed, 3 skipped` and six failures confined to
`tests/test_work_close.py`.

Every failure was the same expected consequence of the new contract:
`_write_unit()` created work items beneath `agents/` but did not create the
direct `agents/runtime` directory that every adopted consumer template ships.
The close command therefore correctly returned
`closeout:active-claim-context-invalid` before reaching the behavior those six
tests intended to exercise.

## Decision

Add `tests/test_work_close.py` to the unit and active claim target set. Modify
only its central `_write_unit()` fixture so it creates direct
`agents/runtime` while leaving final `task_claims` absent. This is fixture
alignment, not a weakening of the production rule: missing `agents` or
`agents/runtime` remains invalid, while absence of final `task_claims` beneath
verified direct parents remains compatible.

The change must make all six original closeout assertions execute again and
must be followed by the complete `tests/test_work_close.py`, registered, and
full Runtime suites. Any production-code change or additional test-file scope
requires a new replan or amendment.

## Safety boundary

No consumer write, credential, provider, live network, package installation,
database migration, notification, version, tag, publication, push,
deployment, or external release action is authorized.
