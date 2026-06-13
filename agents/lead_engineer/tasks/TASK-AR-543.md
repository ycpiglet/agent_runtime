---
id: TASK-AR-543
display_id: TASK-AR-543
task_uid: 5f93b27d-34ce-4b82-928a-c5d6f2ba3149
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P1
difficulty: M
est_hours: 7
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UNIFIED-DECISION-CONSOLE
tags:
  - console
  - faceted-views
  - rollups
  - needs-attention
---

# TASK-AR-543 - Faceted saved views + status rollups + needs-attention inbox

## Goal

- Give the decision-maker reusable lenses over the catalog and an exception-only attention surface — saved/faceted views + grouping/swimlanes + rollups (Linear/GitHub Projects/Notion/Jira), with a "needs attention" inbox (Datadog Monitor Quality) — so they see the slice that matters, not the whole store.

## Scope

- Faceted views: filter by kind/owner/status/lifecycle/tags with match counts; AND/OR nested conditions; save + share + favorite views.
- Grouping/swimlanes + status rollups: counts + a few representatives + "see all N" link (never dump N rows); progress/health rollups up the initiative->taskset->task hierarchy (Notion rollup / Linear hierarchy rollup).
- "Needs attention" inbox: blocked items, stale claims, unaccepted triage, at-risk health, missing owner — the exception set only.

## Acceptance Criteria

- Users can save/share faceted views with match counts and grouping.
- Rollups summarize many items as counts+representatives with drill-down, not full dumps.
- A needs-attention inbox surfaces only exception items.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog), soft TASK-AR-533 (board lanes/rollup concept).
- target_files: console views/dashboard module + saved-view store. Disjoint from 540/541/542/544/545 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (Linear Custom Views/swimlanes; GitHub Projects insights group-by; Jira JQL dashboards; Notion relation+rollup; Datadog needs-attention/Case Management).
