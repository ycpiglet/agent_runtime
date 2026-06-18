---
id: TASK-AR-596
display_id: TASK-AR-596
task_uid: 39cb21b7-2cd6-4484-aab2-a2dfba2aaafb
registered_at: 2026-06-17T22:30:00+09:00
created_at: 2026-06-17T22:30:00+09:00
started_at: 2026-06-19T07:58:04+09:00
updated_at: 2026-06-19T08:09:00+09:00
status: completed
priority: P1
difficulty: M
est_hours: 5
est_tokens: 5000
owner: qa
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
tags:
  - wiki
  - knowledge
  - ia
verification:
  - python -m pytest tests\test_wiki_page_api.py tests\test_wiki_search_ask_api.py tests\test_knowledge_graph.py tests\test_knowledge_digest.py tests\test_knowledge_ask.py tests\test_knowledge_lint.py tests\test_knowledge_lint_gate.py tests\test_ui_console.py -q
  - python scripts\knowledge_lint.py --root . --git-limit 0 check --json
  - python scripts\knowledge_graph.py check --json --git-limit 0
  - python scripts\taskset_work_gate.py --task-set-id TASKSET-AR-LLM-WIKI --check
  - python scripts\owner_governance_gate.py
verification_status: passed
verified_at: 2026-06-19T08:06:00+09:00
verified_by: qa-20260619-075804-kst-closeout
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-596-20260619080600.json
w4b_evidence: reviews/W4B-2026-06-19-TASK-AR-596.md
resolution: done
completed_at: 2026-06-19T08:09:00+09:00
closed_by: codex-wiki-closeout-596
actual_hours: 1.5
actual_tokens: 6000
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

## Units

- `UNIT-TASK-AR-596-001` - Extend wiki corpus lint checks before UI-facing
  mini-graph/nav closeout.

## Refs

- Spec: `docs/superpowers/specs/2026-06-17-llm-wiki-design.md`
- Plan: `docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T08:09:00+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `6000`
- Closed by: `codex-wiki-closeout-596`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-596-20260619080600.json`
<!-- work-close:end -->
