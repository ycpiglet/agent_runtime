---
id: TASK-AR-535
display_id: TASK-AR-535
task_uid: 57b5d41e-a8c9-46b0-9092-83a7a7fecce7
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 4500
owner: lead_engineer
task_set_id: TASKSET-AR-WORK-STORE-RESTRUCTURE
tags:
  - work-store
  - numbering
  - classifier
  - policy
---

# TASK-AR-535 - Classifier ordinal as canonical human ID + numbering policy

## Goal

- Dissolve the "quantum jump" (200s -> 300s -> no 400s -> 500s): gaps are inherent to any central sequence, and hand-allocating in blocks *manufactures* them. Declare the dynamic classifier ordinal (`N.N.N.N` from `work_item_classifier.py`) the official Owner-facing number and treat `TASK-AR-NNN` gaps as cosmetic — exactly as Jira keys and Stripe invoice numbers separate an opaque stable key from a derived display number.

## Scope

- Update `scripts/work_item_classifier.py` + governance docs (`AGENTS.md`, `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`, `agents/project/work-items/WORK-ITEM-CLASSIFICATION.md`) so the hierarchical ordinal leads in Owner-facing views.
- Stop hand-allocating display blocks: new `TASK-AR-NNN` are allocated **contiguously** from max+1 (this taskset already does so: 533..); document that gaps are non-canonical and never backfilled.
- Surface the ordinal on `BACKLOG-BOARD.md` (coordinate with TASK-AR-533 lanes).

## Acceptance Criteria

- Governance docs state: stable key (UUID) is canonical identity; `TASK-AR-NNN` is a display key whose gaps are cosmetic; ordinal `N.N.N.N` is the human-facing number.
- Board/views render the ordinal; numbering policy documents contiguous allocation.

## Dependency / Footprint

- depends_on: none (policy + classifier; foundational).
- target_files: `scripts/work_item_classifier.py`, `AGENTS.md`, `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`, `agents/project/work-items/WORK-ITEM-CLASSIFICATION.md`. Disjoint from 533/534/536.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` (Postgres/MySQL "sequences are not gapless"; Linear UUID+identifier; Jira mutable key; Stripe opaque id + separate invoice number).
