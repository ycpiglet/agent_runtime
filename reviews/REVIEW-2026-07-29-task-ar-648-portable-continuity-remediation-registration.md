---
title: TASK-AR-648 Portable Continuity Remediation Registration
date: 2026-07-29
status: active
signal: pass
score: 98
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-008
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, portable-continuity, adoption, compound, release-blocker]
---

# TASK-AR-648 Portable Continuity Remediation Registration

## Bottom Line

Register one Runtime-only unit to close the producer-to-consumer continuity
contract exposed by frozen Bean attempt 2. No consumer worktree may be created
or repaired in this unit.

The repair must not seed a second generic status ledger merely to satisfy one
gate. It must make the existing canonical pointer and claim sidecars an exact,
fail-closed continuity path while preserving host-owned STATUS validation when
a host intentionally supplies it.

## Fixed Inputs

| Boundary | Fixed value |
| --- | --- |
| Last approved product | `6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39` |
| Frozen failed replay | Bean attempt 2 at `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Independent verdict | P0, `REQUEST_CHANGES`, 45/100 |
| Defect signature | `defect:portable-active-claim-requires-status-that-core:ed6b5505366251e8` |
| Compound record | `COMPOUND-20260729-233100-portable-continuity-must-close-the-adoption-to-f-d70d307c6cef` |
| Consumer and external effects | forbidden |

## Contract

When either `STATUS.md` or `agents/lead_engineer/STATUS.md` exists, retain the
existing resume-marker check. When both are absent, the fallback passes only
if all of the following are true:

1. `agents/project/NEXT-SESSION-POINTER.yml` has the canonical schema and is
   newer than or equal to every active claim heartbeat.
2. `pointers.active_claims` is an exact set match for active non-overlay claim
   paths, with no missing or stale entry.
3. `active_work.current_agents` has an exact claim-id match and the projected
   task, task-set, role, instance, worktree, branch, phase, status text,
   handoff, and heartbeat fields agree with each claim.
4. Every claim-declared handoff and log path exists.
5. Resume next actions are non-empty.

Malformed YAML-like structure, template placeholders, stale timestamps,
partial identity, duplicates, extra entries, missing sidecars, and claim/pointer
mismatch all block.

## Implementation Boundary

- Extend the deterministic claim projection payload if needed; do not make
  claim creation mutate the serially owned pointer.
- Keep source and packaged template copies byte-identical where parity is the
  existing contract.
- Add doctor output that explicitly names `status` versus `pointer+sidecars`
  as the effective continuity path and blocks an unusable canonical pointer.
- Remove the status-specific false requirement from the installed
  `check_agent_docs.py` path when the strict pointer contract is available;
  do not redesign its broader legacy document model.
- Update only the narrow portable continuity protocol text and template
  pointer guidance required to stop advertising a missing mandatory file.

## Verification Strategy

RED proof must include the exact supported journey:

```text
fresh core adoption
  -> registered unit
  -> default working-tree claim
  -> deterministic serial pointer projection
  -> installed parallel/state/RBAC/governance gates
```

Negative tests must cover missing, placeholder, malformed, stale, duplicate,
extra, and mismatching pointer projections plus absent handoff/log files.
Tests must prove that a present invalid STATUS file still blocks and is not
silently bypassed by a good pointer.

## Routing

Request `worker_standard`, but escalate for `data_integrity`,
`cross_cutting`, and `repeated_failure`. Configured provider tier is not an
observed model. Token, cost, and savings stay unavailable without provider
evidence.

## Stop Boundary

Stop on any fail-open fallback, automatic pointer write from claim creation,
source/template drift, weakened STATUS validation, mutation of a Bean
worktree, Allimbot work, consumer commit, release/version/tag/package action,
push, publish, deploy, credential access, network delivery, or P0/P1 from W4a
or independent W4b.
