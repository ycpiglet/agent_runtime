---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-07-31-task-ar-654-rsi-skill-contract-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-07-31T04:30:20+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: tests/test_rsi_operating_system_docs.py
tags: [task-ar-654, scope-amendment, consumer-skill, regression]
---

# TASK-AR-654 RSI skill contract scope amendment

## Evidence

The first full regression run completed with `3116 passed`, `3 skipped`, and
one failure in `test_task_ar_304_skill_layer_is_packaged`. That legacy test
requires the root-only failure casebook path, a reproduction-command phrase,
and an explicit non-repro phrase to appear somewhere in the Runtime skill
layer.

TASK-AR-654 intentionally removed those repository-only dependencies from
`failure-to-regression` because the skill now ships in the consumer core
profile. Reintroducing absent host paths merely to satisfy a string assertion
would make the packaged skill misleading and would contradict the accepted T3
replan.

## Decision

Add `tests/test_rsi_operating_system_docs.py` to the active unit and claim
footprint. Replace only the stale TASK-AR-304 packaging assertion with the
current contract:

- the consumer skill is byte-identical to the source skill;
- root-only casebook and evidence-inbox paths are absent from that consumer
  skill;
- the skill names the canonical Compound commands, supported prevention
  destinations, accepted-watch contract, and task-proposal boundary.

No product behavior, legacy Compound history, release surface, or consumer
repository is changed by this amendment.
