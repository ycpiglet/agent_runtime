---
id: TASK-AR-596
display_id: TASK-AR-596
task_uid: 39cb21b7-2cd6-4484-aab2-a2dfba2aaafb
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
updated_at: 2026-06-18T23:30:00+09:00
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 5000
owner: qa
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
tags:
  - wiki
  - knowledge
  - ia
---

# TASK-AR-596 - Wiki lint extension + closeout

## Goal

Extend knowledge lint coverage for the expanded corpus and close
`TASKSET-AR-LLM-WIKI` with full E2E, DOM budget, owner governance, and W4b
evidence.

## Acceptance

- Knowledge lint understands the new wiki/corpus kinds and relationships.
- Wiki/search/ask regressions pass together.
- W4b verifier is independent from the implementer.
- Taskset closeout updates owner-facing state without leaving stale pointers.

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
