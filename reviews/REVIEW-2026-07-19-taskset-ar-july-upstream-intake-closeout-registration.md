---
title: Upstream Intake Closer Registration
date: 2026-07-19
signal: pass
score: 95
tags: [work-registration, task-ar-372, work-cli]
---

# Upstream Intake Closer Registration

## Bottom Line

Structured work registration created initiative `INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT`, taskset
`TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT`, `7` task records, and `7` unit specs
from one input file.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Input schema | pass | `agent-runtime-work-registration/v1` |
| Reservation ledger | pass | task display IDs fulfilled during registration |
| Generated records | pass | initiative, taskset plan, task files, unit specs included, and generated views refreshed |

## Decision

Use `scripts/work.py new --input <json>` as the deterministic planner-facing
registration path for this taskset shape.

Implementation order and boundaries are fixed as follows:

1. `TASK-AR-594` repairs the P0 dispatcher ordering defect before this taskset
   relies on taskset dispatch behavior.
2. `TASK-AR-595` through `TASK-AR-597` close the remaining host-reported
   updater, conversation-audit, and diagnostic defects without expanding into
   adjacent publish behavior.
3. `TASK-AR-598` integrates PR #277 on current `main`; PR #276's atomic-write
   implementation is treated as an already-landed prerequisite, not repeated.
4. `TASK-AR-599` adopts allimbot only as an optional, three-second-bounded,
   never-blocking channel. Empty configuration is a silent no-op, tests use
   mocks/local servers, and no real notification or secret is allowed during
   verification.
5. `TASK-AR-602` is release-only and cannot start until all six predecessor
   tasks have W4a/W4b evidence and are integrated. The old v0.7.0 candidate SHA
   from issue #280 is superseded; the release candidate must be rebuilt from
   the then-current verified `main`.

The Owner's "전부 진행" instruction is the authorization to implement the
registered fixes and, after all gates are green, publish v0.7.0. It does not
waive claim-first, independent verification, secret boundaries, or release
preflight.

## Action Board

| Task | Title | Status |
| --- | --- | --- |
| `TASK-AR-594` | Honor canonical taskset task order | planned |
| `TASK-AR-595` | Enforce isolated build prerequisites in host updater | planned |
| `TASK-AR-596` | Resolve slugged canonical task files in conversation audit | planned |
| `TASK-AR-597` | Preserve Git stderr in release-auto test failures | planned |
| `TASK-AR-598` | Integrate crash-safe session resume audit | planned |
| `TASK-AR-599` | Adopt never-blocking allimbot notifications | planned |
| `TASK-AR-602` | Synchronize state and release v0.7.0 | planned |

## Risks / Blockers

- `TASK-AR-594` changes the dispatcher used by later work, so its focused tests
  and independent review are a hard boundary before downstream dispatch.
- PR #277 is currently conflict-marked; integrate only its four declared files
  and preserve newer hook-chain changes.
- allimbot is an external-effect integration. Network delivery remains disabled
  in verification and every runtime call must swallow timeout/network failures.
- Release issue #280 references a SHA seven commits behind the registration
  baseline; do not tag or publish that stale candidate.

## Next

- Run `python scripts/work_item_classifier.py --check` and
  `python scripts/taskset_work_gate.py --check` before handoff.
- Keep AI `split`, `criteria`, and `assign` tools behind B-mode proposal review.
- Continue into `work close`, `work verify`, and AI proposal tools after unit generation is covered.
