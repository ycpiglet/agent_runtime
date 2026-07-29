---
title: TASK-AR-648 Consumer Continuity Ownership Repair Registration
date: 2026-07-30
status: active
signal: pass
score: 98
priority: P1
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-010
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, continuity, ownership, consumer-host, bean-wiki]
---

# Consumer Continuity Ownership Repair Registration

## Bottom Line

Register one Runtime-only repair for the independently confirmed P1 from Bean
attempt 3. Do not alter Bean documents and do not replay the consumer until the
exact Runtime product passes W4a and independent W4b.

## Finding

The pointer, state, Scribe, claim, sidecar, and RBAC paths passed. The remaining
failure is documentation ownership: the continuity gate treats a generated
consumer like the Agent Runtime source repository and requires Runtime wording
in files the adoption contract preserves as host-owned or does not manage.

## Fixed Decision

- Source repository: keep README, protocol-rule, and pointer checks strict.
- Generated consumer: enable ownership-aware document selection only when a
  valid v2 config and v2 lock agree.
- Common Runtime rules: validate a lock-proven managed Runtime document.
- Pointer schema: validate in all modes, without exemption.
- Missing, malformed, or mismatched provenance: block.

## Boundary

No Bean worktree mutation, consumer workaround, Allimbot action, provider-live
call, release, version, tag, package, push, publish, deploy, credential access,
or network delivery is authorized.

## Next

T3-anchor UNIT-010, prove it is the only runnable TASK-AR-648 unit, create a
default working-tree claim, then implement RED-to-green product tests.
