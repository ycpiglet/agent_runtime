---
type: initiative
id: INIT-AR-WORK-METADATA-ANALYTICS
status: planned
owner: lead_engineer
created_at: 2026-06-12T23:30:00+09:00
updated_at: 2026-06-12T23:35:00+09:00
priority: High
task_sets:
  - TASKSET-AR-WORK-METADATA-ANALYTICS
---

# Work Metadata Analytics Initiative

## Purpose

Make the Owner/Claude/Codex discussion about Work Item metadata, A2A evidence,
agent identity, query/statistics, and verification freshness visible as
canonical work instead of scattered chat or broad platform tasks.

## Decision

- A2A core routing and lifecycle proof remain completed archived evidence.
- The remaining work is not "more A2A transport"; it is traceability and
  analytics over work, evidence, verification, and agent instances.
- The taskset is intentionally separate from generic UI platform work so each
  metadata field has a measurable consumer and each follow-up appears on the
  Owner board.

## Scope

- Conversation-to-work traceability and registration audit (TASK-AR-514).
- Work metadata schema catalog and envelope fields (TASK-AR-515).
- Work Explorer tree roll-up and facet filters (TASK-AR-516).
- Work query, stats, export, and saved views (TASK-AR-517).
- Agent instance attribution across A2A, evidence, closeout, and commits
  (TASK-AR-518).
- Verification freshness and stale evidence gate (TASK-AR-519).

## Out Of Scope

- Reopening completed A2A routing/lifecycle tasks unless a new defect is found.
- Networked external A2A transport.
- Automatic canonical mutation from conversation without review.
