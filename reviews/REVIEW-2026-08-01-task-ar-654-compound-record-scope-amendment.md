---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-01T00:27:00+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
tags: [task-ar-654, scope-amendment, compound, repeated-failure, regression]
---

# TASK-AR-654 Compound record scope amendment

## Evidence

The skeptic closeout established a second occurrence of the accepted-watch
authority defect. The active repair claim therefore carries the
`repeated_failure` escalation trigger and the stable signature
`defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694`.
The failure-to-regression contract requires this repair to create and validate
a current-work canonical Compound record before closure.

The unit footprint already owns the source, packaged helper, closure consumers,
and their regressions, but it did not name the new record or generated Compound
index. Leaving those paths undeclared would make the prevention artifact
operationally necessary but outside the claim's collision boundary.

## Decision

Add only these paths to the active unit and claim footprint:

- `agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json`
- `agents/project/knowledge/compounds/INDEX.json`

This amendment records the already-required repeated-failure prevention
artifact. It does not broaden Compound requirements to ordinary work, rewrite
legacy records, alter consumer repositories, or add release scope. Review,
verification, claim, projection, and index files remain lifecycle evidence
rather than product implementation targets.
