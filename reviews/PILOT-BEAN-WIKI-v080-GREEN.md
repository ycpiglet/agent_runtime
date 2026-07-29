---
title: Bean Wiki v0.8 Green Pilot Attempt 3
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-009
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: in_progress
signal: watch
score: 0
priority: P0
tags: [pilot, bean-wiki, green-replay, attempt-3, adoption, evidence]
---

# Bean Wiki v0.8 Green Pilot Attempt 3

## Bottom Line

Attempt 3 is not yet classified green. The Runtime prerequisite is approved,
registered, selected, and claimed; the immutable pre-creation snapshot below
was captured while the attempt-3 path and branch were both absent.

## Signal

Pending. No consumer result is claimed before the complete adoption,
continuity, editorial, Compound, restart, Scribe, routing, preservation, and
zero-external-effect evidence passes independent review.

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

The attempt-3 path
`/home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-3`
and branch `codex/task-ar-648-agent-runtime-green-pilot-3` were both absent.

## Action

Create exactly that new Bean worktree from
`357eee4fd8c29c33a949adbe3a0ffa80c874bf42`, capture its clean host/content
digests, and apply only the exact approved `core+web-content` projection.

## Decision

Use a fresh worktree and keep the primary, original red pilot, two frozen
attempts, and Allimbot read-only. The Bean editorial specialist may write only
one review artifact under the host pilot evidence area.

## Risk

The pilot remains release-blocking until exact template provenance, strict
pointer/claim/sidecar continuity, host and content preservation, truthful
routing fields, local editorial validation, and integer-zero external effects
all pass. Any P0/P1 freezes this attempt.

## Next

Create the worktree, run the adoption plan and safe apply, then register the
three bounded local tasks before creating any Bean claim.
