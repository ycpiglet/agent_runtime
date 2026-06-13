---
id: TASK-AR-554
display_id: TASK-AR-554
task_uid: 62ff8a17-5e89-4ac6-b269-1d7db2afb20b
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P2
difficulty: L
est_hours: 12
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - reliability
  - claims
  - distributed
---

# TASK-AR-554 - Multi-host distributed claim safety

## Goal

- Claim reaping/recovery assumes a single checkout (single-writer). Multiple hosts or CI workers touching the same repo could race on claim JSON read/write. Add explicit atomicity/locking and document the single-host assumption otherwise.

## Scope

### Input
- `scripts/claim_lease.py` (lease primitive), `scripts/claim_reaper.py`, `scripts/task_claim_dispatcher.py`.
- Verification case VC-REAP-19 (concurrent reaper race).

### Process
- Enforce atomic file-lock on claim JSON read-modify-write; or document and gate a single-host assumption with a sanity check for multi-host use.
- Optional pluggable backend (flock/Redis/DDB) behind a config flag.

### Output
- Locking/atomicity in the claim R/W path + a multi-host safety note/gate.

## Acceptance Criteria

- Concurrent writers cannot corrupt or lose a claim file.
- A documented sanity check detects unsafe multi-host configuration.
- Single-host behavior unchanged.

## Evidence Targets

- Diff + concurrency tests; VC-REAP-19.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` (multi-host gap).
