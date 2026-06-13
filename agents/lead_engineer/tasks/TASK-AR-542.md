---
id: TASK-AR-542
display_id: TASK-AR-542
task_uid: 2bc66839-72e7-4670-bd5d-8b018af0a67d
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P2
difficulty: M
est_hours: 7
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UNIFIED-DECISION-CONSOLE
tags:
  - console
  - activity
  - provenance
  - timeline
  - audit
---

# TASK-AR-542 - Activity/provenance timeline + audit stream

## Goal

- Answer "who/what/when/why did this change" for any entity by unifying scattered history into a typed, chronological event stream (GitHub timeline-event model), plus a separate filterable audit log for governance.

## Scope

- Typed event stream per entity: `created`, `claimed`, `reviewed`, `decided`/`verdict`, `merged`, `referenced`/`cross-referenced`, `reopened` — ingest from git log, gh PR/issue timelines, claim records, pane events, and council/seminar verdicts.
- Global activity feed with grouping/collapsing of similar consecutive events (Linear de-noising); trace an entity's lineage end-to-end.
- A separate filter-only audit stream (`category.operation`, actor, time) for governance/compliance, retention-bounded.

## Acceptance Criteria

- Any entity shows a chronological typed event timeline traced to sources.
- A global feed groups/collapses noise; an audit stream is filterable by actor/op/time.
- Events are derived from existing records (git/gh/claims/pane-events/verdicts), not re-entered.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog), soft TASK-AR-534 (reviews index), TASK-AR-537 (read-index).
- target_files: console activity module + provenance/event index reader. Disjoint from 540/541/543/544/545 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (GitHub timeline event types + audit log category.operation; Linear collapsed issue history; Datadog Audit Trail; Grafana annotations over time-series).
