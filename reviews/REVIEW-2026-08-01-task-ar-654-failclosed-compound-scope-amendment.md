---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-01-task-ar-654-failclosed-compound-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-01T01:47:30+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801014422.json
tags: [task-ar-654, scope-amendment, compound, fail-closed, repeated-failure]
---

# TASK-AR-654 fail-closed corrective Compound scope amendment

## Evidence

The exact repair candidate `52510a48899470cc8c6d04b076241b36907ac5be`
passed the registered focused suite (`1104 passed`), all three registered
asset/mirror/lock gates, and the repository-wide suite (`3947 passed, 3
skipped`). The fresh machine Verify is
`reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801014422.json`.

The prior append-only Compound records only capture the earlier physical-line
boundary. They cannot be rewritten to add the later malformed UTF-8, bounded
read, and claim-authority findings. The failure-to-regression contract
therefore requires one new current-work record carrying both work IDs and all
four stable defect signatures.

## Decision

Add exactly this new append-only prevention target to the unit and active claim
footprint:

- `agents/project/knowledge/compounds/records/COMPOUND-20260801-014607-fail-closed-across-accepted-watch-and-claim-auth-634ffb3a3711.json`

Keep the generated Compound index already covered by the earlier amendment.
Link the new record from task, unit, and claim authority before W4 review and
before any terminal resolution. This amendment does not rewrite earlier
records, widen Compound to ordinary work, modify consumer repositories, or add
external release scope.
