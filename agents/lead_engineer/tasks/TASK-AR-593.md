---
id: TASK-AR-593
display_id: TASK-AR-593
task_uid: 5ee2d0c0-f1fb-4f20-b7d9-c034b658712d
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-18T23:30:54+09:00
updated_at: 2026-06-19T08:02:00+09:00
status: completed
verification_status: passed
verified_at: 2026-06-19T00:10:00+09:00
verified_by: codex-w4b-20260619-task-ar-593
evidence_refs:
  - reviews/VERIFY-2026-06-18-task-ar-593-20260618234500.json
w4b_evidence: reviews/W4B-2026-06-19-TASK-AR-593.md
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
resolution: done
completed_at: 2026-06-19T08:02:00+09:00
closed_by: codex-wiki-closeout-596
actual_hours: 2.0
actual_tokens: 7000
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
- Status: W4a and W4b passed; closeout is handled by `TASK-AR-596`.

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T08:02:00+09:00`
- Resolution: `done`
- Actual hours: `2.0`
- Actual tokens: `7000`
- Closed by: `codex-wiki-closeout-596`
- Evidence:
  - `reviews/VERIFY-2026-06-18-task-ar-593-20260618234500.json`
<!-- work-close:end -->
