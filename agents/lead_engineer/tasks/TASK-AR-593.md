---
id: TASK-AR-593
display_id: TASK-AR-593
task_uid: 5ee2d0c0-f1fb-4f20-b7d9-c034b658712d
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-18T23:30:54+09:00
updated_at: 2026-06-18T23:45:00+09:00
status: review
priority: P1
difficulty: L
est_hours: 7
est_tokens: 7000
owner: uiux
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
tags:
  - wiki
  - knowledge
  - ia
---

# TASK-AR-593 - Wiki search + ask

## Goal

Add deterministic `/api/wiki/search?q=` and `/api/wiki/ask?q=&llm=0|1`, then
wire a shared search/ask bar into the Wiki view. Default ask is evidence-only;
LLM synthesis is explicit opt-in and degrades when provider configuration is
missing.

## Acceptance

- `/api/wiki/search` returns ranked `{id, kind, title, snippet, score}` results.
- `/api/wiki/ask` returns `{query, evidence, cited, answer, llm_used}`.
- Wiki UI can search, open result pages, and show evidence answers.
- Tests cover deterministic default and mocked/degraded LLM opt-in path.

## Current Evidence

- Claim: `CLAIM-20260618-233054-task-ar-593-6287`
- Review: `reviews/REVIEW-2026-06-18-wiki-search-ask.md`
- W4a self-verification: `reviews/VERIFY-2026-06-18-task-ar-593-20260618234500.json`
- Status: W4a passed; W4b independent verification and claim release remain pending.

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`
