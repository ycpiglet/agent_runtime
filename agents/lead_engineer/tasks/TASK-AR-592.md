---
id: TASK-AR-592
display_id: TASK-AR-592
task_uid: 32dd58d6-22ad-4dd8-b7e4-eee7108a887f
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-18T00:00:00+09:00
completed_at: 2026-06-18T23:00:00+09:00
updated_at: 2026-06-18T23:00:00+09:00
status: completed
priority: P1
difficulty: L
est_hours: 8
est_tokens: 8000
owner: uiux
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
tags:
  - wiki
  - knowledge
  - ia
---

# TASK-AR-592 - Wiki page view

## Goal

Build the console Wiki view with entity page routing, summary, relations,
backlinks, metadata, and a local mini-graph.

## Current Evidence

- Commit: `c72319a Add deterministic wiki page view`
- Review: `reviews/REVIEW-2026-06-18-wiki-page-view.md`
- Tests: `tests/test_ui_console.py` wiki page asset/routing checks

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
