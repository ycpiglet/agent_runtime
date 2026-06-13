---
id: TASK-AR-536
display_id: TASK-AR-536
task_uid: 30f4de47-2cdd-4af4-85de-a9e9f788bfe9
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P2
difficulty: M
est_hours: 5
est_tokens: 4500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - identity
  - uuidv7
  - reservation
---

# TASK-AR-536 - UUIDv7/ULID stable key + reservation ledger demotion

## Goal

- Make the permanent key collision-free AND time-sortable so multiple agents mint IDs with zero coordination, removing the reservation ledger from the hot path. (RFC 9562 §5.7 prefers UUIDv7; ULID equivalent.)

## Scope

- Upgrade `scripts/task_identity.py` mint path from UUIDv4 -> UUIDv7 (or ULID) for new `task_uid`; existing v4 keys remain valid (no backfill required).
- Make the `TASK-AR-<timestamp>-<hex8>` form the *normal* mint path for new tasks (panes mint locally, no ledger round-trip).
- Demote the file-locked reservation ledger (`TASK-ID-RESERVATIONS.json`) from required to optional "vanity number" reservation; document it as such. Keep the consistency checks for any reservations that still exist.

## Acceptance Criteria

- New tasks get a UUIDv7/ULID `task_uid`; `task_identity.py check` stays green for both old and new keys.
- Concurrent multi-agent creation needs no central allocator to avoid collisions.
- Reservation ledger is documented optional; gates do not require a reservation for a new task.

## Dependency / Footprint

- depends_on: TASK-AR-535 (numbering policy frames stable-key-vs-display-key).
- target_files: `scripts/task_identity.py`, `tests/test_task_identity*.py`, `agents/project/work-items/TASK-ID-RESERVATIONS.json` (doc/flag only). Disjoint from 533/534.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (UUIDv7/ULID time-sortable, coordination-free; Snowflake/Instagram/Discord worker-id partitioning; reservation = serialization point).
