---
id: TASK-AR-590
display_id: TASK-AR-590
task_uid: e2ae011e-bd3e-4cc5-917b-2e833c6587c2
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-18T00:00:00+09:00
completed_at: 2026-06-18T21:42:00+09:00
updated_at: 2026-06-18T21:42:00+09:00
status: completed
priority: P1
difficulty: M
est_hours: 6
est_tokens: 6000
owner: worker-engineer
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
tags:
  - wiki
  - knowledge
  - ia
---

# TASK-AR-590 - Wiki corpus expansion

## Goal

Extend the knowledge graph corpus so LLM-Wiki pages can reason over runtime
assets, hooks, gates, skills, and broader product structure instead of only
project-management artifacts.

## Current Evidence

- Commit: `3f94e0f Expand knowledge graph corpus`
- Review: `reviews/REVIEW-2026-06-18-knowledge-graph-corpus-expansion.md`
- Verification: `python scripts/knowledge_graph.py check --json --git-limit 0`

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
