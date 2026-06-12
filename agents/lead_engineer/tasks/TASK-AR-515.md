---
id: TASK-AR-515
display_id: TASK-AR-515
task_uid: 9c205ef4-f279-4409-8580-2345bbdbd605
registered_at: 2026-06-12T23:31:00+09:00
created_at: 2026-06-12T23:31:00+09:00
updated_at: 2026-06-13T02:55:00+09:00
started_at: 2026-06-13T01:33:46+09:00
completed_at: 2026-06-13T02:55:00+09:00
title: Work metadata schema catalog and envelope fields
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - schema_change
  - cross_cutting
tags:
  - metadata
  - work-schema
  - envelope
  - gate
---

# Work metadata schema catalog and envelope fields

## Goal
- Define and gate the Work Item metadata catalog for provenance, resolution, relationships, routing, verification, display/search, and schema evolution.

## Context

- Owner wants metadata useful for search, CRUD, statistics, query, and
  big-data-style insight, not just frontmatter/footer formatting.
- Existing `WORK-SCHEMA.yml` and `work_schema_gate.py` cover the start of this,
  but the full field catalog and required/optional promotion policy are not yet
  a dedicated task record.

## Scope

- Extend the Work Item envelope catalog around:
  provenance, source references, resolution, relationships, verification
  status/freshness, routing/governance, display/search fields, schema version,
  and custom-property registration.
- Define field owner: generator, gate, human, runtime, or derived-only.
- Gate unknown fields as watch, and block required-field gaps by kind.
- Keep derived values such as progress, age, and variance computed-only.

## Out Of Scope

- One-shot backfill of all legacy task records.
- UI explorer rendering.

## Acceptance Criteria

- Schema fixtures cover required, optional, unknown, and derived-only fields.
- `python scripts/work_schema_gate.py --items --check` passes for valid records
  and fails/watches invalid fixtures.
- Owner documentation explains which fields feed which query/stat.

## Evidence Targets

- `WORK-SCHEMA.yml` update.
- Gate tests.
- Owner-facing schema catalog review.

## Completion Evidence

- PR #49 (97026da): WORK-SCHEMA.yml catalog extension (source classes on 86 fields, promotion policy, 3 new optional fields, allowed_values on 13 enums, variance computed-only) + gate validation + mirrors; 13 new tests. minimum_required_by_kind unchanged (anti-bloat).

## Verification Results

- pytest tests/test_work_schema_gate.py -q -> 21 passed
- pytest tests -q -> 502 passed (+1 pre-existing)
- work_schema_gate --items --check pass before/after on real tree
- W4b inst-w4b-ar515-verifier -> APPROVE (follow-up: verification_status pending enum)
