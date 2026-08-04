---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-canonical-compound-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-02T12:22:38+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802122023.json
tags: [task-ar-654, scope-amendment, compound, canonical-authority, fail-closed]
---

# TASK-AR-654 canonical-authority Compound scope amendment

## Evidence

Candidate `c63c646100e220fb0d24acc291fc2f6f9a00b854` passed the
registered focused suite (`1114 passed`), all registered asset, mirror, and
host-lock checks, and the repository-wide suite (`3957 passed, 3 skipped`).
The fresh machine evidence is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802122023.json`.

The prior append-only Compound records capture earlier physical-line,
malformed-input, bounded-read, and claim-signal failures. They must remain
unchanged and cannot absorb the six later canonical path, authority-shape,
identity, and structural-recursion signatures.

## Decision

Add exactly this new append-only prevention target to the task, unit, and
active claim footprint:

- `agents/project/knowledge/compounds/records/COMPOUND-20260802-122158-bind-closure-authority-to-canonical-paths-shapes-73db9fe7ce52.json`

The record binds both work IDs, all six new stable signatures, the independent
probe and replan sources, the two failure-first regression files, and the fresh
Verify. Keep the generated Compound index within the already authorized
lifecycle footprint. This amendment does not rewrite earlier records, widen
Compound to ordinary work, modify consumer repositories, or authorize any
external release action.
