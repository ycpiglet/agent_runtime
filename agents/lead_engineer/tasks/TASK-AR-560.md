---
id: TASK-AR-560
display_id: TASK-AR-560
task_uid: 01090ddb-fc0d-4a8d-b5e0-f66e5c57c501
registered_at: 2026-06-15T00:29:41+09:00
created_at: 2026-06-15T00:29:41+09:00
updated_at: 2026-06-15T00:29:41+09:00
status: planned
priority: P1
difficulty: XL
est_hours: 12
est_tokens: 12000
owner: lead_engineer
task_set_id: TASKSET-AR-AGENT-ORG-DELEGATION
tags:
  - agent-org
  - delegation
---

# TASK-AR-560 - Orchestrator + swappable WorkerBackend (SubagentBackend)

## Goal

- Lead orchestrator: create claim+worktree+instance, spawn Worker/Reviewer sub-agents (Agent tool, worktree isolation), sync claim lease/release lifecycle; enforce seam-serialization + concurrency/budget caps + idempotency + full-trace sharing. WorkerBackend interface (Phase2 daemon-swappable).

## Refs

- Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md
- Research: reviews/RESEARCH-2026-06-14-agent-org-design-references.md
