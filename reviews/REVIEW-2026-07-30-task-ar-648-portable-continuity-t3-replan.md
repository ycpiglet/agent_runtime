---
title: TASK-AR-648 Portable Continuity T3 Replan
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-008
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
signal: pass
score: 97
priority: P0
status: approved
tags: [task-ar-648, t3-replan, portable-continuity, pointer, fail-closed]
---

# TASK-AR-648 Portable Continuity T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-648-008` as the only runnable TASK-AR-648 unit,
after re-recording this review and the exact current dispatch surfaces as the
taskset's T3 assumption snapshot.

The selector repair is complete at product
`a3a5eebe0584a7d5359a15c43f205b9770b7cbce`. It passed W4a, independent W4b
at 99/100 with no P0/P1, and canonical verification with `113` selector tests,
`83` claim/readiness tests, and `2658 passed, 3 skipped` across the complete
Runtime suite. `UNIT-TASK-AR-648-007` is completed and its claim is released.

No consumer replay is authorized by this review. Bean Wiki primary, frozen
attempts 1 and 2, and Allimbot remain read-only until portable continuity has
its own exact-product W4a and independent W4b approval.

## Signal

Pass for a bounded Runtime-only remediation.

The previous plan snapshot now correctly fails with exactly three changed
anchors:

- `scripts/taskset_dispatcher.py`
- `src/agent_runtime/templates/project/scripts/taskset_dispatcher.py`
- `tests/test_taskset_dispatcher.py`

Those changes are the independently approved blocked-unit redispatch guard,
not unexplained drift. The task's canonical `unit_spec` now points to
`UNIT-TASK-AR-648-008`; every historical failed, blocked, released, or
completed sibling is non-runnable.

## Action

Re-anchor the taskset to this review and the current work, claim, selection,
continuity, diagnostic, template, and test surfaces. Then run the canonical
read-only taskset plan and require it to select only
`UNIT-TASK-AR-648-008` before creating a claim.

Implement the smallest strict fallback:

1. If either STATUS candidate exists, preserve the current STATUS handoff
   validation. A malformed or stale present STATUS cannot be bypassed.
2. If both STATUS candidates are absent, accept only the canonical
   `agents/project/NEXT-SESSION-POINTER.yml`.
3. The pointer must be fresh and must exactly match every active non-overlay
   claim, its current-agent projection, and its handoff/log sidecars.
4. Claim creation remains claim-only. A separate deterministic projection
   command emits the serial state needed by the pointer; it does not write it.
5. Doctor and the installed document check report the effective continuity
   path and reject an unusable bootstrap before work begins.
6. A clean installed `core` host must complete claim, projection, parallel
   gate, state-sync, RBAC, and owner-governance checks without a STATUS seed.

## Contract Matrix

| Condition | Required result |
| --- | --- |
| Valid present STATUS | Existing STATUS path passes |
| Invalid present STATUS plus valid pointer | Block; no fallback bypass |
| No STATUS, exact fresh pointer and sidecars | Pointer continuity passes |
| Missing or placeholder pointer | Stable fail-closed reason |
| Malformed, stale, duplicate, extra, or partial pointer state | Stable fail-closed reason |
| Pointer/claim identity, path, unit, branch, phase, or heartbeat mismatch | Stable fail-closed reason |
| Missing handoff or log for any active claim | Block |
| Default working-tree claim | Claim record only; repository HEAD unchanged |
| Installed core bootstrap | Doctor identifies pointer path before first claim |

The fallback applies to active non-overlay claims because overlay claims do
not own the primary task projection. Existing sidecar requirements remain
enforced for every active claim.

## Verification Boundary

RED must reproduce the frozen Bean attempt-2
`portable-active-claim-status-seed-missing` failure in an offline installed
core fixture before product code changes.

W4a must include:

- pointer negative cases and present-STATUS precedence;
- claim projection field completeness and non-mutation;
- doctor and installed document diagnostics;
- source/template byte parity;
- selected-template, lock, dependency-closure, sanitizer, and ownership gates;
- the complete clean installed-host journey;
- model-routing regressions; and
- the complete Runtime suite.

A fresh independent W4b must pin one exact product SHA and return no P0/P1.

## Risk

The highest risk is replacing one implicit monolithic status dependency with a
second permissive state source. Exact set equality, freshness, bounded parsing,
and stable fail-closed reason codes are therefore release-blocking.

Do not seed a generic STATUS placeholder, auto-write the pointer during claim
creation, loosen present-STATUS behavior, accept partial agent records, or add
PyYAML as an undeclared installed-host dependency.

The closeout of UNIT-007 also exposed a separate lifecycle semantics gap:
`work verify` appends both failed and later-passed attempts to `evidence_refs`,
while `work close` rejects any historical failed ref. The failed attempt was
retained in the evidence index and claim log, while only the current passed
evidence was used for closeout. This is a P1 follow-up for separating attempt
history from effective close evidence; it does not expand UNIT-008.

## Next

1. Record this T3 snapshot and confirm the taskset assumption gate passes.
2. Confirm the read-only plan selects only UNIT-008 with its own routing,
   dependencies, and stop condition.
3. Create the UNIT-008 claim without SCM persistence or consumer mutation.
4. Implement RED-first, obtain exact-product W4a and independent W4b, and stop
   on any P0/P1.
5. Only after approval create a fresh Bean Wiki attempt 3 from the pinned
   `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` baseline.

No version bump, tag, package, release, push, publish, deployment, credential
access, provider-live test, or network delivery is authorized.
