---
id: TASK-AR-591
display_id: TASK-AR-591
task_uid: 67b812de-9f02-493b-b3de-19668ce616f9
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-18T00:00:00+09:00
completed_at: 2026-06-18T22:05:00+09:00
updated_at: 2026-06-18T22:05:00+09:00
status: completed
priority: P1
difficulty: M
est_hours: 5
est_tokens: 5000
owner: worker-engineer
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
tags:
  - wiki
  - knowledge
  - ia
---

# TASK-AR-591 - Wiki read API /api/wiki/page/:id

## Goal

Add a deterministic wiki page envelope with summary, metadata, typed
relationships, backlinks, and bounded minigraph data.

## Current Evidence

- Commit: `9a95f22 Add deterministic wiki page API`
- Review: `reviews/REVIEW-2026-06-18-wiki-page-api-envelope.md`
- Tests: `tests/test_wiki_page_api.py`

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
