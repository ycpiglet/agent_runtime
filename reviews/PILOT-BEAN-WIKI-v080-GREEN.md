---
title: Bean Wiki v0.8 Green Pilot Attempt 3
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-009
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: blocked
signal: block
score: 38
priority: P1
tags: [pilot, bean-wiki, green-replay, attempt-3, adoption, evidence]
---

# Bean Wiki v0.8 Green Pilot Attempt 3

## Bottom Line

Attempt 3 is blocked. Safe adoption, lock, doctor repair, no-STATUS standby and
active pointer continuity, state sync, Scribe freshness, and RBAC all passed,
but the installed Owner governance chain exposed a new P1: the source-repo
continuity documentation contract is imposed on Bean Wiki's host-owned files.
The consumer stayed at its exact baseline with zero content or external-effect
mutation and is frozen as failure evidence.

## Signal

`BLOCK / P1`; P0 none. Independent W4b confirmed that editing Bean
`README.md`, `AGENTS.md`, or `CLAUDE.md` would be an invalid workaround.

## Runtime Baseline

| Field | Observed value |
| --- | --- |
| Approved product | `b82042eba58f1e06e1e73130a189cb72245462a0` |
| Product tree | `3b63e0c920a47bf89a5f4bb6e4c84d7f1f20f239` |
| Template tree | `d61713bc4066d4ea549efcc7826da10929e64e94` |
| Registration commit | `363e915f02e7d49b77d633b766af0d2ec081448c` |
| Claim lifecycle commit | `7aa7655ac3bcc86ffa2426bca3e77b05dfceda8c` |
| Product/pilot-validator delta from approved product | `0` |
| Runtime default-claim HEAD before/after create | `363e915f02e7d49b77d633b766af0d2ec081448c` |
| Runtime claim persistence | `working_tree`; no SCM commit authorized at creation |

The later commits contain only registration and claim lifecycle records. The
checked product boundary was `src/agent_runtime`, root claim/parallel
dispatchers, pilot validator/tests, and the host lock fixture.

## Pre-Creation Consumer Snapshot

Captured at `2026-07-30T01:40:00+09:00`.

| Checkout | HEAD | Branch | Status count | Status SHA-256 | Tracked diff SHA-256 | Untracked count | Untracked manifest SHA-256 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| Bean primary | `808309a7b41b80b901e79a1fa6ad546871187ab9` | `main` | 143 | `5d96bc89d446656292101d186b3f3fbcb88927f5c7e6fac89952ff9803fa71f9` | `80f27cfe93c65836da0ed2e75c6a37e1993c2ee256844ef8beca60ebb9a50e8c` | 35 | `16d012f68b73478c8d14f22be0fdb38017d66c67b71ab93034de1ccc71570b1a` |
| Original red pilot | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` | `codex/task-ar-648-agent-runtime-pilot` | 320 | `6592f83d25226a5af59eb478bc144f56b7e2752d20e8bb5928092f21efe6f9f9` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 320 | `9819a170b487b122d9a5e57e90e85ff7a8640dd79dc5683415b8c01d00563044` |
| Frozen attempt 1 | `c93d12baa0020c30e71b50211ecd0c760a65e5e2` | `codex/task-ar-648-agent-runtime-green-pilot` | 301 | `1413e072f0b9d163bf1b558282f6ffae86aa21374629a4d872c7f3d37daf33ce` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 301 | `0d9c3a0ba2e9c0e58650898ee47477098c3a495570f4dd32657a6d3c7890e69a` |
| Frozen attempt 2 | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` | `codex/task-ar-648-agent-runtime-green-pilot-2` | 283 | `d3b478e86d6d88237515eb9dec82b9184988d11e1be44ab09b59db73be353c5e` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 283 | `bba8c9100e16d9461546ce95c0134ac6bc5926866e65e824353689d4a79fa55b` |
| Allimbot | `5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd` | `codex/full-web-parity-account` | 2 | `97585bc46387fde8ee01b51518bfe5ffeb3084f3b6f7b085cf555059f83eded6` | `c90de2ff8397144a33a708f8c551162f6578cea9efcb4af30256cf1246902a69` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

`Status SHA-256` hashes NUL-delimited porcelain-v2 output with all untracked
paths. `Tracked diff SHA-256` hashes the binary worktree delta against HEAD.
The untracked manifest hashes each untracked file's SHA-256 line in Git path
order. The first untracked-manifest invocation used the wrong working
directory and emitted missing-file diagnostics; the values in this table are
from the corrected repository-qualified invocation.

At snapshot time the attempt-3 path
`/home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-3`
and branch `codex/task-ar-648-agent-runtime-green-pilot-3` were both absent.

## Attempt 3 Observed Result

| Field | Observed value |
| --- | --- |
| Bean start/current HEAD | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Selected profile/files | `core+web-content`; 246 |
| Safe apply | 244 applied; 0 conflict |
| Immediate reconcile | 0 safe update; 244 preserved; 2 excluded |
| Lock | `agent-runtime-lock/v2`; 246 files; check passed |
| Doctor | 1 initial empty-runtime blocker; safe repair -> 0 blocker |
| STATUS candidates | both absent |
| Standby/active continuity | both passed |
| State sync / Scribe / RBAC | passed / fresh / passed |
| Host assets | 16/16 byte-identical |
| Content | 125/125 byte-identical; tracked diff empty |
| Consumer commit/push | 0 / 0 |
| External effects | all integer zero |
| Owner governance | blocked by 13 continuity documentation findings |
| Independent verdict | `BLOCK / P1`; P0 none |

Consumer evidence:

- `agents/host/pilot/evidence/adoption-verification-green-3.json`
- `agents/host/pilot/reviews/W4A-TASK-AR-201.md`
- `agents/host/pilot/reviews/W4B-TASK-AR-201.md`

The installed classifier also reported stale immediately after lifecycle writes;
its canonical regeneration and focused check passed. The remaining blocker is
therefore isolated to the ownership-insensitive continuity documentation gate.

## Action

Create a separate Runtime repair unit. Keep README/protocol documentation checks
strict in the Runtime source repository, but make the installed consumer
contract ownership-aware without weakening pointer schema, claim matching,
sidecar, state-sync, RBAC, or parallel-worktree checks.

## Decision

Freeze attempt 3. Do not edit Bean host documents to satisfy Runtime wording.
Do not start its editorial or restart tasks, and do not create an Allimbot
worktree. Replay only from a fourth fresh Bean worktree after the Runtime repair
passes canonical W4a and independent W4b.

## Risk

An over-broad consumer skip would turn the repair into a continuity fail-open.
The pointer contract must remain mandatory even when project documents are
host-owned. A missing or malformed ownership configuration must retain strict
behavior.

## Next

Register, claim, implement, and independently verify the Runtime-only repair.
Then create a fresh pinned product worktree and Bean attempt 4; keep every
earlier attempt and Allimbot read-only.

## Runtime Repair Disposition

The attempt-3 verdict remains immutable failure evidence. Its blocker was
repaired only in Agent Runtime UNIT-010 at exact product
`dd279cd5613578c87ed6c4c24b37325084449d82`, tree
`ea843b6ca5661f04179376df92a11f4416217ab1`.

Canonical verification passed with focused counts `23`, `82`, and `167`, plus
the complete Runtime suite at `2692 passed, 3 skipped`. Independent W4b
approved the same exact product at 99/100 with no P0/P1:
`reviews/W4B-2026-07-30-unit-task-ar-648-010.md`.

This repair does not convert attempt 3 into a passing pilot and does not
authorize a consumer-side document edit. It clears only the prerequisite for
a separately registered, fresh attempt 4 from Bean baseline `357eee4`.
